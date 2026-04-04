import cv2
import numpy as np
from collections import deque
import time


class LaneDetector:
    def __init__(self, config):
        self.config = config
        # Smoothing buffers for stable lane lines
        self.left_lane_buffer = deque(maxlen=15)
        self.right_lane_buffer = deque(maxlen=15)
        self.center_line_buffer = deque(maxlen=15)

        # Lane departure tracking
        self.departure_start_time = None
        self.departure_direction = None
        self.departure_threshold_seconds = 5  # Show warning after 5 seconds
        self.center_threshold_pixels = 50  # Pixels before it's considered departed

        # Lane detection confidence tracking
        self.left_lane_confidence = 0
        self.right_lane_confidence = 0
        self.min_confidence_threshold = 0.3  # Minimum confidence to display lanes

    def detect(self, frame):
        """Main lane detection pipeline."""
        height, width = frame.shape[:2]

        # 1. Preprocess
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, (7, 7), 1)

        # 2. Edge detection with adaptive thresholds
        edges = cv2.Canny(blur, 80, 200)

        # 3. Region of interest mask (focus on current lane area)
        roi_mask = self._create_roi_mask(edges, height, width)
        masked_edges = cv2.bitwise_and(edges, roi_mask)

        # 4. Hough transform for line detection
        lines = cv2.HoughLinesP(
            masked_edges,
            rho=2,
            theta=np.pi / 180,
            threshold=self.config.lane_hough_threshold,
            minLineLength=self.config.lane_min_line_length,
            maxLineGap=self.config.lane_max_line_gap
        )

        # 5. Separate and average lane lines (only current lane)
        left_lane, right_lane, left_conf, right_conf = self._process_lines(lines, height, width)

        # Store confidence
        self.left_lane_confidence = left_conf
        self.right_lane_confidence = right_conf

        # 6. Only display lanes if confidence is above threshold
        lane_display_left = None
        lane_display_right = None

        if left_conf >= self.min_confidence_threshold:
            lane_display_left = self._get_lane_display_points(left_lane, height, width, 'left')

        if right_conf >= self.min_confidence_threshold:
            lane_display_right = self._get_lane_display_points(right_lane, height, width, 'right')

        # 7. Calculate lane center offset (only if both lanes detected)
        if lane_display_left and lane_display_right:
            lane_center_offset = self._calculate_center_offset(left_lane, right_lane, width)
        else:
            lane_center_offset = 0

        # 8. Detect lane departure with 5-second threshold
        departure_warning = self._check_lane_departure_with_timer(lane_center_offset)

        return {
            'left_lane': lane_display_left,
            'right_lane': lane_display_right,
            'left_lane_raw': left_lane,
            'right_lane_raw': right_lane,
            'center_offset': lane_center_offset,
            'departure_warning': departure_warning,
            'edges': masked_edges,
            'left_confidence': left_conf,
            'right_confidence': right_conf
        }

    def _create_roi_mask(self, edges, height, width):
        """Create trapezoidal region of interest focused on current lane."""
        mask = np.zeros_like(edges)

        roi_top = int(height * self.config.lane_roi_top_percent)
        roi_bottom = int(height * 0.95)  # Close to bottom

        # Narrower trapezoid to focus on current lane (center-focused)
        vertices = np.array([[
            (width * 0.25, roi_bottom),  # Bottom left
            (width * 0.35, roi_top),  # Top left
            (width * 0.65, roi_top),  # Top right
            (width * 0.75, roi_bottom)  # Bottom right
        ]], dtype=np.int32)

        cv2.fillPoly(mask, vertices, 255)
        return mask

    def _process_lines(self, lines, height, width):
        """Separate lines into left/right lanes and average them."""
        left_lines = []
        right_lines = []

        if lines is None or len(lines) == 0:
            return self._get_smoothed_lane('left'), self._get_smoothed_lane('right'), 0, 0

        # Center of frame (assumed car position)
        frame_center = width / 2

        for line in lines:
            x1, y1, x2, y2 = line[0]
            if x2 == x1:
                continue

            slope = (y2 - y1) / (x2 - x1)
            intercept = y1 - slope * x1

            # Filter by slope - ignore near-horizontal and vertical lines
            if abs(slope) < 0.4 or abs(slope) > 3:
                continue

            # Determine if this line belongs to left or right lane
            mid_x = (x1 + x2) / 2

            if slope < 0:  # Negative slope (left lane in image coordinates)
                if mid_x < frame_center:  # And physically on the left
                    left_lines.append((slope, intercept))
            else:  # Positive slope (right lane)
                if mid_x > frame_center:  # And physically on the right
                    right_lines.append((slope, intercept))

        # Average and extrapolate only the current lane section
        left_lane, left_conf = self._average_lane(left_lines, height, width, 'left')
        right_lane, right_conf = self._average_lane(right_lines, height, width, 'right')

        return left_lane, right_lane, left_conf, right_conf

    def _average_lane(self, lines, height, width, side):
        """Average line parameters and extrapolate to lane display section."""
        if not lines:
            return self._get_smoothed_lane(side), 0  # Return 0 confidence

        # Calculate confidence based on number of lines detected
        confidence = min(len(lines) / 5.0, 1.0)  # Max confidence at 5+ lines

        avg_slope = np.mean([l[0] for l in lines])
        avg_intercept = np.mean([l[1] for l in lines])

        # MUCH SHORTER display - only show 200 pixels worth
        y1 = height - 50  # Start 50px from bottom
        y2 = height - 250  # End 250px from bottom (only 200px line)

        if avg_slope == 0:
            x1, x2 = 0, 0
        else:
            x1 = int((y1 - avg_intercept) / avg_slope)
            x2 = int((y2 - avg_intercept) / avg_slope)

        # Clamp x values to frame boundaries
        x1 = np.clip(x1, 0, width)
        x2 = np.clip(x2, 0, width)

        lane = (x1, y1, x2, y2)

        # Add to buffer for smoothing
        if side == 'left':
            self.left_lane_buffer.append(lane)
        else:
            self.right_lane_buffer.append(lane)

        return self._get_smoothed_lane(side), confidence

    def _get_lane_display_points(self, lane, height, width, side):
        """Get smoothed lane points for display with better interpolation."""
        if lane is None:
            return None

        x1, y1, x2, y2 = lane

        # Create multiple points along the line for smoother rendering (fewer points for short line)
        points = []
        steps = 5  # Reduced from 10 for shorter line
        for i in range(steps + 1):
            t = i / steps
            x = int(x1 * (1 - t) + x2 * t)
            y = int(y1 * (1 - t) + y2 * t)
            points.append((x, y))

        return points

    def _get_smoothed_lane(self, side):
        """Return smoothed lane from buffer with better averaging."""
        buffer = self.left_lane_buffer if side == 'left' else self.right_lane_buffer
        if not buffer:
            return None

        # Use median for more robust smoothing
        buffer_array = np.array(list(buffer))
        smoothed = np.median(buffer_array, axis=0)

        return tuple(smoothed.astype(int))

    def _calculate_center_offset(self, left_lane, right_lane, width):
        """Calculate how far the car is from lane center."""
        if left_lane is None or right_lane is None:
            return 0

        # Lane center at bottom of image (y = height)
        left_x = left_lane[0]
        right_x = right_lane[0]
        lane_center = (left_x + right_x) / 2

        # Car center (assume camera is centered)
        car_center = width / 2

        # Offset in pixels (positive = right of center)
        offset = car_center - lane_center

        return offset

    def _check_lane_departure_with_timer(self, offset, threshold=50):
        """
        Check if vehicle is departing from lane.
        Only show warning after continuous departure for 5 seconds.
        """
        current_time = time.time()
        is_departed = abs(offset) > threshold

        if is_departed:
            # Vehicle is outside lane
            new_direction = "LEFT" if offset > 0 else "RIGHT"

            # If just started departing or direction changed, reset timer
            if self.departure_start_time is None or self.departure_direction != new_direction:
                self.departure_start_time = current_time
                self.departure_direction = new_direction

            # Check if departed for 5+ seconds
            departure_duration = current_time - self.departure_start_time
            if departure_duration >= self.departure_threshold_seconds:
                return new_direction
            else:
                # Still within 5 second grace period
                return None
        else:
            # Vehicle is back in lane - reset timer
            self.departure_start_time = None
            self.departure_direction = None
            return None