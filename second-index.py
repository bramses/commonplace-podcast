import pvporcupine
import pyaudio
import struct
import threading
import requests
import time
import io
import wave
import speech_recognition as sr
from collections import deque
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get access key from environment variable
access_key = os.getenv('PV_ACCESS_KEY')

TEST = True
CHUNK_TIME = 5

# Circular buffer to hold the last CHUNK_TIME seconds of audio data
audio_buffer = deque(maxlen=CHUNK_TIME * 16000)  # assuming 16 kHz sample rate

lock = threading.Lock()

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

def recognize_command(audio_data):
    recognizer = sr.Recognizer()
    try:
        command = recognizer.recognize_google(audio_data)
        print(f"You said: {command}")
        return command
    except sr.UnknownValueError:
        print("Could not understand audio")
    except sr.RequestError as e:
        print(f"Could not request results; {e}")
    return None

def process_audio():
    global audio_buffer
    while True:
        time.sleep(CHUNK_TIME)
        with lock:
            # Check if there's enough data in the buffer
            if len(audio_buffer) < CHUNK_TIME * 16000:
                continue
            audio_data = struct.pack('h' * len(audio_buffer), *audio_buffer)
        # ... (rest of your function, if any)
        wf = wave.open("audio_chunk_" + str(time.time()) + ".wav", 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio_data)
        wf.close()

def wake_word_detection():
    global audio_buffer
    porcupine = pvporcupine.create(access_key=access_key, keywords=["jarvis"])
    while True:
        with lock:
            # Check if there's enough data in the buffer
            if len(audio_buffer) < porcupine.frame_length * 2:
                continue
            audio_data = struct.pack('h' * len(audio_buffer), *audio_buffer)
        pcm = struct.unpack_from("h" * porcupine.frame_length, audio_data[-porcupine.frame_length*2:])
        keyword_index = porcupine.process(pcm)
        if keyword_index >= 0:
            print(f'Wake word detected: {"jarvis"}')
            command = recognize_command(io.BytesIO(audio_data))
            if command:
                call_api(command)

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open a stream
stream = p.open(format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=1024,
                input_device_index=None)

try:
    # Start separate threads to process audio chunks and detect wake word
    # threading.Thread(target=process_audio).start()
    threading.Thread(target=wake_word_detection).start()

    while True:
        data = stream.read(1024)
        audio_buffer.extend(struct.unpack_from("h" * (len(data)//2), data))
except KeyboardInterrupt:
    print("Stopping script...")
    stream.stop_stream()
    stream.close()
    p.terminate()