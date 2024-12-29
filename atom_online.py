from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from werkzeug.utils import secure_filename
from multiprocessing import Process
from Atom import handle_text, handle_audio, flask_mode_loop, is_flask_mode

# app = Flask(__name__)
# CORS(app)  # Enable CORS for all routes by default
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@app.route('/process', methods=['POST'])
def process_input():
    app.logger.info('Received request to /process')
    input_text = request.json.get('input_text')
    if not input_text:
        app.logger.error('No input text provided')
        return jsonify({'result': 'No text provided'}), 400

    try:
        # Process the text input (this should return the AI response)
        response_text = handle_text(input_text)
        app.logger.info(f'Response generated: {response_text}')
        return jsonify({'recognized_text': input_text, 'response_text': response_text})
    except Exception as e:
        app.logger.error(f'Error processing input: {e}')
        return jsonify({'result': 'Error processing input'}), 500

@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({'status': 'ok'}), 200

@app.route('/upload_audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        app.logger.error('No audio file provided')
        return jsonify({'result': 'No audio file provided'}), 400
    
    audio = request.files['audio']
    filename = secure_filename(audio.filename)
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio.save(filepath)

    try:
        # Run handle_audio and get both recognized text and response
        recognized_text, response_text = handle_audio(filepath)
        if recognized_text:
            app.logger.info(f'Audio processed. Recognized text: {recognized_text}, Response: {response_text}')
            return jsonify({'recognized_text': recognized_text, 'response_text': response_text})
        else:
            app.logger.error('Processing audio failed')
            return jsonify({'result': 'Error: Processing audio failed.'}), 500
    except Exception as e:
        app.logger.error(f'Error handling audio: {e}')
        return jsonify({'result': 'Error processing audio'}), 500

@app.route('/')
def atom():
    return app.send_static_file('atom.html')

def run_flask_server():
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    # Set the mode to Flask
    is_flask_mode = True

    # Start the Flask server in a separate process
    flask_process = Process(target=run_flask_server)
    flask_process.start()

    # Run the Flask mode loop
    flask_mode_loop()

    # Optionally, join the Flask server process (if you need to wait for it)
    flask_process.join()
