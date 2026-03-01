"""
Stage 1 — Vocal / Source Isolation using Demucs.

Separates vocals from background music/ambient noise.
"""

import logging
from pathlib import Path

import soundfile as sf
import torch
from demucs.apply import apply_model
from demucs.pretrained import get_model

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

    # Load the pre-trained model
    model = get_model(DEMUCS_MODEL)
    model.eval()

    # Load audio via soundfile (avoids torchcodec dependency)
    data, sr = sf.read(str(input_path), dtype="float32")
    wav = torch.from_numpy(data)
    # soundfile returns (samples,) for mono or (samples, channels) for stereo
    if wav.ndim == 1:
        wav = wav.unsqueeze(0)  # (1, samples) = mono
    else:
        wav = wav.T  # (channels, samples)
    if sr != model.samplerate:
        import torchaudio
        wav = torchaudio.functional.resample(wav, sr, model.samplerate)

    # Demucs expects (batch, channels, samples)
    wav = wav.unsqueeze(0)

    # If mono, duplicate to stereo (Demucs expects 2 channels)
    if wav.shape[1] == 1:
        wav = wav.repeat(1, 2, 1)

    # Run separation
    with torch.no_grad():
        sources = apply_model(model, wav, device="cpu", split=True)

    # sources shape: (batch, n_sources, channels, samples)
    # Find the vocals index from model.sources
    vocals_idx = model.sources.index("vocals")
    vocals_tensor = sources[0, vocals_idx]  # (channels, samples)

    # Save the vocals stem
    vocals_path = work_dir / "vocals.wav"
    sf.write(str(vocals_path), vocals_tensor.cpu().numpy().T, model.samplerate)

    logger.info("Stage 1 complete → %s", vocals_path)
    return vocals_path
