import requests
import json
import threading
import time
from datetime import datetime


class SOSHandler:
    def __init__(self, backend_url, user_id):
        """
        Initialize SOS Handler

        Args:
            backend_url: Your backend API URL (e.g., http://192.168.1.39:8000/api/sos/trigger)
            user_id: The user ID/phone number (can be with or without +91)
        """
        self.backend_url = backend_url
        self.user_id = self._format_phone_number(user_id)
        self.last_sos_time = 0
        self.sos_cooldown = 15
        self.last_sent_accident_state = False
        self.backend_checked = False
        self.backend_available = False

        print(f"✅ SOS Handler initialized")
        print(f"   Backend URL: {backend_url}")
        print(f"   User ID (phone): {self.user_id}\n")

        # Check backend connection
        self._check_backend()

    def _check_backend(self):
        """Check if backend is reachable"""
        try:
            print("🔍 Checking backend connection...")
            response = requests.head(self.backend_url, timeout=5)
            self.backend_available = True
            self.backend_checked = True
            print(f"✅ Backend is reachable!\n")
        except:
            self.backend_available = False
            self.backend_checked = True
            print(f"⚠️ WARNING: Backend not reachable at {self.backend_url}")
            print(f"   Make sure your backend server is running!")
            print(f"   SOS alerts will NOT be sent until backend is available.\n")

    def _format_phone_number(self, phone):
        """Format phone number to +91 format"""
        phone = str(phone).strip()
        phone = phone.replace(" ", "").replace("-", "")

        if phone.startswith('+'):
            return phone
        if phone.startswith('91'):
            return '+' + phone
        if len(phone) == 10:
            return '+91' + phone

        return '+91' + phone

    def send_sos_alert(self, accident_data):
        """Send SOS alert to backend ONLY when accident is newly detected"""

        # Check if accident is actually detected
        is_accident_detected = accident_data.get('accident_detected', False)

        if not is_accident_detected:
            # Accident is no longer detected
            self.last_sent_accident_state = False
            return False

        # Accident is detected, but did we already send SOS for it?
        if self.last_sent_accident_state:
            # Already sent, don't show repeated messages
            return False

        # Mark that we're sending SOS for this accident
        self.last_sent_accident_state = True
        self.last_sos_time = time.time()

        # Prepare SOS payload
        sos_payload = {
            "userId": self.user_id,           # ADDED: userId field
            "phone": self.user_id,            # KEPT: phone field
            "accident_detected": True,
            "severity": int(accident_data.get('severity', 0)),
            "status": accident_data.get('status', 'CRITICAL'),
            "reasons": accident_data.get('reasons', []),
            "timestamp": datetime.now().isoformat(),
            "latitude": 0.0,
            "longitude": 0.0,
            "location": "Dashboard Camera Location"
        }

        # Send in background thread (non-blocking)
        thread = threading.Thread(
            target=self._send_request,
            args=(sos_payload,),
            daemon=True
        )
        thread.start()

        return True

    def _send_request(self, payload):
        """Send HTTP request to backend"""

        # Check if backend is available
        if not self.backend_available:
            print(f"\n❌ SOS NOT SENT - Backend is not reachable")
            print(f"   userId: {payload['userId']}")
            print(f"   Please start your backend server at {self.backend_url}\n")
            return False

        try:
            print(f"\n🚨 SENDING SOS ALERT TO BACKEND...")
            print(f"   userId: {payload['userId']}")
            print(f"   phone: {payload['phone']}")
            print(f"   Severity: {payload['severity']}%")
            print(f"   Status: {payload['status']}")
            print(f"   Time: {payload['timestamp']}\n")

            headers = {
                'Content-Type': 'application/json'
            }

            response = requests.post(
                self.backend_url,
                json=payload,
                headers=headers,
                timeout=10
            )

            if response.status_code in [200, 201]:
                print(f"✅ SOS SENT SUCCESSFULLY!")
                print(f"   Status: {response.status_code}\n")
                try:
                    resp_data = response.json()
                    print(f"   Response: {resp_data}\n")
                except:
                    pass
                return True
            else:
                print(f"❌ SOS FAILED!")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}\n")
                return False

        except requests.exceptions.ConnectionError:
            print(f"❌ CONNECTION ERROR")
            print(f"   Backend not reachable at {self.backend_url}")
            print(f"   Please check your backend server\n")
            self.backend_available = False
        except requests.exceptions.Timeout:
            print(f"❌ TIMEOUT - Backend took too long to respond\n")
        except Exception as e:
            print(f"❌ ERROR: {str(e)}\n")

        return False