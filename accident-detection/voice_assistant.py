import pyttsx3
import time


class VoiceAssistant:
    def __init__(self, name="JARVIS"):
        """Initialize JARVIS voice assistant"""
        print(f"🎙️ Initializing {name} Voice Assistant...")

        self.name = name

        try:
            # Initialize engine
            self.engine = pyttsx3.init()

            # Set properties BEFORE speaking
            self.engine.setProperty('rate', 150)
            self.engine.setProperty('volume', 1.0)

            # Test if it works
            print("✅ Engine initialized successfully")

        except Exception as e:
            print(f"❌ Error: {e}")
            self.engine = None

    def speak(self, message):
        """Speak a message"""
        if not message or not self.engine:
            return

        try:
            print(f"🔊 Speaking: {message}")
            self.engine.say(message)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error speaking: {e}")

    def greet_user(self, user_name):
        """Greet user"""
        greeting = f"Hello {user_name}, how are you today? I am JARVIS, your smart driving assistant."
        self.speak(greeting)

    def stop(self):
        """Stop assistant"""
        pass