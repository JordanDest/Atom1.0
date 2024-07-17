from google.cloud import texttospeech
from google.cloud import api_keys_v2
import pygame
import io
import os
import sys

class tts:
    def __init__(self, project_id: str, suffix: str):
        #print("Initializing TTS class...")
        self.project_id = project_id
        self.suffix = suffix
        self.api_key = self.create_api_key()
        self.init_pygame()
        #print(f"API Key created: {self.api_key}")

    def init_pygame(self):
        # Temporarily suppress pygame output
        original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        pygame.mixer.init()
        sys.stdout.close()
        sys.stdout = original_stdout

    def create_api_key(self) -> str:
        client = api_keys_v2.ApiKeysClient()
        key = api_keys_v2.Key()
        key.display_name = f"My API key - {self.suffix}"
        request = api_keys_v2.CreateKeyRequest(parent=f"projects/{self.project_id}/locations/global", key=key)
        response = client.create_key(request=request).result()
        return response.key_string

    def synthesize_speech(self, text: str) -> bytes:
        client_options = {
            'api_key': self.api_key,
        }
        client = texttospeech.TextToSpeechClient(client_options=client_options)
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US",
            name="en-US-Standard-I",
            ssml_gender=texttospeech.SsmlVoiceGender.MALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            pitch=-2.0,
            speaking_rate=1.2,
            volume_gain_db=0.0
        )
        response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)
        return response.audio_content

    def play_audio(self, audio_content: bytes):
        audio_stream = io.BytesIO(audio_content)
        with open("temp.wav", "wb") as f:
            f.write(audio_stream.read())

        pygame.mixer.music.load("temp.wav")
        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        pygame.mixer.music.unload()
        os.remove("temp.wav")

    def speak(self, text: str):
        print(f"Starting TTS for text: {text}")
        try:
            audio_content = self.synthesize_speech(text)
            self.play_audio(audio_content)
            #print(f"Finished TTS for text: {text}")
        except Exception as e:
            if "API key expired" in str(e):
                print("API key expired. Refreshing API key...")
                self.api_key = self.create_api_key()
                self.speak(text)
            else:
                print(f"An error occurred: {e}")

# # Example usage:
# if __name__ == "__main__":
#     tts_service = tts(project_id="enhanced-option-413003", suffix="my-api-key")

#     def speak(output):
#         tts_service.speak(output)

#     speak("Hello Sir, I'm glad you've created my voice.")
#     speak("Although a bit more work is needed I'm afraid.")
