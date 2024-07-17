# STT.py
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import os
import time

# Load environment variables
load_dotenv()
subscription_key = os.getenv("Azure_SpeechKey")
service_region = os.getenv("Azure_ServiceRegion")

# Verify that the variables are not None
if subscription_key is None:
    raise ValueError("Azure_SpeechKey environment variable is not set")
if service_region is None:
    raise ValueError("Azure_ServiceRegion environment variable is not set")

# Initialize the speech configuration
speech_config = speechsdk.SpeechConfig(subscription=subscription_key, region=service_region)
speech_config.speech_recognition_language = "en-US"

# Initialize the audio configuration (default microphone)
audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

class SpeechToText:
    def __init__(self):
        self.speech_config = speech_config
        self.audio_config = audio_config

    def short_speak(self):
        """Perform one-shot speech recognition."""
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=self.audio_config)
        print("Say something...")

        result = speech_recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            print("Recognized: {}".format(result.text))
            return result.text
        elif result.reason == speechsdk.ResultReason.NoMatch:
            #print("No speech could be recognized: {}".format(result.no_match_details))
            print("Silence Detected. Going into Standby")
            return None
        elif result.reason == speechsdk.ResultReason.Canceled:
            cancellation_details = result.cancellation_details
            print("Speech Recognition canceled: {}".format(cancellation_details.reason))
            if cancellation_details.reason == speechsdk.CancellationReason.Error:
                print("Error details: {}".format(cancellation_details.error_details))
            return None
        elif result.no_match_details.reason == speechsdk.NoMatchReason.InitialSilenceTimeout:
            print("Initial silence timeout, waiting for wake word...")
            return None

    def long_speak(self):
        """Perform continuous speech recognition until silence is detected."""
        speech_recognizer = speechsdk.SpeechRecognizer(speech_config=self.speech_config, audio_config=self.audio_config)
        print("Listening...")

        done = False
        silence_start_time = None
        recognized_text = []

        def stop_cb(evt):
            print('CLOSING on {}'.format(evt))
            nonlocal done
            done = True

        def recognizing_cb(evt):
            nonlocal silence_start_time
            silence_start_time = None
            print(f'RECOGNIZING: {evt.result.text}')

        def recognized_cb(evt):
            nonlocal silence_start_time, recognized_text
            print(f'RECOGNIZED: {evt.result.text}')
            if evt.result.text.strip() == "":
                if silence_start_time is None:
                    silence_start_time = time.time()
                elif time.time() - silence_start_time > 2:
                    print("Detected 2 seconds of silence, stopping recognition...")
                    speech_recognizer.stop_continuous_recognition_async().get()
                    silence_start_time = None
            else:
                recognized_text.append(evt.result.text)
                silence_start_time = None

        def canceled_cb(evt):
            print(f'CANCELED: Reason={evt.reason} ErrorDetails={evt.error_details}')
            nonlocal done
            done = True

        def session_started_cb(evt):
            print(f'SESSION STARTED: {evt}')

        def session_stopped_cb(evt):
            print(f'SESSION STOPPED: {evt}')
            nonlocal done
            done = True

        # Connect callbacks
        speech_recognizer.recognizing.connect(recognizing_cb)
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.session_started.connect(session_started_cb)
        speech_recognizer.session_stopped.connect(session_stopped_cb)
        speech_recognizer.canceled.connect(canceled_cb)

        # Start continuous recognition
        print("Starting continuous recognition...")
        speech_recognizer.start_continuous_recognition()

        while not done:
            time.sleep(0.1)

        print("Recognition stopped.")
        final_text = " ".join(recognized_text)
        print("Final Recognized Text:")
        print(final_text)
        return final_text

# Create an instance of SpeechToText to be used in other modules
stt = SpeechToText()
