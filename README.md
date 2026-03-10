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
| Console mode | Text logs showing transcript, detected prayer, decade, and bead index |

---

## Requirements

- Python 3.9 or newer  
- A working microphone  
- ~150 MB disk space for the Whisper `base` model (downloaded automatically on first run)

### System libraries (Linux / macOS)

`sounddevice` requires PortAudio:

```bash
# Debian / Ubuntu
sudo apt-get install portaudio19-dev

# macOS (Homebrew)
brew install portaudio
```

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/piwa87/rosenkrans-app.git
cd rosenkrans-app

# 2. (Optional) create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
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
| Our Father | `"our father"`, `"thy will be done"`, `"daily bread"` |
| Hail Mary | `"hail mary"`, `"full of grace"`, `"blessed art thou among women"` |
| Glory Be | `"glory be"`, `"world without end"`, `"as it was in the beginning"` |
| Fatima prayer | `"o my jesus"`, `"forgive us our sins"` |

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

**Poor recognition / wrong prayers detected**  
Try a larger Whisper model:  `model_name="small"` in `app/main.py`.  
You can also raise `DETECTION_THRESHOLD` in `app/detector.py` to require more anchor matches before advancing.

**`pyaudio` preferred over `sounddevice`**  
Install it and the app will use it automatically:
```bash
pip install pyaudio
```

**Import errors when running `python app/main.py`**  
Always run from the **repository root**, not from inside `app/`.

---

## Licence

MIT
