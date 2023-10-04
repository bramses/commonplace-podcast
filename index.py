import pvporcupine
import pyaudio
import struct
import threading
import requests
import time
import io
import wave
import speech_recognition as sr
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get access key from environment variable
access_key = os.getenv('PV_ACCESS_KEY')

TEST = True

def call_api(command):
    if TEST:
        print("api call sim:")
        return
    # Replace 'your_api_url' and 'your_api_key' with your API endpoint and key
    response = requests.post(
        'your_api_url',
        headers={'Authorization': 'Bearer your_api_key'},
        json={'command': command}
    )
    print(response.json())  # Print the API response

def recognize_command():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for a command...")
        audio = recognizer.listen(source, timeout=5)
    try:
        command = recognizer.recognize_google(audio)
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    return None

def process_audio():
    while True:
        time.sleep(15)
        audio_data.seek(0)
        audio_chunk = audio_data.read()
        audio_data.seek(0)
        audio_data.truncate()
        call_api(audio_chunk)
        wf = wave.open("audio_chunk_" + str(time.time()) + ".wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_chunk)
        wf.close()

def wake_word_detection():
    porcupine = pvporcupine.create(access_key=access_key, keywords=["jarvis"])
    pa = pyaudio.PyAudio()
    audio_stream = pa.open(
        rate=porcupine.sample_rate,
        channels=1,
        format=pyaudio.paInt16,
        input=True,
        frames_per_buffer=porcupine.frame_length,
        input_device_index=None
    )

    print(f'Listening for wake word: {"jarvis"}')

    try:
        while True:
            pcm = audio_stream.read(porcupine.frame_length)
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print(f'Wake word detected: {"jarvis"}')
                audio_stream.stop_stream()
                command = recognize_command()
                if command:
                    call_api(command)
                audio_stream.start_stream()
    except KeyboardInterrupt:
        print('Stopping ...')
    finally:
        if audio_stream is not None:
            audio_stream.close()
        if porcupine is not None:
            porcupine.delete()
        if pa is not None:
            pa.terminate()

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open a stream
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024)

# Create a BytesIO object to hold the audio data
audio_data = io.BytesIO()

try:
    # Start separate threads to process audio chunks and detect wake word
    threading.Thread(target=process_audio).start()
    threading.Thread(target=wake_word_detection).start()

    while True:
        data = stream.read(1024)
        audio_data.write(data)
except KeyboardInterrupt:
    print("Stopping script...")
    stream.stop_stream()
    stream.close()
    p.terminate()
