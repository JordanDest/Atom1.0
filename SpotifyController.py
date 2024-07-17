import os
import logging
from models import get_model
import spacy
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configure the logging system
logging.basicConfig(
    filename='log_atom_interactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
'''
Error log:
Retrain Target classifier. "Play back in black" should not play backstreet boys. Provide more data regarding single song no context requests
Activate device upon intialization. songs wont play unless the device is already playing music, not the best for a speaker system.
When retraining, make sure to differentiate between rewind and replay. Spotify does both and currently regardless of wording it will play the last completed track
When retraining, be sure to include odd orders of words. Ex. Attempting to play: search_query=artist:ACDC back in black.
Decrease volume by 20 - somehow doesnt work?
'''
logger = logging.getLogger(__name__)

class SpotifyController:
    def __init__(self):
        self.sp = self.authenticate_spotify()
        self.volume_level = self.get_current_volume()  # Initialize volume_level with the current volume
        self.load_models()

    def authenticate_spotify(self):
        load_dotenv()
        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        try:
            auth_manager = SpotifyOAuth(client_id=client_id,
                                        client_secret=client_secret,
                                        redirect_uri="http://localhost:8888/callback",
                                        scope="user-modify-playback-state user-read-playback-state user-read-currently-playing")
            logger.info("Spotify authentication successful")
            return spotipy.Spotify(auth_manager=auth_manager)
        except Exception as e:
            logger.error(f"Failed to authenticate with Spotify: {e}")
            return None

    def load_models(self):
        try:
            # Load Spacy model
            self.nlp = get_model("Music_Parameter_Classification")

            # Load Joblib pipelines and label encoders
            self.action_pipeline = get_model('Music_GradientBoosting_action_pipeline.pkl')
            self.target_pipeline = get_model("Music_GradientBoosting_target_pipeline.pkl")
            self.action_label_encoder = get_model("Music_action_label_encoder.pkl")
            self.target_label_encoder = get_model("Music_target_label_encoder.pkl")

            logger.info("Models loaded successfully")
        except Exception as e:
            logger.error(f"Error loading models: {e}")

    def classify_utterance(self, utterance):
        try:
            # Process the utterance using Spacy
           # doc = self.nlp(utterance)

            # Classify action
            action_pred = self.action_pipeline.predict([utterance])
            action = self.action_label_encoder.inverse_transform(action_pred)[0]
            logger.info(f"Predicted action: {action}")

            # Classify target only if action is 'play' or 'volume'
            target = None
            parameter = None
            if action in ['play', 'volume']:
                target_pred = self.target_pipeline.predict([utterance])
                target = self.target_label_encoder.inverse_transform(target_pred)[0]
                logger.info(f"Predicted target: {target}")

            if action == 'play':
                doc = self.nlp(utterance)
                parameter = " ".join([ent.text for ent in doc.ents])
                logger.info(f"Extracted parameter: {parameter}")

            return action, target, parameter
        except Exception as e:
            logger.error(f"Error classifying utterance '{utterance}': {e}")
            return None, None, None

    def play(self, search_query=None):
        logger.info(f"Attempting to play: search_query={search_query}")
        try:
            if search_query:
                results = self.sp.search(q=search_query, type='track', limit=1)
                tracks = results['tracks']['items']
                if tracks:
                    self.sp.start_playback(uris=[tracks[0]['uri']])
                    logger.info(f"Playing track: {tracks[0]['name']}")
                else:
                    logger.warning("No tracks found for your query.")
            else:
                logger.warning("No search query specified.")
        except Exception as e:
            logger.error(f"Error during playback operation: {e}")

    def stop(self):
        try:
            self.sp.pause_playback()
            logger.info("Playback stopped")
        except Exception as e:
            logger.error(f"Error trying to stop playback: {e}")

    def skip(self):
        try:
            self.sp.next_track()
            logger.info("Skipped to next track")
        except Exception as e:
            logger.error(f"Error trying to skip track: {e}")

    def rewind(self):
        try:
            self.sp.previous_track()
            logger.info("Rewound to previous track")
        except Exception as e:
            logger.error(f"Error trying to rewind track: {e}")

    def adjust_volume(self, direction):
        try:
            new_volume_level = int(direction)  # Assuming direct volume level input
            if 0 <= new_volume_level <= 100:
                self.volume_level = new_volume_level
                self.sp.volume(self.volume_level)  # Adjust the volume on Spotify
                logger.info(f"Volume level set to: {self.volume_level}%")
            else:
                logger.warning("Volume level must be between 0 and 100.")
                return
        except ValueError:
            volume = self.get_current_volume()
            if direction.lower() in ["up"]:
                self.volume_level = min(volume + 10, 100)
                logger.info(f"Volume increased to: {self.volume_level}%")
            elif direction.lower() in ["down"]:
                self.volume_level = max(volume - 10, 0)
                logger.info(f"Volume decreased to: {self.volume_level}%")
            else:
                logger.warning("Invalid volume direction. Use 'increase', 'decrease', or a number between 0 and 100.")

        try:
            self.sp.volume(self.volume_level)  # Adjust the volume on Spotify
        except Exception as e:
            logger.error(f"Error adjusting volume: {e}")

    def interpret_command(self, utterance):
        action, target, parameter = self.classify_utterance(utterance)
        logger.info(f"Interpreting: {utterance}")
        try:
            if action == "play":
                if target in ["song", "artist", "genre", "album", "playlist"]:
                    search_query = f"{target}:{parameter}" if target != "song" else parameter
                    self.play(search_query=search_query)
                else:
                    logger.warning(f"Unsupported target for action 'play': {target}")
            elif action in ["stop", "pause"]:
                self.stop()
            elif action == "skip":
                self.skip()
            elif action == "rewind":
                self.rewind()
            elif action == "volume":
                self.adjust_volume(target)
            else:
                logger.warning(f"Action '{action}' is not recognized. Please try again.")
        except Exception as e:
            logger.error(f"Error interpreting command '{utterance}': {e}")

    def list_devices(self):
        logger.info("Fetching available devices...")
        try:
            devices = self.sp.devices()
            if 'devices' in devices:
                for device in devices['devices']:
                    logger.info(f"Device Name: {device['name']}, Device ID: {device['id']}, Type: {device['type']}, Active: {device['is_active']}")
            else:
                logger.warning("No devices found. Make sure your device is connected to Spotify.")
        except Exception as e:
            logger.error(f"Failed to fetch devices: {e}")

    def get_current_volume(self):
        try:
            devices = self.sp.devices()
            if 'devices' in devices:
                for device in devices['devices']:
                    if device['is_active']:
                        logger.info(f"Current active device: {device['name']}, Volume Level: {device['volume_percent']}%")
                        return device['volume_percent']
                logger.warning("No active device found. Returning default volume level.")
            else:
                logger.warning("No devices found. Make sure your device is connected to Spotify.")
        except Exception as e:
            logger.error(f"Failed to fetch current volume level: {e}")

        #return 50  # Return default volume level as fallback


# if __name__ == "__main__":
#     spotify_controller = SpotifyController()
#     spotify_controller.interpret_command("play back in black by acdc")
