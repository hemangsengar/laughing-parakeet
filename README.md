# Audio Optimizer Studio

**Audio Optimizer Studio** is a fully automated, AI-powered "One-Click Magic" platform for enhancing audio recordings. It wraps state-of-the-art machine learning models (Demucs, Resemble Enhance) in a production-grade FastAPI + React application, enabling anyone to achieve studio-quality audio without needing to understand developer settings or complex audio engineering.

![Audio Optimizer Interface](./frontend/public/vite.svg)

## How It Works

The platform uses a fully automated 4-stage pipeline that runs blindly on the backend:

1. **Vocal Isolation**: Uses [Meta's Demucs](https://github.com/facebookresearch/demucs) to extract raw voices from background music and noise.
2. **AI Denoising**: Uses [Resemble Enhance's UNet](https://github.com/resemble-ai/resemble-enhance) to clean microphone hiss, echo, and residual artifacting.
3. **Reference Mastering** (Optional): Uses [Matchering](https://github.com/sergree/matchering) to match the EQ and frequency response of your audio to a professional reference track.
4. **Loudness Normalization**: Uses `ffmpeg loudnorm` to automatically hit the industry standard **-14 LUFS** (YouTube/Spotify standard) for the final export.

## Quick Start

### Prerequisites
You must have `ffmpeg` installed on your system.
```bash
# On macOS
brew install ffmpeg

# On Ubuntu
sudo apt install ffmpeg
```

### Installation & Running
We have completely automated the environment setup via `start.sh`.

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/audio-optimizer.git
cd audio-optimizer

# 2. Run the magic start script
./start.sh
```

**What `start.sh` does:**
- Automatically creates a Python `.venv`
- Installs all heavy Machine Learning dependencies (PyTorch, Demucs, etc.)
- Installs Node dependencies and builds the Vite/React frontend to static files.
- Starts the FastAPI server.

Once `start.sh` finishes, simply open your browser to **http://localhost:8000** and drop your audio file in to experience the magic!

## Tech Stack
- **Backend**: Python 3.12, FastAPI, Uvicorn, PyTorch
- **Frontend**: React 18, Vite, Lucide Icons, Vanilla CSS (Dark Studio Theme)
- **Audio Processing**: ffmpeg, soundfile, librosa
