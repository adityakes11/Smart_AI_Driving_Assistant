# config.py
from dataclasses import dataclass


@dataclass
class Config:
    # Video settings
    input_source: str = "dashcam.mp4"  # Or 0 for webcam
    output_path: str = "output.mp4"

    # Lane detection
    lane_roi_top_percent: float = 0.6  # Region of interest starts at 60% from top
    lane_hough_threshold: int = 50
    lane_min_line_length: int = 100
    lane_max_line_gap: int = 50

    # Vehicle detection
    vehicle_confidence_threshold: float = 0.5
    vehicle_classes: tuple = (2, 3, 5, 7)  # car, motorcycle, bus, truck in COCO

    # Collision warning
    warning_distance_close: float = 30.0  # meters - red warning
    warning_distance_medium: float = 50.0  # meters - yellow warning

    # Speed limit detection
    speed_limit_default: int = 60  # km/h

    # Display
    display_width: int = 1280
    display_height: int = 720