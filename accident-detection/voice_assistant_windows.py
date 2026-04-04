import os
import threading
import time


class VoiceAssistant:
    def __init__(self, name="JARVIS"):
        """Initialize JARVIS using Windows TTS"""
        print(f"🎙️ Initializing {name} Voice Assistant (Windows TTS)...")
        self.name = name
        self.speaking_thread = None
        print("✅ TTS Engine Ready!\n")

    def _speak_in_background(self, message):
        """Speak in background thread so video keeps playing"""
        try:
            # Escape quotes in message
            message = message.replace('"', '\\"')
            message = message.replace("'", "\\'")

            # Use Windows PowerShell to speak (non-blocking)
            command = f'powershell -Command "Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak(\'{message}\')"'

            os.system(command)

        except Exception as e:
            print(f"❌ Error: {e}")

    def speak(self, message):
        """Speak without blocking video"""
        if not message:
            return

        print(f"🔊 Speaking: {message}")

        # Speak in background thread so video continues
        self.speaking_thread = threading.Thread(target=self._speak_in_background, args=(message,), daemon=True)
        self.speaking_thread.start()

    def greet_user(self, user_name):
        """Greet user"""
        greeting = f"Hello {user_name}, how are you today? I am JARVIS, your smart driving assistant."
        self.speak(greeting)

    def stop(self):
        """Stop assistant"""
        pass