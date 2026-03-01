"""
Stage 2 — Denoise + AI Enhancement using Resemble Enhance.

Runs a UNet denoiser followed by a generative enhancer to restore
lost frequencies and bandwidth.
"""

import logging
from pathlib import Path

import torch
import torchaudio

from app.config import ENHANCE_LAMBD, ENHANCE_NFE, ENHANCE_TAU

logger = logging.getLogger(__name__)


def _get_device() -> str:
    """Auto-detect best available device."""
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def enhance_audio(input_path: Path, work_dir: Path) -> Path:
    """
    Denoise and enhance the audio using Resemble Enhance.

    Args:
        input_path:  Path to the isolated vocals WAV.
        work_dir:    Temporary working directory for this request.

    Returns:
        Path to the enhanced WAV file.
    """
    device = _get_device()
    logger.info("Stage 2 — Enhancing audio (device=%s, nfe=%d)", device, ENHANCE_NFE)

    from resemble_enhance.enhancer.inference import enhance

    wav, sr = torchaudio.load(str(input_path))

    # Resemble Enhance expects mono or will handle multi-channel internally
    enhanced_wav, new_sr = enhance(
        wav.to(device),
        sr,
        device=device,
        nfe=ENHANCE_NFE,
        solver="midpoint",
        lambd=ENHANCE_LAMBD,
        tau=ENHANCE_TAU,
    )

    output_path = work_dir / "enhanced.wav"
    torchaudio.save(str(output_path), enhanced_wav.cpu(), new_sr)

    logger.info("Stage 2 complete → %s", output_path)
    return output_path
