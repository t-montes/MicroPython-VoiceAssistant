from flask import Flask, request, Response, send_file
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
    print(f"\tTranscript [{language}]: {transcript}")
    return transcript, language

def generate_response(req):
    res = req
    print(f"\tGenerated Response: {res}")
    return res

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
        res = response.json()[0]['generated_text']
    else:
        res = f"Error in API response: {response.status_code}: {response.json()['error']}"
    print(f"\tGenerated Response: {res}")
    return res

def convert_to_speech(text, language):
    tts = gTTS(text=text, lang=language)
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_tts_file:
        tts.save(temp_tts_file.name)
        return temp_tts_file.name

""" Receives an audio file and returns a processed transcript audio file """
@app.route('/process-audio', methods=['POST'])
def process_audio():
    audio_file = request.files['audio']
    use_huggingface = request.args.get('hf', default='0') == '1'
    audio_format = audio_file.filename.split('.')[-1]

    print("\tAudio of length", request.content_length, "received")

    with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as temp_audio:
        audio_file.save(temp_audio.name)

        transcript, detected_language = transcribe_audio(temp_audio.name)
        response_text = (generate_response_hf if use_huggingface else generate_response)(transcript)
        tts_output_path = convert_to_speech(response_text, detected_language)

    return send_file(tts_output_path, as_attachment=True, download_name='processed_audio.mp3', mimetype='audio/mpeg')

    #response = Response(return_data, mimetype="audio/mpeg")
    #response.headers.set('Content-Disposition', 'attachment', filename='processed_audio.mp3')
    #return response

""" Tests that receives a TEXT wav file and returns an AUDIO wav file """
@app.route('/test', methods=['POST'])
def test():
    audio_file = request.files['audio']
    message = audio_file.read()

    # Send the 'message' in an attached file with the same bytes message
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        audio_text = message.decode('utf-8')
        print("Decoded:", audio_text)
        tts = gTTS(text=audio_text, lang='en')
        tts.save(temp_file.name)
        temp_file_path = temp_file.name

    return send_file(temp_file_path, as_attachment=True, download_name='response.wav', mimetype='audio/wav')

""" Tests that receives and returns the same WAV file """
@app.route('/test2', methods=['POST'])
def test2():
    audio_file = request.files['audio']
    message = audio_file.read()

    # Send the 'message' in an attached file with the same bytes message
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        print("Decoded:", message.decode('utf-8'))
        temp_file.write(message)
        temp_file_path = temp_file.name

    return send_file(temp_file_path, as_attachment=True, download_name='response.wav', mimetype='audio/wav')

@app.route('/test-get', methods=['GET'])
def test_get():
    return "OK"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=env.SERVER_PORT, debug=True)
