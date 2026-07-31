import sounddevice as sd
import numpy as np
import time
from openwakeword.model import Model

CHUNK_SIZE = 1280
SAMPLE_RATE = 16000
COOLDOWN_SECONDS = 2.0
DETECTION_THRESHOLD = 0.5
CONSECUTIVE_CHUNKS_REQUIRED = 2
INPUT_DEVICE = 1
HARD_MUTE_SECONDS = 3.0  # completely ignore all audio for this long after stream opens

_model = Model(wakeword_models=["hey_jarvis"])
_last_trigger_time = 0
_wake_detected = False
_consecutive_high_chunks = 0
_stream_start_time = 0


def _audio_callback(indata, frames, time_info, status):
    global _last_trigger_time, _wake_detected, _consecutive_high_chunks

    elapsed_since_start = time.time() - _stream_start_time

    if elapsed_since_start < HARD_MUTE_SECONDS:
        return  # completely skip processing, no scoring at all during mute window

    audio_chunk = indata[:, 0]
    prediction = _model.predict(audio_chunk)
    score = prediction["hey_jarvis"]

    if score > 0.3:
        print(f"[DEBUG] wake score: {score:.2f} (elapsed: {elapsed_since_start:.1f}s)")

    if score > DETECTION_THRESHOLD:
        _consecutive_high_chunks += 1
    else:
        _consecutive_high_chunks = 0

    now = time.time()
    if _consecutive_high_chunks >= CONSECUTIVE_CHUNKS_REQUIRED and (now - _last_trigger_time) > COOLDOWN_SECONDS:
        _wake_detected = True
        _last_trigger_time = now
        _consecutive_high_chunks = 0


def wait_for_wake_word():
    """Blocks until 'Hey Jarvis' is detected. Ignores all audio for the first
    HARD_MUTE_SECONDS after starting, to avoid self-triggering on residual
    speaker/mic leakage from JARVIS's own previous reply."""
    global _wake_detected, _consecutive_high_chunks, _stream_start_time
    _wake_detected = False
    _consecutive_high_chunks = 0
    _stream_start_time = time.time()

    print(f"Listening for 'Hey Jarvis'... (muted for first {HARD_MUTE_SECONDS}s)")

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SIZE,
        device=INPUT_DEVICE,
        callback=_audio_callback
    ):
        while not _wake_detected:
            sd.sleep(100)

    print("Wake word detected!")