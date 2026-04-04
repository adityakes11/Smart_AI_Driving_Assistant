# vehicle_detector.py
import cv2
import numpy as np
from ultralytics import YOLO


class VehicleDetector:
    def __init__(self, config):
        self.config = config
        # Load YOLOv8 model (downloads automatically on first run)
        self.model = YOLO('yolov8n.pt')  # nano model for speed; use 'yolov8s.pt' for better accuracy

        # COCO class names we care about
        self.target_classes = {
            2: 'car',
            3: 'motorcycle',
            5: 'bus',
            7: 'truck',
            0: 'person',
            1: 'bicycle'
        }

        # Tracking for consistent IDs
        self.tracked_objects = {}
        self.next_id = 0

    def detect(self, frame):
        """Detect vehicles and other road objects."""
        results = self.model(frame, verbose=False)[0]

        detections = []

        for box in results.boxes:
            cls_id = int(box.cls[0])
            confidence = float(box.conf[0])

            if cls_id not in self.target_classes:
                continue
            if confidence < self.config.vehicle_confidence_threshold:
                continue

            # Bounding box
            x1, y1, x2, y2 = map(int, box.xyxy[0])

            # Estimate distance based on bounding box size
            distance = self._estimate_distance(y2 - y1, frame.shape[0])

            detections.append({
                'bbox': (x1, y1, x2, y2),
                'class': self.target_classes[cls_id],
                'class_id': cls_id,
                'confidence': confidence,
                'distance': distance,
                'center': ((x1 + x2) // 2, (y1 + y2) // 2)
            })

        # Sort by distance (closest first)
        detections.sort(key=lambda x: x['distance'])

        return detections

    def _estimate_distance(self, bbox_height, frame_height):
        """
        Rough distance estimation based on bounding box size.
        This is a simplified model - real systems use stereo cameras or radar.

        Assumptions:
        - Average car height ~1.5m
        - Camera focal length approximation
        """
        if bbox_height < 10:
            return 999

        # Calibration values (adjust based on your camera)
        REAL_CAR_HEIGHT = 1.5  # meters
        FOCAL_LENGTH = 800  # pixels (approximate)

        distance = (REAL_CAR_HEIGHT * FOCAL_LENGTH) / bbox_height
        return round(distance, 1)

    def get_lead_vehicle(self, detections, frame_width):
        """Find the vehicle directly ahead (in our lane)."""
        center_zone = (frame_width * 0.3, frame_width * 0.7)

        for det in detections:
            center_x = det['center'][0]
            if center_zone[0] <= center_x <= center_zone[1]:
                if det['class'] in ['car', 'truck', 'bus', 'motorcycle']:
                    return det
        return None