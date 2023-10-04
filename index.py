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
CHUNK_TIME = 5

def call_api(command):
    if TEST:
        print("api call sim:", command)
        return
    # Replace 'your_api_url' and 'your_api_key' with your API endpoint and key
    response = requests.post(
        'your_api_url',
        headers={'Authorization': 'Bearer your_api_key'},
        json={'command': command}
    )
    print(response.json())  # Print the API response

UNLOCKED = True

def process_audio():
    while True:
        if UNLOCKED:
            time.sleep(CHUNK_TIME)
            audio_data.seek(0)
            audio_chunk = audio_data.read()
            audio_data.seek(0)
            audio_data.truncate()
            call_api("AUDIO_CHUNK")
            wf = wave.open("audio_chunk_" + str(time.time()) + ".wav", 'wb')
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(audio_chunk)
            wf.close()
        else:
            continue

def wake_word_detection():
    global UNLOCKED
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
            if audio_stream is not None and not audio_stream.is_active():  # Check if the stream is still open
                break
            try:
                pcm = audio_stream.read(porcupine.frame_length)
            except OSError as e:
                if e.errno == -9981:
                    continue  # Ignore buffer overflow and continue
                else:
                    raise e  # Re-raise exception if it's not a buffer overflow
            pcm = struct.unpack_from("h" * porcupine.frame_length, pcm)
            keyword_index = porcupine.process(pcm)
            if keyword_index >= 0:
                print(f'Wake word detected: {"jarvis"}')
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
    # wait 3 seconds for threads to finish
    stream.stop_stream()
    stream.close()
    p.terminate()
