import cv2
import numpy as np


class Dashboard:
    def __init__(self, config):
        self.config = config

        # Track when accident alert was first shown
        self.accident_alert_start_time = None
        self.accident_alert_duration = 15  # 15 seconds

        # Colors (BGR)
        self.COLORS = {
            'lane': (0, 255, 0),
            'lane_warning': (0, 165, 255),
            'vehicle_safe': (0, 255, 0),
            'vehicle_caution': (0, 255, 255),
            'vehicle_warning': (0, 165, 255),
            'vehicle_critical': (0, 0, 255),
            'text': (255, 255, 255),
            'red': (0, 0, 255),
            'yellow': (0, 255, 255),
            'green': (0, 255, 0),
        }

    def render(self, frame, lane_data, detections, sign_data, collision_data, accident_data=None):
        """Render all HUD elements onto frame."""
        overlay = frame.copy()

        # 1. Draw lanes
        self._draw_lanes(overlay, lane_data)

        # 2. Draw lane fill (drivable area)
        self._draw_lane_fill(overlay, lane_data)

        # 3. Draw vehicle detections
        self._draw_vehicles(overlay, detections, collision_data)

        # 4. Draw info panels
        self._draw_speed_limit_panel(overlay, sign_data)
        self._draw_traffic_light_panel(overlay, sign_data)
        self._draw_collision_warning_panel(overlay, collision_data)

        # 5. ONLY DRAW ACCIDENT POPUP IF ACCIDENT ACTUALLY DETECTED
        # AND NOT EXPIRED (within 15 seconds)
        if accident_data and accident_data.get('accident_detected'):
            self._draw_accident_alert(overlay, accident_data)
        else:
            # Reset timer when accident ends
            self.accident_alert_start_time = None

        self._draw_lane_departure_warning(overlay, lane_data)

        # 6. Draw minimap/bird's eye view
        self._draw_minimap(overlay, lane_data, detections, sign_data)

        return overlay

    def _draw_lanes(self, frame, lane_data):
        """Draw detected lane lines with smooth polylines."""
        if lane_data is None:
            return

        color = self.COLORS['lane']
        if lane_data.get('departure_warning'):
            color = self.COLORS['lane_warning']

        # Draw left lane
        left_lane = lane_data.get('left_lane')
        if left_lane is not None:
            if isinstance(left_lane, list):
                points = np.array(left_lane, dtype=np.int32)
                cv2.polylines(frame, [points], False, color, 3, cv2.LINE_AA)
            else:
                x1, y1, x2, y2 = left_lane
                cv2.line(frame, (x1, y1), (x2, y2), color, 3)

        # Draw right lane
        right_lane = lane_data.get('right_lane')
        if right_lane is not None:
            if isinstance(right_lane, list):
                points = np.array(right_lane, dtype=np.int32)
                cv2.polylines(frame, [points], False, color, 3, cv2.LINE_AA)
            else:
                x1, y1, x2, y2 = right_lane
                cv2.line(frame, (x1, y1), (x2, y2), color, 3)

    def _draw_lane_fill(self, frame, lane_data):
        """Fill the detected lane area with semi-transparent color."""
        if lane_data is None:
            return

        left = lane_data.get('left_lane')
        right = lane_data.get('right_lane')

        if left is None or right is None:
            return

        if isinstance(left, list) and isinstance(right, list):
            if len(left) < 2 or len(right) < 2:
                return
            pts = np.array(left + right[::-1], dtype=np.int32)
        else:
            try:
                x1_left, y1_left, x2_left, y2_left = left
                x1_right, y1_right, x2_right, y2_right = right
                pts = np.array([
                    [x1_left, y1_left],
                    [x2_left, y2_left],
                    [x2_right, y2_right],
                    [x1_right, y1_right]
                ], np.int32)
            except (TypeError, ValueError):
                return

        overlay = frame.copy()
        color = (0, 255, 0) if not lane_data.get('departure_warning') else (0, 165, 255)
        cv2.fillPoly(overlay, [pts], color)
        cv2.addWeighted(overlay, 0.2, frame, 0.8, 0, frame)

    def _draw_vehicles(self, frame, detections, collision_data):
        """Draw bounding boxes around detected vehicles."""
        warning_level = collision_data.get('warning_level', 'NONE') if collision_data else 'NONE'

        for i, det in enumerate(detections):
            x1, y1, x2, y2 = det['bbox']
            distance = det['distance']
            cls = det['class']

            if i == 0 and warning_level == 'CRITICAL':
                color = self.COLORS['vehicle_critical']
                thickness = 3
            elif i == 0 and warning_level == 'WARNING':
                color = self.COLORS['vehicle_warning']
                thickness = 3
            elif distance < 40:
                color = self.COLORS['vehicle_caution']
                thickness = 2
            else:
                color = self.COLORS['vehicle_safe']
                thickness = 2

            cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness)

            label = f'{cls} {distance:.0f}m'
            label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)[0]
            cv2.rectangle(frame, (x1, y1 - 20), (x1 + label_size[0], y1), color, -1)
            cv2.putText(frame, label, (x1, y1 - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)

    def _draw_speed_limit_panel(self, frame, sign_data):
        """Draw speed limit indicator in top right."""
        if sign_data is None or sign_data.get('speed_limit') is None:
            return

        speed_limit = sign_data.get('speed_limit')
        if speed_limit is None:
            return

        center = (frame.shape[1] - 60, 60)

        cv2.circle(frame, center, 40, (255, 255, 255), -1)
        cv2.circle(frame, center, 40, (0, 0, 255), 4)
        cv2.circle(frame, center, 35, (0, 0, 255), 2)

        text = str(speed_limit)
        font_scale = 1.0 if speed_limit < 100 else 0.8
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
        text_x = center[0] - text_size[0] // 2
        text_y = center[1] + text_size[1] // 2
        cv2.putText(frame, text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, (0, 0, 0), 2)

    def _draw_traffic_light_panel(self, frame, sign_data):
        """Draw traffic light indicator in top left area."""
        if sign_data is None or sign_data.get('traffic_light') is None:
            return

        traffic_light = sign_data.get('traffic_light')
        if traffic_light is None:
            return

        center_x = 60
        center_y = 60

        if traffic_light == 'RED':
            light_color = self.COLORS['red']
            message = 'STOP'
            text_color = (255, 255, 255)
            bg_color = (0, 0, 180)
        elif traffic_light == 'YELLOW':
            light_color = self.COLORS['yellow']
            message = 'STAY'
            text_color = (0, 0, 0)
            bg_color = (0, 200, 200)
        elif traffic_light == 'GREEN':
            light_color = self.COLORS['green']
            message = 'GO'
            text_color = (0, 0, 0)
            bg_color = (0, 150, 0)
        else:
            return

        panel_width = 120
        panel_height = 130
        x1 = center_x - panel_width // 2
        y1 = center_y - panel_height // 2

        cv2.rectangle(frame, (x1, y1), (x1 + panel_width, y1 + panel_height), bg_color, -1)
        cv2.rectangle(frame, (x1, y1), (x1 + panel_width, y1 + panel_height), (200, 200, 200), 2)

        cv2.circle(frame, (center_x, center_y - 25), 30, light_color, -1)
        cv2.circle(frame, (center_x, center_y - 25), 30, (200, 200, 200), 2)

        text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)[0]
        text_x = center_x - text_size[0] // 2
        text_y = center_y + 30
        cv2.putText(frame, message, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.9, text_color, 2)

    def _draw_collision_warning_panel(self, frame, collision_data):
        """Draw collision warning indicator."""
        if collision_data is None or not collision_data.get('show_warning'):
            return

        message = collision_data.get('message')
        distance = collision_data.get('distance', 0)

        if not message:
            return

        h, w = frame.shape[:2]

        panel_width = 500
        panel_height = 100
        x1 = (w - panel_width) // 2
        y1 = 30

        overlay = frame.copy()
        cv2.rectangle(overlay, (x1 - 10, y1 - 10), (x1 + panel_width + 10, y1 + panel_height + 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)

        cv2.rectangle(frame, (x1, y1), (x1 + panel_width, y1 + panel_height), (0, 0, 255), -1)
        cv2.line(frame, (x1, y1), (x1 + panel_width, y1), (0, 255, 255), 4)
        cv2.line(frame, (x1, y1 + panel_height), (x1 + panel_width, y1 + panel_height), (0, 165, 255), 4)
        cv2.rectangle(frame, (x1, y1), (x1 + panel_width, y1 + panel_height), (255, 255, 255), 2)

        icon_x = x1 + 30
        icon_y = y1 + panel_height // 2
        icon_pts = np.array([[icon_x, icon_y - 20], [icon_x - 15, icon_y + 15], [icon_x + 15, icon_y + 15]],
                            dtype=np.int32)
        cv2.fillPoly(frame, [icon_pts], (0, 255, 255))
        cv2.polylines(frame, [icon_pts], True, (255, 255, 255), 2)

        text = message
        text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1.3, 3)[0]
        text_x = x1 + (panel_width - text_size[0]) // 2
        text_y = y1 + 50

        cv2.putText(frame, text, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.3, (0, 255, 255), 3)

        dist_text = f'Distance: {distance:.1f}m'
        dist_size = cv2.getTextSize(dist_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        dist_x = x1 + (panel_width - dist_size[0]) // 2
        dist_y = y1 + 75

        cv2.putText(frame, dist_text, (dist_x, dist_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    def _draw_accident_alert(self, frame, accident_data):
        """Draw accident alert for 15 seconds - CLEAN VERSION"""
        import time

        # Initialize timer on first accident detection
        if self.accident_alert_start_time is None:
            self.accident_alert_start_time = time.time()

        # Calculate elapsed time
        elapsed_time = time.time() - self.accident_alert_start_time

        # Only show for 15 seconds
        if elapsed_time > self.accident_alert_duration:
            return

        h, w = frame.shape[:2]

        status = accident_data.get('status', 'NORMAL')

        # Determine colors based on severity
        if status == 'SEVERE':
            color = (0, 0, 255)  # Red
            thickness = 8
            font_scale = 2.5
        else:
            color = (0, 165, 255)  # Orange
            thickness = 4
            font_scale = 2.0

        # Main alert box
        panel_width = 700
        panel_height = 200
        x1 = max(10, (w - panel_width) // 2)
        y1 = max(10, (h - panel_height) // 2)
        x2 = min(w - 10, x1 + panel_width)
        y2 = min(h - 10, y1 + panel_height)

        # Dark background overlay
        overlay = frame.copy()
        cv2.rectangle(overlay, (x1 - 10, y1 - 10), (x2 + 10, y2 + 10), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.8, frame, 0.2, 0, frame)

        # Heavy colored border
        for i in range(thickness):
            cv2.rectangle(frame, (x1 + i, y1 + i), (x2 - i, y2 - i), color, 2)

        # Main message (BIG AND CENTERED)
        message = "ACCIDENT DETECTED"
        text_size = cv2.getTextSize(message, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 4)[0]
        text_x = x1 + (panel_width - text_size[0]) // 2
        text_y = y1 + (panel_height // 2) + 30
        cv2.putText(frame, message, (text_x, text_y),
                    cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 5)

    def _draw_lane_departure_warning(self, frame, lane_data):
        """Draw lane departure warning."""
        if lane_data is None or not lane_data.get('departure_warning'):
            return

        direction = lane_data['departure_warning']
        h, w = frame.shape[:2]

        if direction == 'LEFT':
            pts = np.array([[50, h // 2], [100, h // 2 - 50], [100, h // 2 + 50]], np.int32)
            cv2.fillPoly(frame, [pts], (0, 165, 255))
            cv2.putText(frame, 'LANE', (30, h // 2 + 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
        else:
            pts = np.array([[w - 50, h // 2], [w - 100, h // 2 - 50], [w - 100, h // 2 + 50]], np.int32)
            cv2.fillPoly(frame, [pts], (0, 165, 255))
            cv2.putText(frame, 'LANE', (w - 80, h // 2 + 80),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

    def _draw_minimap(self, frame, lane_data, detections, sign_data):
        """Draw a bird's eye view minimap with traffic light indicator."""
        h, w = frame.shape[:2]

        map_w, map_h = 180, 230
        map_x, map_y = 20, h - map_h - 20

        minimap = np.zeros((map_h, map_w, 3), dtype=np.uint8)
        minimap[:] = (50, 50, 50)

        cv2.rectangle(minimap, (0, 0), (map_w, 30), (40, 40, 40), -1)
        cv2.putText(minimap, 'ADAS VIEW', (5, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

        if sign_data and sign_data.get('traffic_light'):
            traffic_light = sign_data.get('traffic_light')
            if traffic_light == 'RED':
                light_color = self.COLORS['red']
            elif traffic_light == 'YELLOW':
                light_color = self.COLORS['yellow']
            elif traffic_light == 'GREEN':
                light_color = self.COLORS['green']
            else:
                light_color = (200, 200, 200)

            cv2.circle(minimap, (map_w - 20, 15), 8, light_color, -1)
            cv2.circle(minimap, (map_w - 20, 15), 8, (150, 150, 150), 1)

        road_left = map_w // 4
        road_right = 3 * map_w // 4
        cv2.rectangle(minimap, (road_left, 50), (road_right, map_h), (80, 80, 80), -1)

        for i in range(50, map_h, 20):
            cv2.line(minimap, (map_w // 2, i), (map_w // 2, i + 10), (255, 255, 255), 2)

        ego_x = map_w // 2
        ego_y = map_h - 40
        cv2.rectangle(minimap, (ego_x - 12, ego_y - 20), (ego_x + 12, ego_y + 20), (0, 255, 0), -1)
        cv2.rectangle(minimap, (ego_x - 12, ego_y - 20), (ego_x + 12, ego_y + 20), (200, 200, 200), 2)

        pts = np.array([[ego_x, ego_y - 25], [ego_x - 8, ego_y - 15], [ego_x + 8, ego_y - 15]], np.int32)
        cv2.fillPoly(minimap, [pts], (0, 255, 0))

        vehicle_count = 0
        for det in detections[:5]:
            if det['class'] not in ['car', 'truck', 'bus']:
                continue

            distance = det['distance']
            center_x = det['center'][0]

            lateral = (center_x / w) * map_w
            lateral = int(np.clip(lateral, road_left + 10, road_right - 10))

            longitudinal = int(map_h - 40 - (distance / 100) * (map_h - 90))
            longitudinal = np.clip(longitudinal, 50, ego_y - 40)

            if distance < 30:
                color = (0, 0, 255)
                thickness = 2
            elif distance < 50:
                color = (0, 165, 255)
                thickness = 1
            else:
                color = (0, 255, 255)
                thickness = 1

            cv2.rectangle(minimap, (lateral - 10, longitudinal - 15),
                          (lateral + 10, longitudinal + 15), color, thickness)

            dist_label = f'{distance:.0f}m'
            cv2.putText(minimap, dist_label, (lateral - 15, longitudinal - 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.3, color, 1)

            vehicle_count += 1

        if vehicle_count > 0:
            cv2.putText(minimap, f'{vehicle_count} vehicles', (5, map_h - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.35, (200, 200, 200), 1)

        frame[map_y:map_y + map_h, map_x:map_x + map_w] = minimap
        cv2.rectangle(frame, (map_x, map_y), (map_x + map_w, map_y + map_h), (100, 100, 100), 3)