from flask import Flask, request, Response
import whisper
from gtts import gTTS
import tempfile
import requests
import env

app = Flask(__name__)

def transcribe_audio(audio_path):
    model = whisper.load_model("small")
    result = model.transcribe(audio_path)
    language = result['language']
    transcript = result['text']
    return transcript, language

def generate_response(req):
    return req

def generate_response_hf(req):
    if req == "":
        return "No request received"
    headers = {
        "Authorization": f"Bearer {env.HF_TOKEN}"
    }
    payload = {
        "inputs": req,
        "parameters": {"return_full_text": False, "max_new_tokens": 50},
        "options": {"use_cache": False}
    }
    response = requests.post(
        "https://api-inference.huggingface.co/models/EleutherAI/gpt-neo-2.7B",
        headers=headers,
        json=payload
    )
    if response.status_code == 200:
        return response.json()[0]['generated_text']
    else:
        return f"Error in API response: {response.status_code}: {response.json()['error']}"

def convert_to_speech(text, language):
    tts = gTTS(text=text, lang=language)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_tts_file:
        tts.save(temp_tts_file.name)
        return temp_tts_file.name

@app.route('/process-audio', methods=['POST'])
def process_audio():
    audio_file = request.files['audio']
    audio_format = audio_file.filename.split('.')[-1]

    print("\tAudio of length", request.content_length, "received")

    # Save the received audio to a temporary file
    with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_audio:
        audio_file.save(temp_audio.name)

        # 1. TRANSCRIBE
        transcript, detected_language = transcribe_audio(temp_audio.name)
        print(f"\tTranscript [{detected_language}]: {transcript}")

        # 2. GENERATE RESPONSE
        response_text = generate_response(transcript)
        print(f"\tGenerated Response: {response_text}")

        # 3. CONVERT TO SPEECH
        tts_output_path = convert_to_speech(response_text, detected_language)

        # Read the file and prepare the response
        with open(tts_output_path, 'rb') as f:
            return_data = f.read()

    response = Response(return_data, mimetype="audio/mpeg")
    response.headers.set('Content-Disposition', 'attachment', filename='processed_audio.mp3')
    return response

if __name__ == "__main__":
    app.run(host=env.SERVER_HOST, port=env.SERVER_PORT, debug=True)
