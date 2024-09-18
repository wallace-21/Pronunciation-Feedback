from flask import Flask, request, jsonify, render_template
from google.cloud import speech
from google.oauth2 import service_account
import os
import nltk
import phonetics
from nltk.corpus import cmudict

# Define PHONEME_MAPPING and phonemes_to_readable function
PHONEME_MAPPING = {
    'AA': 'ah', 'AE': 'a', 'AH': 'uh', 'AO': 'aw', 'AW': 'ow',
    'AY': 'eye', 'B': 'b', 'CH': 'ch', 'D': 'd', 'DH': 'th',
    'EH': 'e', 'ER': 'er', 'EY': 'ay', 'F': 'f', 'G': 'g',
    'HH': 'h', 'IH': 'i', 'IY': 'ee', 'JH': 'j', 'K': 'k',
    'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ng', 'OW': 'o',
    'OY': 'oy', 'P': 'p', 'R': 'r', 'S': 's', 'SH': 'sh',
    'T': 't', 'TH': 'th', 'UH': 'uh', 'UW': 'oo', 'V': 'v',
    'W': 'w', 'Y': 'y', 'Z': 'z', 'ZH': 'zh',
    'EH': 'e', 'IH': 'i', 'AH': 'uh', 'EH': 'e', 'UH': 'uh'
}

def phonemes_to_readable(phonemes):
    return '-'.join(PHONEME_MAPPING.get(p, p.lower()) for p in phonemes)

app = Flask(__name__)

# Initialize Google Cloud client with credentials
client_file = "speech-to-text-and-pronunciati-8071b3a2d499.json"
creds = service_account.Credentials.from_service_account_file(client_file)
client = speech.SpeechClient(credentials=creds)

# Serve the index.html at the root URL
@app.route('/')
def index():
    return render_template('index.html')

# Ensure NLTK corpora are downloaded
nltk.download('cmudict')

# Load CMU Pronouncing Dictionary
d = cmudict.dict()

# Function to get phonemes from text
def get_phonemes(word):
    word = word.lower()
    if word in d:
        return d[word][0]  # Return the first pronunciation variant
    else:
        return phonetics.metaphone(word)  # Use metaphone as fallback

# Function to compare pronunciation
def compare_pronunciation(user_text, expected_text):
    user_phonemes = [get_phonemes(word) for word in user_text.split()]
    expected_phonemes = [get_phonemes(word) for word in expected_text.split()]

    feedback = []
    for user_word, expected_word, user_phoneme, expected_phoneme in zip(user_text.split(), expected_text.split(), user_phonemes, expected_phonemes):
        user_readable = phonemes_to_readable(user_phoneme)
        expected_readable = phonemes_to_readable(expected_phoneme)
        if user_phoneme != expected_phoneme:
            feedback.append(f"Try pronouncing '{user_word}' as '{user_readable}'")

    return feedback

# Example usage within your Flask app
@app.route('/feedback', methods=['POST'])
def get_pronunciation_feedback():
    data = request.get_json()
    user_transcription = data.get('transcription', '').lower()
    expected_text = data.get('expected_text', '').lower()

    feedback = compare_pronunciation(user_transcription, expected_text)

    if not feedback:
        feedback = ["Great job! Your pronunciation was correct."]

    return jsonify({"feedback": feedback})

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
