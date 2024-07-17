# picovoice.py
import pvporcupine
from pvrecorder import PvRecorder
from dotenv import load_dotenv
import os

class WakeWordDetector:
    def __init__(self):
        load_dotenv()
        access_key = os.getenv("PicoVoiceKey")
        keyword_path = 'Hey-Atom_en_windows_v3_0_0.ppn'  

        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[keyword_path]
        )
        self.recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)

    def start(self):
        self.recorder.start()
        print("Listening for 'Hey Atom'...")

    def wait_for_wake_word(self):
        while True:
            pcm = self.recorder.read()
            result = self.porcupine.process(pcm)
            if result >= 0:
                print("Detected 'Hey Atom'!")
                break
        
        self.porcupine.delete()
        self.recorder.delete()
