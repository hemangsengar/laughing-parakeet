#!/usr/bin/env bash
# ──────────────────────────────────────────────
#  Audio Optimizer — One-click setup & start
# ──────────────────────────────────────────────
set -e

cd "$(dirname "$0")"

echo "🎧 Audio Optimizer — Setup & Start"
echo "──────────────────────────────────"

# 1. Check for ffmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg is not installed."
    echo "   Install it with: brew install ffmpeg"
    exit 1
fi
echo "✅ ffmpeg found"

# 2. Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# 3. Activate venv
source .venv/bin/activate
echo "✅ Virtual environment activated"

# 4. Install/update dependencies
echo "📦 Installing dependencies (first run may take a few minutes)..."
if command -v uv &> /dev/null; then
    uv pip install -r requirements.txt --prerelease=allow -q
else
    pip install -r requirements.txt -q
fi
echo "✅ Dependencies installed"

# 5. Build frontend if present
if [ -d "frontend" ]; then
    echo "🏗️  Building React frontend..."
    cd frontend
    npm install --silent
    npm run build --silent
    cd ..
    echo "✅ Frontend built to static/"
fi

# 6. Start the server
echo ""
echo "🚀 Starting Audio Optimizer on http://localhost:8000"
echo "   Open that URL in your browser to use the UI."
echo "   API docs available at http://localhost:8000/docs"
echo "   Press Ctrl+C to stop."
echo ""

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
