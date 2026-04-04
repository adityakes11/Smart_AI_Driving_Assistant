import cv2
import numpy as np
from ultralytics import YOLO
from collections import deque


class AccidentDetector:
    def __init__(self):
        """Initialize accident detector - optimized for speed"""
        print("🚗 Loading YOLO vehicle detection model...")

        # Use smaller model for faster inference
        self.model = YOLO("yolov8n.pt")  # nano model is faster

        print("✅ Model loaded!")

        # Tracking
        self.tracks = {}
        self.next_id = 0
        self.max_history = 20

        # Motion detection
        self.prev_gray = None
        self.motion_history = deque(maxlen=15)

        # Accident state
        self.accident_active = False
        self.accident_frames = 0
        self.accident_cooldown = 0

        # Ego vehicle info
        self.ego_zone_x_min = 0.25
        self.ego_zone_x_max = 0.75
        self.ego_zone_y_min = 0.55

        # LOWER thresholds for better detection
        self.collision_distance = 80  # Increased from 60
        self.gap_closing_threshold = 25  # Decreased from 35
        self.approaching_speed_threshold = 5  # Decreased from 8
        self.impact_motion_threshold = 50  # Decreased from 80
        self.motion_spike_threshold = 20  # Decreased from 40

        # Frame skip for motion detection
        self.motion_detect_skip = 2
        self.motion_frame_count = 0

    def analyze(self, frame, lane_data=None):
        """Analyze frame - optimized"""
        h, w = frame.shape[:2]

        # Skip motion detection on some frames for speed
        self.motion_frame_count += 1

        # Run YOLO inference WITHOUT resizing frame (let YOLO handle it)
        results = self.model(frame, verbose=False, conf=0.5, imgsz=416)[0]

        detections = self._extract_vehicles(results)
        tracked_objects = self._track_objects(detections)

        ego_vehicle = self._find_ego_vehicle(tracked_objects, h, w)

        accident_flag = False
        severity = 0
        reasons = []

        # Motion detection (every N frames)
        motion_score = 0
        if self.motion_frame_count % self.motion_detect_skip == 0:
            motion_score = self._detect_motion(frame)
            self.motion_history.append(motion_score)
        else:
            if len(self.motion_history) > 0:
                motion_score = self.motion_history[-1]

        # Collision detection
        if ego_vehicle is not None:
            other_vehicles = [obj for obj in tracked_objects if obj['id'] != ego_vehicle['id']]

            if len(other_vehicles) > 0:
                collision_info = self._detect_direct_collision(ego_vehicle, other_vehicles)
                if collision_info['detected']:
                    accident_flag = True
                    severity = collision_info['severity']
                    reasons = collision_info['reasons']

        # Impact detection (less frequent)
        if len(self.motion_history) >= 3 and self.motion_frame_count % 3 == 0:
            impact_info = self._detect_extreme_impact(self.motion_history)
            if impact_info['detected']:
                accident_flag = True
                severity = max(severity, impact_info['severity'])
                reasons.extend(impact_info['reasons'])

        # Accident state management
        if self.accident_cooldown > 0:
            self.accident_cooldown -= 1

        if accident_flag and self.accident_cooldown == 0:
            self.accident_active = True
            self.accident_frames = 1
            self.accident_cooldown = 120

        elif self.accident_active:
            self.accident_frames += 1
            accident_flag = True

            if self.accident_frames > 300:
                self.accident_active = False
                self.accident_frames = 0
        else:
            self.accident_active = False
            self.accident_frames = 0

        # Format output
        if accident_flag:
            status = "SEVERE"
            message = "ACCIDENT DETECTED"
            police_needed = True
            hospital_needed = True
        else:
            status = "NORMAL"
            message = None
            police_needed = False
            hospital_needed = False

        return {
            "accident_detected": accident_flag,
            "severity": min(severity, 100),
            "status": status,
            "message": message,
            "sos_required": accident_flag,
            "police_needed": police_needed,
            "hospital_needed": hospital_needed,
            "reasons": reasons,
            "motion_score": motion_score,
            "vehicle_count": len(tracked_objects),
            "ego_vehicle": ego_vehicle is not None
        }

    def _find_ego_vehicle(self, tracked_objects, h, w):
        """Find OUR vehicle"""
        ego_x_min = w * self.ego_zone_x_min
        ego_x_max = w * self.ego_zone_x_max
        ego_y_min = h * self.ego_zone_y_min

        ego_vehicle = None
        max_area = 0

        for obj in tracked_objects:
            cx = (obj['box'][0] + obj['box'][2]) / 2
            cy = (obj['box'][1] + obj['box'][3]) / 2

            if ego_x_min < cx < ego_x_max and cy > ego_y_min:
                area = (obj['box'][2] - obj['box'][0]) * (obj['box'][3] - obj['box'][1])

                if area > max_area and area > 5000:
                    max_area = area
                    ego_vehicle = obj

        return ego_vehicle

    def _detect_direct_collision(self, ego_vehicle, other_vehicles):
        """Detect direct collision - LOWER thresholds"""
        detected = False
        severity = 0
        reasons = []

        ego_x = (ego_vehicle['box'][0] + ego_vehicle['box'][2]) / 2
        ego_y = (ego_vehicle['box'][1] + ego_vehicle['box'][3]) / 2

        for other in other_vehicles:
            other_x = (other['box'][0] + other['box'][2]) / 2
            other_y = (other['box'][1] + other['box'][3]) / 2

            distance = np.sqrt((ego_x - other_x) ** 2 + (ego_y - other_y) ** 2)

            if distance < self.collision_distance:
                if len(ego_vehicle['box_history']) > 1 and len(other['box_history']) > 1:
                    prev_ego_box = ego_vehicle['box_history'][-2]
                    prev_other_box = other['box_history'][-2]

                    prev_ego_x = (prev_ego_box[0] + prev_ego_box[2]) / 2
                    prev_ego_y = (prev_ego_box[1] + prev_ego_box[3]) / 2
                    prev_other_x = (prev_other_box[0] + prev_other_box[2]) / 2
                    prev_other_y = (prev_other_box[1] + prev_other_box[3]) / 2

                    prev_distance = np.sqrt((prev_ego_x - prev_other_x) ** 2 + (prev_ego_y - prev_other_y) ** 2)
                    gap_closing = prev_distance - distance

                    if gap_closing > self.gap_closing_threshold:
                        detected = True
                        severity = 60  # ⬇️ Changed from 75 to 60
                        reasons.append(f"COLLISION!")

        return {'detected': detected, 'severity': severity, 'reasons': reasons}

    def _detect_extreme_impact(self, motion_history):
        """Detect extreme impacts - LOWER thresholds"""
        detected = False
        severity = 0
        reasons = []

        if len(motion_history) < 3:
            return {'detected': detected, 'severity': severity, 'reasons': reasons}

        current_motion = motion_history[-1]
        prev_motion = motion_history[-2]

        motion_spike = current_motion - prev_motion

        if motion_spike > self.motion_spike_threshold and current_motion > self.impact_motion_threshold:
            detected = True
            severity = 60  # ⬇️ Changed from 70 to 60
            reasons.append(f"IMPACT!")

        return {'detected': detected, 'severity': severity, 'reasons': reasons}

    def _extract_vehicles(self, results):
        """Extract vehicles"""
        vehicles = []

        for box in results.boxes:
            cls = int(box.cls)
            conf = float(box.conf)
            class_name = results.names[cls]

            if conf < 0.4:
                continue

            if class_name in ['car', 'truck', 'bus', 'motorcycle']:
                # Get coordinates directly without modifying
                xyxy = box.xyxy[0].cpu().numpy()
                x1, y1, x2, y2 = xyxy
                vehicles.append({
                    'box': [x1, y1, x2, y2],
                    'class': class_name,
                    'conf': conf
                })

        return vehicles

    def _track_objects(self, detections):
        """Track objects"""
        objects = []
        matched_tracks = set()

        for det in detections:
            box = det['box']
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2

            assigned_id = None
            min_distance = float('inf')

            for obj_id, track_data in self.tracks.items():
                if obj_id in matched_tracks:
                    continue

                history = track_data['positions']
                if len(history) == 0:
                    continue

                prev_cx, prev_cy = history[-1]
                distance = np.hypot(cx - prev_cx, cy - prev_cy)

                if distance < 80 and distance < min_distance:
                    assigned_id = obj_id
                    min_distance = distance

            matched_tracks.add(assigned_id)

            if assigned_id is None:
                assigned_id = self.next_id
                self.next_id += 1
                self.tracks[assigned_id] = {
                    'positions': deque(maxlen=20),
                    'boxes': deque(maxlen=20),
                    'speeds': deque(maxlen=20)
                }

            track_data = self.tracks[assigned_id]
            track_data['positions'].append((cx, cy))
            track_data['boxes'].append(box)

            speed, acc, prev_speed = self._compute_motion(track_data)
            track_data['speeds'].append(speed)

            objects.append({
                "id": assigned_id,
                "box": box,
                "speed": speed,
                "prev_speed": prev_speed,
                "acc": acc,
                "class": det['class'],
                "box_history": list(track_data['boxes']),
            })

        return objects

    def _compute_motion(self, track_data):
        """Compute motion"""
        positions = list(track_data['positions'])
        speeds = list(track_data['speeds'])

        if len(positions) < 3:
            return 0, 0, 0

        p1, p2, p3 = positions[-3], positions[-2], positions[-1]
        v1 = np.linalg.norm(np.array(p2) - np.array(p1))
        v2 = np.linalg.norm(np.array(p3) - np.array(p2))

        prev_speed = speeds[-1] if len(speeds) > 0 else 0
        acceleration = v2 - v1

        return v2, acceleration, prev_speed

    def _detect_motion(self, frame):
        """Detect motion - optimized"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        if self.prev_gray is None:
            self.prev_gray = gray
            return 0

        diff = cv2.absdiff(self.prev_gray, gray)
        motion = np.mean(diff)

        self.prev_gray = gray
        return motion