import sounddevice as sd
import requests
import tempfile
import numpy as np
from scipy.io.wavfile import write
import pygame

# Record Audio
def record_audio(duration=5, fs=44100):
    print("Recording...")
    recording = sd.rec(int(duration * fs), samplerate=fs, channels=2, dtype='float64')
    sd.wait()
    return recording

def play_audio(file_path):
    # Initialize pygame
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():  # wait for music to finish playing
        pygame.time.Clock().tick(10)

# Save Audio to a WAV file
def save_audio(recording, fs, file_path):
    write(file_path, fs, np.int16(recording * 32767))

# Main function
def main():
    # Record for 5 seconds
    recording = record_audio(duration=5)

    # Save to a temporary file for recording
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
        save_audio(recording, 44100, temp_file.name)

        print("Sending the audio to the API...")
        # Send the audio file to the API
        with open(temp_file.name, 'rb') as audio:
            response = requests.post("http://localhost:5000/process-audio", files={'audio': audio})

        # Check if the request was successful
        if response.status_code == 200:
            print("Length of response content:", len(response.content))
            # Use a temporary file for the response audio
            with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_output_file:
                temp_output_file.write(response.content)
                temp_output_file_path = temp_output_file.name

            # Play the returned audio
            print("Playing the response audio...")
            play_audio(temp_output_file_path)
        else:
            print("Error in API response:", response.status_code)

if __name__ == "__main__":
    main()
