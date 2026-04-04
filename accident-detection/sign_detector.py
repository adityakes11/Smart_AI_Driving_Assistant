import cv2
import numpy as np
from ultralytics import YOLO


class SignDetector:
    def __init__(self, config=None):
        self.config = config

        print("Loading sign detector...")

        # Load models
        self.sign_model = YOLO('yolov8n.pt')
        self.traffic_light_model = YOLO('yolov8n.pt')

        print("✅ Sign detector loaded!")

        self.speed_limit = None
        self.traffic_light_state = None

    def detect(self, frame):
        """Detect traffic signs"""
        sign_data = {
            'speed_limit': self.speed_limit,
            'traffic_light': self.traffic_light_state,
            'signs': []
        }

        try:
            # Detect speed limits
            try:
                results = self.sign_model(frame, verbose=False, conf=0.5)[0]

                for box in results.boxes:
                    cls = int(box.cls)
                    conf = float(box.conf)
                    class_name = results.names[cls]

                    if 'stop' in class_name.lower():
                        sign_data['speed_limit'] = 0
                        self.speed_limit = 0
            except Exception as e:
                print(f"[SIGN] Error detecting speed limits: {e}")

            # Detect traffic light
            try:
                results = self.traffic_light_model(frame, verbose=False, conf=0.5)[0]

                for box in results.boxes:
                    cls = int(box.cls)
                    conf = float(box.conf)
                    class_name = results.names[cls]

                    if 'traffic' in class_name.lower() or 'light' in class_name.lower():
                        # Get bounding box
                        xyxy = box.xyxy[0].cpu().numpy()
                        x1, y1, x2, y2 = xyxy

                        # Extract ROI
                        roi = frame[int(y1):int(y2), int(x1):int(x2)]

                        if roi.size > 0:
                            state = self._analyze_traffic_light_color(roi)
                            if state:
                                sign_data['traffic_light'] = state
                                self.traffic_light_state = state
            except Exception as e:
                print(f"[SIGN] Error detecting traffic light: {e}")

        except Exception as e:
            print(f"[SIGN] Error in sign detection: {e}")

        return sign_data

    def _analyze_traffic_light_color(self, roi):
        """Analyze traffic light color"""
        try:
            if roi.size == 0:
                return None

            hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

            # Red
            lower_red1 = np.array([0, 100, 100])
            upper_red1 = np.array([10, 255, 255])
            lower_red2 = np.array([170, 100, 100])
            upper_red2 = np.array([180, 255, 255])

            mask_red1 = cv2.inRange(hsv, lower_red1, upper_red1)
            mask_red2 = cv2.inRange(hsv, lower_red2, upper_red2)
            mask_red = cv2.bitwise_or(mask_red1, mask_red2)

            # Green
            lower_green = np.array([35, 100, 100])
            upper_green = np.array([85, 255, 255])
            mask_green = cv2.inRange(hsv, lower_green, upper_green)

            # Yellow
            lower_yellow = np.array([15, 100, 100])
            upper_yellow = np.array([35, 255, 255])
            mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)

            red_count = cv2.countNonZero(mask_red)
            green_count = cv2.countNonZero(mask_green)
            yellow_count = cv2.countNonZero(mask_yellow)

            total = red_count + green_count + yellow_count

            if total == 0:
                return None

            if red_count > green_count and red_count > yellow_count and red_count > total * 0.3:
                return 'RED'
            elif green_count > red_count and green_count > yellow_count and green_count > total * 0.3:
                return 'GREEN'
            elif yellow_count > red_count and yellow_count > green_count and yellow_count > total * 0.3:
                return 'YELLOW'

            return None

        except Exception as e:
            print(f"[SIGN] Error analyzing color: {e}")
            return None