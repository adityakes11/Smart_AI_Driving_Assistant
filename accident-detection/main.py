import cv2
import time
from config import Config
from lane_detector import LaneDetector
from vehicle_detector import VehicleDetector
from sign_detector import SignDetector
from collision_warning import CollisionWarning
from accident_detector import AccidentDetector
from dashboard import Dashboard
from voice_assistant_windows import VoiceAssistant
from traffic_voice_alerts import TrafficVoiceAlerts
from sos_handler import SOSHandler


class SmartDrivingAssistant:
    def __init__(self, config=None, user_name="Driver", user_id=None, backend_url=None):
        self.config = config or Config()
        self.user_name = user_name

        print("\n" + "=" * 60)
        print("INITIALIZING SMART DRIVING ASSISTANT WITH JARVIS")
        print("=" * 60 + "\n")

        print("📍 Loading lane detector...")
        self.lane_detector = LaneDetector(self.config)

        print("📍 Loading vehicle detector...")
        self.vehicle_detector = VehicleDetector(self.config)

        print("📍 Loading sign detector...")
        self.sign_detector = SignDetector(self.config)

        print("📍 Initializing collision warning...")
        self.collision_warning = CollisionWarning(self.config)

        print("📍 Initializing accident detection...")
        self.accident_detection = AccidentDetector()

        print("📍 Initializing dashboard...")
        self.dashboard = Dashboard(self.config)

        print("\n🎙️ Initializing JARVIS Voice Assistant...\n")
        self.voice_assistant = VoiceAssistant(name="JARVIS")
        self.traffic_alerts = TrafficVoiceAlerts(self.voice_assistant)

        # ============================================================
        # Initialize SOS Handler
        # ============================================================
        print("\n🚨 Initializing SOS Handler...\n")
        if backend_url and user_id:
            self.sos_handler = SOSHandler(
                backend_url=backend_url,
                user_id=user_id
            )
        else:
            print("⚠️ SOS Handler NOT initialized")
            self.sos_handler = None

        print("\n" + "=" * 60)
        print("✅ SYSTEM READY - JARVIS ONLINE")
        print("=" * 60 + "\n")

        self.frame_count = 0
        self.start_time = time.time()
        self.user_name = user_name

    def process_video(self, input_source=None, output_path=None, show_preview=True):
        input_source = input_source or self.config.input_source
        output_path = output_path or self.config.output_path

        # ============================================================
        # STEP 1: GREET USER FIRST
        # ============================================================
        print("🎙️ JARVIS greeting you...\n")
        self.voice_assistant.greet_user(self.user_name)

        print("⏳ Waiting for greeting to complete...\n")
        time.sleep(5)

        print("\n" + "=" * 60)
        print("🎬 STARTING VIDEO PROCESSING")
        print("=" * 60 + "\n")

        # ============================================================
        # STEP 2: START VIDEO
        # ============================================================
        cap = cv2.VideoCapture(input_source)
        if not cap.isOpened():
            raise ValueError(f"Could not open video source: {input_source}")

        fps = int(cap.get(cv2.CAP_PROP_FPS)) or 30
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        print(f"📹 Video: {width}x{height} @ {fps}fps")
        if total_frames > 0:
            print(f"📊 Total frames: {total_frames}\n")

        writer = None
        if output_path:
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

        frame_count = 0
        start_time = time.time()

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                frame_count += 1

                try:
                    result = self.process_frame(frame)
                except KeyboardInterrupt:
                    print("\n⚠️ Interrupted")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}")
                    result = frame

                if writer:
                    writer.write(result)

                if show_preview:
                    display = result
                    if width > 1280:
                        scale = 1280 / width
                        display = cv2.resize(result, None, fx=scale, fy=scale)

                    cv2.imshow('JARVIS - Smart Driving Assistant', display)

                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('q'):
                        print("\n❌ Stopped")
                        break

                if frame_count % 30 == 0:
                    elapsed = time.time() - start_time
                    fps_actual = frame_count / elapsed
                    if total_frames > 0:
                        progress = (frame_count / total_frames) * 100
                        print(f"\r⏱️ Progress: {progress:.1f}% | FPS: {fps_actual:.1f}", end='', flush=True)

        finally:
            cap.release()
            if writer:
                writer.release()
            cv2.destroyAllWindows()

        elapsed = time.time() - start_time
        print(f"\n✅ Done! {frame_count} frames in {elapsed:.1f}s")

    def process_frame(self, frame):
        try:
            lane_data = self.lane_detector.detect(frame)
            detections = self.vehicle_detector.detect(frame)
            lead_vehicle = self.vehicle_detector.get_lead_vehicle(detections, frame.shape[1])
            sign_data = self.sign_detector.detect(frame)
            collision_data = self.collision_warning.analyze(lead_vehicle)
            accident_data = self.accident_detection.analyze(frame, lane_data)

            # ============================================================
            # JARVIS ALERTS
            # ============================================================

            if sign_data and sign_data.get('traffic_light'):
                self.traffic_alerts.traffic_light_alert(sign_data['traffic_light'])

            if lane_data:
                self.traffic_alerts.lane_departure_alert(lane_data)

            if collision_data:
                self.traffic_alerts.collision_warning_alert(collision_data)

            if accident_data:
                self.traffic_alerts.accident_alert(accident_data)

            # ============================================================
            # SOS TRIGGER - SEND TO BACKEND (ONLY when accident shown)
            # ============================================================
            if self.sos_handler and accident_data:
                self.sos_handler.send_sos_alert(accident_data)

            result = self.dashboard.render(
                frame, lane_data, detections, sign_data, collision_data, accident_data
            )

            return result

        except Exception as e:
            print(f"Error: {e}")
            return frame


def main():
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='JARVIS Driving Assistant with SOS')
    parser.add_argument('--input', '-i', type=str, default='dashcam.mp4', help='Input video')
    parser.add_argument('--output', '-o', type=str, default='output.mp4', help='Output video')
    parser.add_argument('--name', '-n', type=str, default='Driver', help='Your name')
    parser.add_argument('--user-id', '-u', type=str, default=None, help='User ID/Phone number')
    parser.add_argument('--backend-url', '-b', type=str, default='http://192.168.3.57:8000/api/sos/trigger',
                        help='Backend SOS API URL')
    parser.add_argument('--no-preview', action='store_true', help='No preview')
    parser.add_argument('--no-save', action='store_true', help='No save')

    args = parser.parse_args()

    input_source = args.input
    try:
        input_source = int(input_source)
    except ValueError:
        pass

    user_id = args.user_id
    if not user_id:
        print("\n" + "=" * 60)
        print("🚨 SOS SYSTEM - USER IDENTIFICATION")
        print("=" * 60)
        print("\nEnter your phone number:")
        print("  Examples: 9876543210, 919876543210, +919876543210\n")
        user_id = input("Enter your User ID/Phone number: ").strip()
        if not user_id:
            print("❌ User ID required")
            sys.exit(1)

    try:
        config = Config(input_source=input_source)
        assistant = SmartDrivingAssistant(
            config,
            user_name=args.name,
            user_id=user_id,
            backend_url=args.backend_url
        )
        output_path = None if args.no_save else args.output

        assistant.process_video(
            input_source=input_source,
            output_path=output_path,
            show_preview=not args.no_preview
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()