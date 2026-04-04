import time


class TrafficVoiceAlerts:
    def __init__(self, voice_assistant):
        """Initialize traffic alerts with voice"""
        self.voice_assistant = voice_assistant

        # Track CURRENT state
        self.current_traffic_light = None
        self.current_lane_departure = None
        self.current_accident_state = None

        # Lane departure timer
        self.lane_departure_start_time = {}
        self.lane_departure_threshold = 15

        # Collision: track last time we spoke
        self.last_collision_speak_time = 0
        self.collision_speak_cooldown = 15  # 15 seconds cooldown

    def traffic_light_alert(self, traffic_light):
        """Alert only when traffic light STATE CHANGES"""
        if traffic_light is None:
            return

        # Only speak if state changed
        if traffic_light != self.current_traffic_light:
            self.current_traffic_light = traffic_light

            if traffic_light == 'RED':
                self.voice_assistant.speak("Red light ahead. Please stop immediately.")
            elif traffic_light == 'GREEN':
                self.voice_assistant.speak("Green light ahead. You can go.")
            elif traffic_light == 'YELLOW':
                self.voice_assistant.speak("Yellow light. Prepare to stop.")

    def speed_warning_alert(self, lead_vehicle_distance):
        """Speed warning - not used anymore"""
        pass

    def lane_departure_alert(self, lane_data):
        """Lane departure after 15 seconds - speak only ONCE"""
        if lane_data is None or not lane_data.get('departure_warning'):
            # Back in lane
            self.lane_departure_start_time = {}
            self.current_lane_departure = None
            return

        direction = lane_data['departure_warning']
        current_time = time.time()

        # Start timer if not already started
        if direction not in self.lane_departure_start_time:
            self.lane_departure_start_time[direction] = current_time
            return

        elapsed_time = current_time - self.lane_departure_start_time[direction]

        # Only speak ONCE after 15 seconds, not repeatedly
        if elapsed_time > self.lane_departure_threshold and self.current_lane_departure != direction:
            self.current_lane_departure = direction
            msg = f"Alert! You have been drifting to the {direction} for over 15 seconds. Return to your lane!"
            self.voice_assistant.speak(msg)

    def collision_warning_alert(self, collision_data):
        """Collision warning - speak ONCE, then wait 15 seconds before speaking again"""
        if collision_data is None or not collision_data.get('show_warning'):
            # No warning
            return

        warning_level = collision_data.get('warning_level', 'NONE')
        distance = collision_data.get('distance', 0)
        current_time = time.time()

        # Only alert if distance < 10m
        if distance < 10 and warning_level != 'NONE':
            # Check if 15 seconds have passed since last speak
            time_since_last_speak = current_time - self.last_collision_speak_time

            if time_since_last_speak >= self.collision_speak_cooldown:
                # Cooldown finished, speak now
                self.last_collision_speak_time = current_time
                msg = f"Vehicle ahead at {distance:.1f} meters. Reduce your speed!"
                self.voice_assistant.speak(msg)

    def accident_alert(self, accident_data):
        """Accident alert only when state CHANGES"""
        if accident_data is None:
            is_accident = False
        else:
            is_accident = accident_data.get('accident_detected', False)

        # Only speak when accident STARTS (not continuously)
        if is_accident and self.current_accident_state != True:
            self.current_accident_state = True
            msg = "Critical alert! An accident has been detected. Emergency services contacted. Please remain calm."
            self.voice_assistant.speak(msg)

        # Reset when accident ends
        elif not is_accident and self.current_accident_state == True:
            self.current_accident_state = False