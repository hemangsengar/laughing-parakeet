"""
Stage 1 — Vocal / Source Isolation using Demucs.

Separates vocals from background music/ambient noise.
"""

import logging
import shutil
from pathlib import Path

from demucs.api import Separator

from app.config import DEMUCS_MODEL

logger = logging.getLogger(__name__)


def isolate_vocals(input_path: Path, work_dir: Path) -> Path:
    """
    Run Demucs to isolate vocals from the input audio.

    Args:
        input_path:  Path to the raw input audio file.
        work_dir:    Temporary working directory for this request.

    Returns:
        Path to the isolated vocals WAV file.
    """
    logger.info("Stage 1 — Isolating vocals with Demucs (%s)", DEMUCS_MODEL)

    separator = Separator(model=DEMUCS_MODEL, segment=None, jobs=0)
    _, separated = separator.separate_audio_file(input_path)

    # Save the vocals stem to the work directory
    vocals_path = work_dir / "vocals.wav"

    import torchaudio

    vocals_tensor = separated["vocals"]
    # Demucs returns tensors at the model's sample rate (44100 by default)
    torchaudio.save(str(vocals_path), vocals_tensor.cpu(), separator.samplerate)

    logger.info("Stage 1 complete → %s", vocals_path)
    return vocals_path
