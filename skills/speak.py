import os
os.environ["COQUI_TOS_AGREED"] = "1"
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"  # hide GPU from PyTorch entirely, avoids CUDA conflict with Ollama

import time
from TTS.api import TTS
import sounddevice as sd
import soundfile as sf
from skills.interrupt import is_interrupted

SPEAKER = "Dionisio Schuyler"
LANGUAGE = "en"
TEMP_AUDIO_PATH = "jarvis_reply.wav"
OUTPUT_DEVICE = 4  # "Haut-parleurs (USB Audio Device" — your headset speaker, pinned explicitly
POST_PLAYBACK_BUFFER = 0.8  # extra safety pause in case driver reports "done" before audio physically finishes

print("Loading TTS voice model...")
_tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")
print("Voice model ready.")


def speak(text: str) -> None:
    """Generates speech for the given text using JARVIS's voice and plays it
    out loud. Blocks until playback finishes, plus a small safety buffer.
    Stops early if the global interrupt hotkey is pressed."""
    if not text or not text.strip():
        return

    start = time.time()
    _tts.tts_to_file(
        text=text,
        speaker=SPEAKER,
        language=LANGUAGE,
        file_path=TEMP_AUDIO_PATH
    )
    generation_time = time.time() - start
    print(f"[DEBUG] TTS generation took {generation_time:.2f}s for {len(text)} characters")

    data, samplerate = sf.read(TEMP_AUDIO_PATH)
    sd.play(data, samplerate, device=OUTPUT_DEVICE)

    # Poll instead of a single blocking sd.wait(), so we can stop early on interrupt
    while sd.get_stream().active:
        if is_interrupted():
            sd.stop()
            print("[INTERRUPT] Speech stopped.")
            return
        sd.sleep(50)

    time.sleep(POST_PLAYBACK_BUFFER)  # extra margin against driver/hardware buffering delay