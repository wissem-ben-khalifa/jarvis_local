# JARVIS-Local

A local, voice-controlled AI desktop assistant for Windows. It listens for a wake word, understands natural language commands, executes real actions on your PC, and replies with dynamically LLM-generated speech in a custom voice — all running fully offline via [Ollama](https://ollama.com), with no cloud APIs required.

Built as a portfolio project to demonstrate agentic AI with tool use, real-time audio pipelines, and safety engineering — deliberately scoped around a fixed set of reliable skills rather than "do anything," so every capability is tested and defensible.

## Features

- **Wake word activation** — say "Hey Jarvis" to start a conversation, with a short follow-up window so you don't have to repeat the trigger for every command
- **Voice in, voice out** — local speech-to-text (faster-whisper) and text-to-speech (Coqui XTTS v2) with a custom voice
- **6 local skills**, routed by an LLM (not hardcoded keywords):
  - Take a screenshot
  - Open an app or website
  - Send a Discord message (via UI automation, with spoken confirmation before sending)
  - Web search + spoken summary
  - Vision — describes or reads what's on your screen using a local multimodal model (`llava`)
  - Long-term memory — remembers facts across sessions using ChromaDB, recalled automatically when relevant
- **Multi-action chaining** — a single request can trigger several skills in sequence ("open YouTube and take a screenshot"), capped at 5 actions per request as a safety limit
- **Safety features** — spoken confirmation before irreversible actions (like sending a message), a global hotkey (`Ctrl+Shift+X`) to interrupt speech/listening instantly
- **Full desktop dashboard app** — a custom UI (PySide6 + embedded web view) with a live system-state panel, activity log, animated central orb that reacts to state, and working Skills/Memory/Settings tabs
- **Ambient floating orb** — when the dashboard isn't open, a small always-on-top orb sits in the corner of your screen and animates differently depending on whether JARVIS is idle, listening, or speaking
- **Animated boot sequence** — a synthesized startup chime and loading animation on launch

## Tech Stack

| Component | Tool |
|---|---|
| LLM / routing / vision | Ollama (`llama3.1:8b`, `llava`, `nomic-embed-text`) |
| Wake word | openWakeWord |
| Speech-to-text | faster-whisper |
| Text-to-speech | Coqui TTS (XTTS v2) |
| Memory | ChromaDB |
| Desktop UI | PySide6 + QWebEngineView (HTML/CSS/JS dashboard) |
| App/browser control | `subprocess`, `pyautogui`, `webbrowser` |
| Packaging | PyInstaller |

## Known Limitations

- **Wake word self-triggering**: the wake word system can occasionally trigger on JARVIS's own speech output being picked up by the microphone (acoustic feedback). Partial mitigations are implemented (consecutive-chunk validation, a hard mute window with model warm-up buffering to avoid state discontinuity artifacts), which meaningfully reduce but don't fully eliminate this. A complete fix would require dedicated acoustic echo cancellation (AEC), typically implemented via specialized multi-mic hardware in production voice assistants — out of scope for this project.
- Requires [Ollama](https://ollama.com) installed and running locally, with the models above pulled.
- Discord messaging works via UI automation (simulating keystrokes into the real Discord app), not the Discord API — it's a deliberate design choice so messages appear as genuinely sent by the user, but it's inherently more fragile than an API-based integration if Discord's UI layout changes.

## Setup

1. Install [Ollama](https://ollama.com) and pull the required models:
   ```
   ollama pull llama3.1:8b
   ollama pull llava
   ollama pull nomic-embed-text
   ```
2. Clone this repo and create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run it:
   ```
   python run_app.py
   ```

## Building a standalone .exe

```
pip install pyinstaller
pyinstaller jarvis.spec
```
The packaged app will be in `dist/JARVIS/`. Note that Ollama and its models are a separate dependency — they aren't bundled into the executable and must be installed independently on any machine running the packaged app.

## Project Structure

```
jarvis-local/
  main.py              # Voice loop, routing orchestration
  run_app.py            # Desktop app entry point (UI + voice loop together)
  router.py             # LLM-based action routing
  resource_path.py       # Path resolution for source vs packaged builds
  skills/                # One file per capability
  ui/                     # Dashboard HTML/CSS/JS, floating orb, splash screen
  memory_db/              # ChromaDB storage (gitignored, created at runtime)
```

## Safety & Privacy

Everything runs locally — no audio, screenshots, or messages are sent to any cloud service. The only network calls this project makes are for web search results and one-time model downloads.