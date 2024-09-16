from flask import Flask, request, jsonify, render_template
from google.cloud import speech
from google.oauth2 import service_account
import os

app = Flask(__name__)

# Initialize Google Cloud client with credentials
client_file = "speech-to-text-and-pronunciati-8071b3a2d499.json"
creds = service_account.Credentials.from_service_account_file(client_file)
client = speech.SpeechClient(credentials=creds)

# Serve the index.html at the root URL
@app.route('/')
def index():
    return render_template('index.html')

# Endpoint for receiving audio and translating it
@app.route('/translate', methods=['POST'])
def translate_audio():
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files['audio']
    audio_path = os.path.join('uploads', audio_file.filename)
    audio_file.save(audio_path)

    # Read the audio file for transcription
    with open(audio_path, "rb") as audio:
        content = audio.read()
    
    if not content:  # If the file has no data
        return jsonify({"error": "No audio content found"}), 400

    audio_recognition = speech.RecognitionAudio(content=content)
    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.MP3,
        sample_rate_hertz=48000,
        language_code="en-US",
    )

    response = client.recognize(config=config, audio=audio_recognition)

    transcription = ""
    for result in response.results:
        transcription += result.alternatives[0].transcript + " "

    return jsonify({"transcription": transcription.strip()})

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)
