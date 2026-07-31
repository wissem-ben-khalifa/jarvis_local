import sounddevice as sd
import numpy as np
import time
from openwakeword.model import Model

CHUNK_SIZE = 1280
SAMPLE_RATE = 16000
COOLDOWN_SECONDS = 2.0  # ignore repeat detections within this window

model = Model(wakeword_models=["hey_jarvis"])

last_trigger_time = 0

print("Listening for 'Hey Jarvis'... (Ctrl+C to stop)")

def audio_callback(indata, frames, time_info, status):
    global last_trigger_time

    audio_chunk = indata[:, 0]
    prediction = model.predict(audio_chunk)
    score = prediction["hey_jarvis"]

    now = time.time()
    if score > 0.5 and (now - last_trigger_time) > COOLDOWN_SECONDS:
        print(f"Wake word detected! (confidence: {score:.2f})")
        last_trigger_time = now

try:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SIZE,
        callback=audio_callback
    ):
        while True:
            sd.sleep(100)
except KeyboardInterrupt:
    print("\nStopped listening.")