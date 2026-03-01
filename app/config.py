"""
Central configuration for the audio optimizer pipeline.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
TEMP_DIR = BASE_DIR / "tmp_processing"
REFERENCES_DIR = BASE_DIR / "references"

# Ensure directories exist at import time
TEMP_DIR.mkdir(exist_ok=True)
REFERENCES_DIR.mkdir(exist_ok=True)

# ---------------------------------------------------------------------------
# Platform LUFS targets
# ---------------------------------------------------------------------------
PLATFORM_TARGETS: dict[str, dict] = {
    "youtube":   {"lufs": -14, "tp": -1, "lra": 11},
    "podcast":   {"lufs": -16, "tp": -1, "lra": 11},
    "broadcast": {"lufs": -23, "tp": -1, "lra": 11},
    "reels":     {"lufs": -14, "tp": -1, "lra": 11},
}

VALID_PLATFORMS = list(PLATFORM_TARGETS.keys())

# ---------------------------------------------------------------------------
# Resemble Enhance defaults
# ---------------------------------------------------------------------------
ENHANCE_NFE = 32       # number of function evaluations (lower = faster + more conservative)
ENHANCE_LAMBD = 0.9    # denoiser ↔ enhancer crossfade (1.0 = pure denoiser, 0.0 = pure enhancer)
ENHANCE_TAU = 0.3      # prior temperature (lower = more conservative, less frequency synthesis)

# ---------------------------------------------------------------------------
# Demucs model
# ---------------------------------------------------------------------------
DEMUCS_MODEL = "htdemucs"

# ---------------------------------------------------------------------------
# Supported upload extensions
# ---------------------------------------------------------------------------
SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma"}
