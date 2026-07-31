import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280          # 80ms chunks
SILENCE_THRESHOLD = 300    # RMS amplitude below this = silence (tune if needed)
SILENCE_DURATION = 1.5     # stop after this many seconds of continuous silence
MAX_RECORD_SECONDS = 15    # hard safety cap so it never listens forever
INPUT_DEVICE = 1  # "Microphone (USB Audio Device)" — your headset mic, pinned explicitly

print("Loading speech-to-text model...")
_model = WhisperModel("base.en", device="cpu", compute_type="int8")
print("Speech-to-text model ready.")


def _rms(chunk: np.ndarray) -> float:
    """Root-mean-square amplitude of an audio chunk, used to detect silence vs speech."""
    return np.sqrt(np.mean(chunk.astype(np.float32) ** 2))


def listen() -> str:
    """Records audio until the user stops talking (silence-based), then
    transcribes it using Whisper. Returns the transcribed text (may be empty)."""

    print("Listening... (speak now, will stop automatically after you pause)")

    recorded_chunks = []
    silent_chunks_in_a_row = 0
    silence_chunks_needed = int(SILENCE_DURATION * SAMPLE_RATE / CHUNK_SIZE)
    max_chunks = int(MAX_RECORD_SECONDS * SAMPLE_RATE / CHUNK_SIZE)
    started_talking = False

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16", blocksize=CHUNK_SIZE, device=INPUT_DEVICE) as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(CHUNK_SIZE)
            chunk = chunk[:, 0]
            recorded_chunks.append(chunk)

            level = _rms(chunk)

            if level > SILENCE_THRESHOLD:
                started_talking = True
                silent_chunks_in_a_row = 0
            else:
                silent_chunks_in_a_row += 1

            # Only stop on silence AFTER the person has actually started talking
            if started_talking and silent_chunks_in_a_row >= silence_chunks_needed:
                break

    print("Done recording. Transcribing...")

    if not recorded_chunks:
        return ""

    audio_flat = np.concatenate(recorded_chunks).astype(np.float32) / 32768.0  # normalize int16 -> float32

    segments, _ = _model.transcribe(audio_flat, language="en")
    text = " ".join(segment.text.strip() for segment in segments)

    return text.strip()