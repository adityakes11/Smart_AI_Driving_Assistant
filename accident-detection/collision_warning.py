import numpy as np
from collections import deque


class CollisionWarning:
    def __init__(self, config):
        self.config = config
        self.distance_history = deque(maxlen=10)

    def analyze(self, lead_vehicle, estimated_speed=None):
        """Analyze collision risk with lead vehicle."""
        if lead_vehicle is None:
            self.distance_history.clear()
            return {
                'warning_level': 'NONE',
                'distance': None,
                'message': None,
                'show_warning': False
            }

        distance = lead_vehicle['distance']
        self.distance_history.append(distance)

        if distance < 10:
            return {
                'warning_level': 'WARNING',
                'distance': distance,
                'message': 'REDUCE YOUR SPEED',
                'show_warning': True
            }

        return {
            'warning_level': 'NONE',
            'distance': None,
            'message': None,
            'show_warning': False
        }