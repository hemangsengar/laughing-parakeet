"""
Stage 2 — Denoise audio using Resemble Enhance's UNet denoiser.

Runs ONLY the denoiser (not the generative enhancer) to clean noise
while preserving the natural voice frequencies.
"""

import logging
from pathlib import Path

import soundfile as sf
import torch

logger = logging.getLogger(__name__)


def _get_device() -> str:
    """Auto-detect best available device (CPU or CUDA, skips MPS)."""
    if torch.cuda.is_available():
        return "cuda"
    return "cpu"


def enhance_audio(input_path: Path, work_dir: Path) -> Path:
    """
    Denoise the audio using Resemble Enhance's UNet denoiser.

    Uses the denoise() function directly — no generative enhancer,
    no frequency synthesis, no distortion. Just noise removal.

    Args:
        input_path:  Path to the isolated vocals WAV.
        work_dir:    Temporary working directory for this request.

    Returns:
        Path to the denoised WAV file.
    """
    device = _get_device()
    logger.info("Stage 2 — Denoising audio (device=%s, denoiser-only mode)", device)

    from resemble_enhance.enhancer.inference import denoise

    data, sr = sf.read(str(input_path), dtype="float32")
    wav = torch.from_numpy(data)

    # Resemble Enhance denoiser expects exactly a 1D tensor (frames,)
    if wav.ndim == 2:
        # sf.read returns (frames, channels), so we mean over dim 1
        wav = wav.mean(dim=1)

    # Run denoiser only — no generative model, no distortion
    denoised_wav, new_sr = denoise(
        wav.to(device),
        sr,
        device=device,
    )

    # Output is 1D (frames), convert to numpy directly for soundfile (it accepts 1D for mono)
    out = denoised_wav.cpu().numpy()
    
    output_path = work_dir / "enhanced.wav"
    sf.write(str(output_path), out, new_sr)

    logger.info("Stage 2 complete → %s", output_path)
    return output_path

