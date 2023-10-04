import pyaudio
import threading
import time
import wave
# You might need to import more modules based on your "call API" function and Porcupine specifics.

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"
import pvporcupine
import struct

from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Get access key from environment variable
access_key = os.getenv('PV_ACCESS_KEY')

audio_buffer = []

def save_audio_chunk_to_wav(data):
    with wave.open(WAVE_OUTPUT_FILENAME, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(data))

def thread1_func():
    global audio_buffer
    while True:
        time.sleep(RECORD_SECONDS)
        save_audio_chunk_to_wav(audio_buffer[-(RATE * RECORD_SECONDS // CHUNK):])
        # Call your API here
        call_api()


porcupine_buffer = []
CHUNK = 512  # This aligns with Porcupine's frame length expectation.


def thread2_func():
    porcupine = None
    try:
        porcupine = pvporcupine.create(keywords=["jarvis"], access_key=access_key)

        while True:
            if not porcupine_buffer:
                time.sleep(0.05)  # Avoid busy-waiting when there's no data
                continue

            pcm_data = porcupine_buffer.pop(0)
            
            # Assuming CHUNK = 1024
            pcm = struct.unpack_from("h" * 512, pcm_data)  # Unpacking 1024 bytes into 512 short integers

            keyword_index = porcupine.process(pcm)
                
            if keyword_index >= 0:
                print("Wake word detected!")
                # Capture additional audio or process the command

    except Exception as e:
        print(f"Error in Porcupine processing: {e}")
    finally:
        if porcupine is not None:
            porcupine.delete()

def callback(in_data, frame_count, time_info, status):
    global audio_buffer, porcupine_buffer
    audio_buffer.append(in_data)
    porcupine_buffer.append(in_data)
    return (in_data, pyaudio.paContinue)


def call_api():
    # Your logic to call the API here
    pass

def call_api_with_command(command):
    # Your logic to call the API with the specific command here
    pass

p = pyaudio.PyAudio()
device_index = p.get_default_input_device_info()["index"]
stream = p.open(format=FORMAT,
               channels=CHANNELS,
               rate=RATE,
               input=True,
               frames_per_buffer=CHUNK,
               input_device_index=device_index,
               stream_callback=callback)

stream.start_stream()

try:
    thread1 = None
    # thread1 = threading.Thread(target=thread1_func)
    # thread1.start()

    thread2 = None
    thread2 = threading.Thread(target=thread2_func)
    thread2.start()

    while stream.is_active():
        time.sleep(0.1)  # To prevent 100% CPU usage

except KeyboardInterrupt:
    stream.stop_stream()
    stream.close()
    p.terminate()
    thread1.join()
    thread2.join()
