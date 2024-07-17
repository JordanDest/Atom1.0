import joblib
import pickle
import spacy

# Dictionary to cache models
model_cache = {}

def load_model(model_name):
    """
    Load a model based on its file type.
    """
    if model_name.endswith('.pkl'):
        return load_joblib_model(model_name)  # Assume joblib for .pkl
    elif model_name.endswith('.joblib'):
        return load_joblib_model(model_name)
    elif model_name == 'Music_Parameter_Classification':
        return load_spacy_model(model_name)
    else:
        raise ValueError(f"Unknown model type for: {model_name}")

def load_joblib_model(model_name):
    """
    Load a joblib model.
    """
    #print(f"Loading {model_name} from joblib...")
    return joblib.load(model_name)

def load_spacy_model(model_name):
    """
    Load a Spacy model.
    """
    #print(f"Loading Spacy model: {model_name}...")
    # Make sure to use the correct path for the Spacy model if necessary
    return spacy.load(model_name)

def cache_model(model_name, model):
    """
    Store the model in the cache.
    """
    model_cache[model_name] = model

def get_cached_model(model_name):
    """
    Retrieve a model from the cache if it exists.
    """
    return model_cache.get(model_name)

def get_model(model_name):
    """
    Get a model, either from the cache or by loading it if necessary.
    """
    model = get_cached_model(model_name)
    if model is None:
        model = load_model(model_name)
        cache_model(model_name, model)
    return model




############# EXAMPLE for main file logic:############################
# from models import get_model, cache_model

# # List of essential models to preload
# essential_models = [
#     'Music_action_label_encoder.pkl',
#     'Music_target_label_encoder.pkl',
#     'Music_GradientBoosting_target_pipeline.pkl',
#     'Music_GradientBoosting_action_pipeline.pkl',
#     'Music_Parameter_Classification'  # Spacy model
# ]

# # Define function to return model list based on key
# def model_list(key):
#     if key == 'chem':
#         models = ['svm_Chem_tfidf_vectorizer.joblib', 'svm_chemistry_classifier.joblib']
#     elif key == 'music':
#         models = []  # No additional models needed for music
#     else:
#         models = []
#     return models

# # Function to load and cache models
# def load_models(model_names):
#     for model_name in model_names:
#         model = get_model(model_name)
#         cache_model(model_name, model)
#         print(f"Loaded and cached model: {model_name}")

# # Preload essential models
# load_models(essential_models)

# # Rest of your main application logic
# if __name__ == "__main__":
#     print("Essential models preloaded.")
#     # Continue with your application logic

#     # Set intent and load models accordingly
#     music = 'music'
#     chem = 'chem'
#     intent = music  # Change this to 'chem' if you want to load chemistry models

#     if intent == music:
#         print("Music intent detected: No additional models need to be loaded.")
#     elif intent == chem:
#         additional_models = model_list('chem')
#         load_models(additional_models)
#         print("Chemistry models loaded.")
#     else:
#         print("Unknown intent.")
