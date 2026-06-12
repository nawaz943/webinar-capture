# 🎥 Webinar Capture & AI Analysis Pipeline

> A fully local, GPU-accelerated pipeline that records technical webinars, detects slide changes, transcribes the audio with AI, and generates professional PDF summaries — **without sending a single byte to the cloud.**

<p align="left">
  <img alt="Python" src="https://img.shields.io/badge/Python-3.9%2B-blue?logo=python&logoColor=white">
  <img alt="Platform" src="https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white">
  <img alt="GPU" src="https://img.shields.io/badge/GPU-NVIDIA%20CUDA-76B900?logo=nvidia&logoColor=white">
  <img alt="Whisper" src="https://img.shields.io/badge/STT-faster--whisper%20large--v3-orange">
  <img alt="LLM" src="https://img.shields.io/badge/LLM-Ollama%20%7C%20Llama%203-black">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-green">
</p>

---

## 📑 Table of Contents
- [Overview](#-overview)
- [Features](#-features)
- [How It Works](#-how-it-works)
- [Prerequisites](#-prerequisites)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Outputs](#-outputs)
- [Scripts Reference](#-scripts-reference)
- [Technical Notes](#-technical-notes)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🔭 Overview

This toolkit was built to automate the tedious process of attending, recording, and documenting online technical webinars (originally for **HVAC & Building Sciences** content). You launch a single orchestrator, play the webinar, and when it ends you get back:

- A clean **MP4 recording** (video + system audio).
- A **timestamped transcript** of everything that was said.
- A polished **AI-generated summary** in both `.txt` and `.pdf` form.
- **Slide screenshots**, captured automatically whenever the deck advances.

Everything runs on your own machine. The speech-to-text uses an NVIDIA GPU via `faster-whisper`, and the summarization uses a local LLM through **Ollama** — so no data ever leaves your computer.

---

## 🚀 Features

| Feature | Description |
|---|---|
| 🎬 **Live Recording** | High-performance screen capture (`mss`) and system audio recording (`pyaudio`) running on parallel threads. |
| 🖼️ **Smart Slide Detection** | Frame-differencing with OpenCV saves a screenshot **only** when the visible content changes past a threshold (i.e. a new slide). |
| ⚡ **GPU Transcription** | `faster-whisper` (`large-v3`) on CUDA with `float16` for fast, near-perfect speech-to-text. |
| 🧠 **Local AI Summaries** | Sends the cleaned transcript to **Ollama (Llama 3)** for a structured technical summary — fully offline. |
| 📄 **PDF Reporting** | Auto-generates a professionally formatted PDF (and TXT) summary via `fpdf2`. |
| 🔊 **Audio Diagnostics** | A built-in VU-meter utility helps you find the correct "Stereo Mix" capture device. |

---

## 🔄 How It Works

```
                ┌─────────────────────────────────────────────┐
                │              video-maker.py                  │
                │            (main orchestrator)               │
                │                                              │
   ┌────────────┼──────────────┬───────────────┬──────────────┼────────────┐
   ▼            ▼              ▼               ▼              ▼            
 Screen      System         Slide-change                                  
 capture     audio          detection                                     
 (video)     (WAV)          (PNG slides)                                  
   │            │                                                          
   └────┬───────┘   ◄── Press Ctrl+C to stop ──►                          
        │                                                                  
        ▼                                                                  
  ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
  │ aud-vid-merge │ ─►│  transcriber.py  │ ─►│  summarizer.py   │
  │  (FFmpeg mux) │   │ (faster-whisper) │   │ (Ollama / Llama) │
  └──────────────┘   └─────────────────┘   └──────────────────┘
        │                     │                      │
        ▼                     ▼                      ▼
  webinar_final.mp4   *_transcript.txt      *_summary.txt + .pdf
```

When you stop recording with `Ctrl+C`, the orchestrator automatically runs the three post-processing scripts in sequence: **merge → transcribe → summarize**.

---

## 🛠️ Prerequisites

### System Requirements
- **OS:** Windows (required for `pygetwindow` window-targeting and `mss`/Stereo-Mix audio capture).
- **GPU:** NVIDIA GPU with CUDA & cuDNN installed (the project was tuned on an **RTX A4000**).
- **FFmpeg:** Installed and available on your system `PATH`. ([Download](https://ffmpeg.org/))
- **Ollama:** Installed and running with a pulled model (default: `llama3`). ([Download](https://ollama.com/))

### Python
- Python **3.9+**

---

## 📦 Installation

```bash
# 1. Clone / copy this directory, then install Python dependencies
pip install mss opencv-python numpy faster-whisper fpdf2 pyaudio pygetwindow requests

# 2. Pull the local LLM (one-time)
ollama pull llama3

# 3. Confirm FFmpeg is on your PATH
ffmpeg -version
```

> 💡 **Tip:** `pyaudio` can be tricky to install on Windows. If `pip` fails, install a prebuilt wheel (e.g. via `pipwin install pyaudio`) or grab one matching your Python version.

---

## ⚙️ Configuration

All settings live at the top of [`video-maker.py`](video-maker.py).

**1. Find your audio device index**

Play any audio, then run the diagnostic tool:
```bash
python list-audio.py
```
Note the `[Index N]` of the device reporting `>>> SIGNAL DETECTED! <<<` (typically "Stereo Mix" or a WASAPI loopback device), and set:
```python
DEVICE_INDEX = 15   # ← your detected index
```

**2. Set the window to capture**

Update the title to match (part of) the browser tab or app window of your webinar:
```python
WEBINAR_WINDOW_TITLE = "Your Webinar Tab Title"
```

**3. (Optional) Tune capture behavior**

| Setting | Default | Purpose |
|---|---|---|
| `SCREENSHOT_THRESHOLD` | `5.0` | % visual change required to save a new slide. |
| `SLIDE_WIDTH_PERCENTAGE` | `0.5` | Left-side fraction of the window treated as the slide area. |
| `VIDEO_FPS` | `10` | Recording frame rate. |
| `RATE` / `CHANNELS` | `48000` / `2` | Audio sample rate and channel count. |

**4. (Optional) Change the summarization model**

In [`summarizer.py`](summarizer.py):
```python
MODEL_NAME = "llama3"   # or "mistral", "phi3", etc.
```

---

## 📖 Usage

### Full automated pipeline (recommended)

```bash
python video-maker.py
```
1. Wait for the `[!!!] START PLAYING THE WEBINAR NOW [!!!]` prompt, then start the webinar.
2. Recording runs until you press **`Ctrl+C`**.
3. On stop, the script automatically merges, transcribes, and summarizes.

### Run any stage standalone

Each script accepts arguments **or** falls back to sensible defaults inside `./webinar_output`:

```bash
# Merge an existing video + audio pair
python aud-vid-merge.py <video.mp4> <audio.wav> <output.mp4>

# Transcribe an audio file
python transcriber.py <audio.wav>

# Summarize a transcript
python summarizer.py <transcript.txt>
```

Running any of them with **no arguments** uses the default `webinar_*` files in `./webinar_output`.

---

## 📂 Outputs

All artifacts are written to **`./webinar_output/`**:

| File | Produced by | Description |
|---|---|---|
| `webinar_video.mp4` | `video-maker.py` | Raw silent screen capture. |
| `webinar_audio.wav` | `video-maker.py` | Raw system audio. |
| `slide_NNN.png` | `video-maker.py` | Auto-captured slide screenshots. |
| `webinar_final.mp4` | `aud-vid-merge.py` | Final merged video **with** audio. |
| `webinar_audio_transcript.txt` | `transcriber.py` | Timestamped transcript. |
| `webinar_audio_summary.txt` | `summarizer.py` | Plain-text AI summary. |
| `webinar_audio_summary.pdf` | `summarizer.py` | Formatted PDF summary. |

---

## 🗂️ Scripts Reference

| Script | Role |
|---|---|
| [`video-maker.py`](video-maker.py) | **Orchestrator.** Records video, audio, and slides on parallel threads, then chains the post-processing pipeline on stop. |
| [`transcriber.py`](transcriber.py) | Loads `faster-whisper large-v3` on CUDA and writes a timestamped transcript. |
| [`summarizer.py`](summarizer.py) | Strips timestamps, sends the text to Ollama, and exports TXT + PDF summaries. |
| [`aud-vid-merge.py`](aud-vid-merge.py) | Muxes the video and audio streams into a final MP4 via FFmpeg. |
| [`list-audio.py`](list-audio.py) | Diagnostic VU-meter to identify the correct audio input device index. |

---

## ⚠️ Technical Notes

- **CUDA DLL discovery:** `transcriber.py` and `video-maker.py` automatically scan your Python `site-packages` for `nvidia-cublas`, `nvidia-cudnn`, and `nvidia-cuda-runtime` DLLs and register them via `os.add_dll_directory()` — a common Windows fix for `faster-whisper` / `ctranslate2`.
- **Context window:** For very long webinars (transcripts over ~6,000 words), the summarizer warns that output may be truncated by the LLM's context limit.
- **PDF encoding:** Summaries are encoded as `latin-1` (with replacement) to stay compatible with `fpdf2`.
- **Threading:** Video, audio, and slide capture each run on their own thread for smooth concurrent recording.

---

## 🩺 Troubleshooting

| Symptom | Likely cause / fix |
|---|---|
| `Audio level very low` warnings | Webinar is muted, or `DEVICE_INDEX` is wrong — re-run `list-audio.py`. |
| Window not found | `WEBINAR_WINDOW_TITLE` doesn't match; use a unique substring of the real title. |
| `Could not load CUDA` / DLL errors | Ensure NVIDIA CUDA + cuDNN are installed and the `nvidia-*` pip packages are present. |
| `Error connecting to Ollama` | Ollama isn't running — start it and confirm `ollama run llama3` works. |
| `FFmpeg not found` | Install FFmpeg and ensure it's on your system `PATH`. |
| Slides not saving | Window may be minimized, or lower `SCREENSHOT_THRESHOLD`. |

---

## 📜 License

Released under the **MIT License** — free to use, modify, and distribute.

---

<sub>Developed as part of the **Weather Analysis** project suite.</sub>
