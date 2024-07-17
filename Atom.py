import logging
from models import get_model, cache_model
from joblib import load
from STT import stt
from TTS import tts 
from picovoice import WakeWordDetector
import os
import govee
from ollama import Ollama
from Weather import weather_call
'''
Error log:
Train sentiment analysis for salutations. Or some way to handle Error vs Success vs Again
Train initial intent detector - create dataset for that
Train chembot
fix IOT issues
Add VTT andN TTS
Add user recognition - lowest priority.
Turn = immediate IOT- turn off music included
More robust IOT handling. I can do more than "Turn" {device} {state} in that order
Volume control for spotify
Starting spotify when not previously playing music.
More robust song queries
Essentially, retrain both IOT and Music because theyre fucked.
Full train PicoVoice
Add basic assistant tasks like time or
include typos in training data
'''
# Configuration
logging.basicConfig(
    filename='log_atom_interactions.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)

essential_models = [
    'Music_action_label_encoder.pkl',
    'Music_target_label_encoder.pkl',
    'Music_GradientBoosting_target_pipeline.pkl',
    'Music_GradientBoosting_action_pipeline.pkl',
    'Music_Parameter_Classification',
    'Intent_SVC_model.joblib',
    'Salutation_SVC_model.joblib'
]

vectorizers_transformers = {
    'Salutation': ('Salutation_vectorizer_Utterance.joblib', 'Salutation_tfidf_Utterance.joblib'),
    'Intent': ('Intent_vectorizer_Command.joblib', 'Intent_tfidf_Command.joblib')
}

# Initialize TTS
tts_service = tts(project_id="enhanced-option-413003", suffix="my-api-key")

def load_models(model_names):
    """Load and cache models."""
    model_count = 0
    for model_name in model_names:
        model = get_model(model_name)
        cache_model(model_name, model)
        model_count += 1
    logger.info(f"Loaded and cached {model_count} models")

def load_model_and_tools(model_file, vectorizer_file, transformer_file):
    """Load the trained model and the pre-processing tools."""
    model = load(model_file)
    vectorizer = load(vectorizer_file)
    transformer = load(transformer_file)
    return model, vectorizer, transformer

def preprocess_and_predict(model, vectorizer, transformer, text):
    """Preprocess the text and predict using the model."""
    text_counts = vectorizer.transform([text])
    text_tfidf = transformer.transform(text_counts)
    prediction = model.predict(text_tfidf)[0]
    return prediction

def control(phrase):
    govee.control(phrase)

def listen():
    return stt.short_speak()

def speak(output):
    tts_service.speak(output)

def check_exit(utterance):
    salutation_model, salutation_vectorizer, salutation_transformer = load_model_and_tools(
        'Salutation_SVC_model.joblib', 'Salutation_vectorizer_Utterance.joblib', 'Salutation_tfidf_Utterance.joblib')
    intent_model, intent_vectorizer, intent_transformer = load_model_and_tools(
        'Intent_SVC_model.joblib', 'Intent_vectorizer_Command.joblib', 'Intent_tfidf_Command.joblib')

    salutation = preprocess_and_predict(salutation_model, salutation_vectorizer, salutation_transformer, utterance)
    logger.info(f"Salutation detected: {salutation}")

    if salutation == "General":
        intent = preprocess_and_predict(intent_model, intent_vectorizer, intent_transformer, utterance)
        logger.info(f"Intent detected: {intent}")
        return intent
    elif salutation == "Exit":
        speak("Understood. I'll go into standby until you request me.")
        return "Exit"
    else:
        logger.info("Non-general salutation detected.")
        return "Blank"

def intent_finder(intent, utterance):
    if intent in ["Exit"]:
        return "Exit"
    
    if intent in ["News", "ScientificResearch", "IoT", "Lexicon", "Music", "Assistant", "Weather", "Blank"]:
        speak("Happily Sir.")
        speak(f"Routing you to: {intent}")
        logger.info(f"Routing to {intent} functionality for utterance: {utterance}")
        if intent == "Music":
            music(utterance)
        elif intent == "IoT":
            control(utterance)
        elif intent == "Blank":
            logger.info("Detected 'Blank' intent.")
        elif intent == "Weather":
            speak(weather_call())
        elif intent == 'ScientificResearch' or "News":
            llm = Ollama()
            try:
                while True:
                    speak("I understand you want me to give a more detailed response, please hold while I load this rather hefty model")
                    result = llm.generate_response(utterance)
                    speak(result)
                    utterance = listen()
                    exit = check_exit(utterance)
                    if exit != "General":
                        break
            except Exception as e:
                print(e)
            logger.info(f"Utterance: {utterance} /n Response: {result}")
        else:
            speak(f"I don't have the functionality for {intent} yet. Blame my creator.")
            logger.info(f"Intent {intent} requested but not yet implemented for utterance: {utterance}")
    else:
        speak("Sorry, I don't understand that request.")
        logger.info(f"Unknown intent classification: {intent} for utterance: {utterance}")
    return "Continue"

def music(utterance):
    import SpotifyController
    spotify_controller = SpotifyController.SpotifyController()
    spotify_controller.interpret_command(utterance)

def log_interaction(utterance):
    logger.info(f"User interaction: {utterance}")
def welcome():
    speak("Hello, I am an Artificial Intelligence in Training. Please wait while I get ready to assist you.")
    load_models(essential_models)
    speak("Initialization complete. I am ready to help!")

def detector():
    detector = WakeWordDetector()
    detector.start()
    detector.wait_for_wake_word()

def main_loop():
    welcome()
    while True:
        detector()
        while True:
            utterance = listen()
            if not utterance:
                break  # Break the inner loop if no utterance is recognized
            log_interaction(utterance)
            intent = check_exit(utterance)
            if intent == "Blank" or intent == "Exit":
                break
            action_result = intent_finder(intent, utterance)
            if action_result == "Exit":
                break


if __name__ == "__main__":
    main_loop()
