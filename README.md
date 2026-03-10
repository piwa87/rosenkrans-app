# Rosary Progress Tracker

A **hands-free** app for praying the Catholic Rosary.  
The app listens through the microphone, uses a local [Whisper](https://github.com/openai/whisper) model to transcribe speech, detects which prayer is being recited, and advances a bead counter — **no button presses, voice commands, or manual interaction required**.

---

## Features

| Feature | Detail |
|---------|--------|
| Hands-free | Purely voice-driven; no taps, clicks, or "next bead" commands |
| Offline STT | OpenAI Whisper runs locally — no internet connection needed |
| Smart detection | Anchor-phrase matching with cooldown/debounce (handles accents & pauses) |
| State machine | Tracks Our Father → 10 × Hail Mary → Glory Be across all 5 decades |
| Web UI | SVG rosary with the current bead highlighted, updating in real time |
| Languages | English and Danish, with a live language switch in the web UI |
| Console mode | Text logs showing transcript, detected prayer, decade, and bead index |

---

## Requirements

- Python 3.9 or newer  
- A working microphone  
- ~150 MB disk space for the Whisper `base` model (downloaded automatically on first run)

---

## Installation on macOS

This section walks through every step needed to get the app running on macOS from scratch.

### 1. Install Homebrew

[Homebrew](https://brew.sh) is the recommended package manager for macOS.  
Open **Terminal** and run:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen prompts. When it finishes, run the two `export` commands that the installer prints at the end (they add Homebrew to your `PATH`). Then verify:

```bash
brew --version
```

### 2. Install Python 3.9 or newer

macOS ships with an older Python 2.x (or 3.x on recent releases) that is not suitable for this app. Install a fresh Python via Homebrew:

```bash
brew install python@3.12
```

Verify the installation:

```bash
python3 --version   # should print Python 3.12.x (or the version you installed)
```

> **Tip:** If you already have Python 3.9+ installed and `python3 --version` confirms it, you can skip this step.

### 3. Install PortAudio

The `sounddevice` audio library requires the PortAudio C library:

```bash
brew install portaudio
```

### 4. Clone the repository

```bash
git clone https://github.com/piwa87/rosenkrans-app.git
cd rosenkrans-app
```

### 5. Create a Python virtual environment

Using a virtual environment keeps the project's dependencies isolated from the rest of your system:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Your prompt will change to show `(.venv)`. Every subsequent `python` / `pip` command will use this isolated environment.

### 6. Install Python dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

This installs `openai-whisper`, `numpy`, `flask`, and `sounddevice`.  
The Whisper `base` model (~150 MB) is downloaded automatically on the **first run** — not during installation.

### 7. Grant microphone access

macOS requires explicit permission before any app can use the microphone.

1. Go to **System Settings → Privacy & Security → Microphone**.
2. Ensure **Terminal** (or whichever terminal emulator you use, e.g. iTerm2) is toggled **on**.

If you skip this step the app will start but will capture only silence, and no prayers will be detected.

### 8. Run the app

Make sure the virtual environment is still active (you see `(.venv)` in your prompt), then run from the **repository root**:

**Console mode** — audio capture and detection with text output only:

```bash
python app/main.py
```

**Web UI mode** *(recommended)* — includes the live SVG rosary visualisation:

```bash
python app/main.py --ui
```

Then open **http://127.0.0.1:5000** in any browser.  
The rosary SVG updates in real time: the current bead glows gold and the decade indicators fill in as decades are completed.
Use the language selector in the page header to switch between English and Danish for both the UI and prayer detection.

Press **Ctrl-C** in the terminal to stop the app.

---

## Installation on Linux

```bash
# Debian / Ubuntu — install PortAudio
sudo apt-get install portaudio19-dev

# Then follow steps 4–8 above (clone → venv → pip install → run)
```

---

## Usage

### Console mode (audio + detection, no browser required)

```bash
python app/main.py
```

### With web UI *(recommended)*

```bash
python app/main.py --ui
```

Then open **http://127.0.0.1:5000** in a browser.  
The rosary SVG updates in real time: the current bead glows gold and the decade indicators fill in as decades are completed.
Use the language selector in the page header to switch languages while the app is running.

---

## How it works

```
Microphone audio
      │
      ▼  (5-second chunks)
 WhisperSTT.transcribe()          ← openai-whisper, offline
      │
      ▼ transcript text
 PrayerDetector.detect()          ← anchor-phrase matching + cooldown
      │
      ▼ PrayerType enum
 RosaryStateMachine.advance()     ← IDLE → OUR_FATHER → HAIL_MARY × 10 → GLORY_BE
      │
      ▼
 Console log + (optional) SSE → browser SVG update
```

---

## Prayer detection

The detector looks for **anchor phrases** — key words unique to each prayer — so exact recitation is not required:

| Prayer | Example anchors |
|--------|-----------------|
| Our Father | `"our father"`, `"thy will be done"`, `"daily bread"` / `"fader vor"`, `"ske din vilje"` |
| Hail Mary | `"hail mary"`, `"full of grace"`, `"blessed art thou among women"` / `"hil dig maria"`, `"fuld af nåde"` |
| Glory Be | `"glory be"`, `"world without end"`, `"as it was in the beginning"` / `"ære være faderen"`, `"som det var i begyndelsen"` |
| Fatima prayer | `"o my jesus"`, `"forgive us our sins"` / `"o min jesus"`, `"tilgiv os vore synder"` |

A **cooldown** (default 15 s) prevents the same prayer from being counted multiple times from consecutive audio chunks while you are still reciting it.

---

## State machine

```
IDLE
  │ Our Father
  ▼
OUR_FATHER  (decade N, bead 0)
  │ Hail Mary
  ▼
HAIL_MARY   (bead 1 … 10)
  │ Hail Mary (repeated up to 10 ×)
  ▼
HAIL_MARY   (bead 10)
  │ Glory Be
  ▼
GLORY_BE    (decade N complete)
  │ Our Father
  ▼
OUR_FATHER  (decade N+1, bead 0)
  ┆
  ▼  (after 5th Glory Be)
COMPLETE
```

---

## Configuration

Edit `app/main.py`:

| Variable | Default | Description |
|----------|---------|-------------|
| `CHUNK_SECONDS` | `5` | Duration of each audio chunk sent to Whisper |
| `model_name` | `"base"` | Whisper model size (`tiny` / `base` / `small` / `medium` / `large`) |
| `language` | `"en"` | Language code for speech recognition |

When the web UI is enabled, the page language selector updates this live between `"en"` and `"da"`.

Edit `app/detector.py`:

| Constant | Default | Description |
|----------|---------|-------------|
| `DETECTION_THRESHOLD` | `1` | Minimum anchor matches needed for detection |
| `DETECTION_COOLDOWN` | `15.0` | Seconds before re-detecting the same prayer |

---

## Running tests

```bash
pytest tests/
```

Tests cover the state machine and prayer detector and require **no microphone, no Whisper model, and no audio libraries**.

---

## Project structure

```
rosenkrans-app/
├── app/
│   ├── main.py           # Entry point: audio → STT → detection → state update
│   ├── stt_whisper.py    # Whisper STT wrapper (lazy model loading, silence skip)
│   ├── detector.py       # Anchor-phrase prayer detection with cooldown/debounce
│   ├── rosary_state.py   # Rosary state machine (5 decades)
│   └── ui/
│       ├── server.py         # Flask server (REST + SSE)
│       └── templates/
│           └── index.html    # SVG rosary visualisation
├── tests/
│   ├── conftest.py
│   ├── test_rosary_state.py
│   └── test_detector.py
├── requirements.txt
└── README.md
```

---

## Troubleshooting

**No audio detected**  
Ensure the microphone is connected, system permissions are granted, and the correct input device is the system default.

**macOS: Terminal does not appear in the Microphone list**  
Open **System Settings → Privacy & Security → Microphone** and check whether your terminal app is listed. If it is not listed at all, run the app once — macOS will prompt you for permission the first time an app requests microphone access.

**macOS: `brew: command not found` after installing Homebrew**  
The installer prints two `export` commands near the end of its output. Run those lines in your terminal (or add them to `~/.zprofile`) and then open a new terminal window.

**macOS: `ERROR: Could not build wheels for sounddevice` / PortAudio not found**  
Make sure PortAudio is installed before installing the Python dependencies:
```bash
brew install portaudio
pip install sounddevice
```

**macOS: `Illegal instruction: 4` or crash on Apple Silicon (M1/M2/M3)**  
The default `openai-whisper` package may install a CPU-only version of PyTorch that is not optimised for Apple Silicon. If you see this error, install the Apple Silicon build explicitly:
```bash
pip install torch torchvision torchaudio
```
Then re-install `openai-whisper` from requirements:
```bash
pip install -r requirements.txt
```

**Poor recognition / wrong prayers detected**  
Try a larger Whisper model:  `model_name="small"` in `app/main.py`.  
You can also raise `DETECTION_THRESHOLD` in `app/detector.py` to require more anchor matches before advancing.

**`pyaudio` preferred over `sounddevice`**  
Install it and the app will use it automatically:
```bash
pip install pyaudio
```
On macOS, PyAudio also requires PortAudio (`brew install portaudio`) before it can be pip-installed.

**Import errors when running `python app/main.py`**  
Always run from the **repository root**, not from inside `app/`.

---

## Licence

MIT
