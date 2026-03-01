"""
Stage 2 — Denoise + AI Enhancement using Resemble Enhance.

Runs a UNet denoiser followed by a generative enhancer to restore
lost frequencies and bandwidth.
"""

import logging
from functools import partial
from pathlib import Path

import numpy as np
import scipy.optimize
import soundfile as sf
import torch

from app.config import ENHANCE_LAMBD, ENHANCE_NFE, ENHANCE_TAU

logger = logging.getLogger(__name__)


def _patch_resemble_enhance():
    """
    Monkey-patch the scipy.optimize.fsolve bug in resemble_enhance.

    Newer numpy/scipy returns an ndarray from fsolve, but the library
    tries to call float() on it directly which fails.  We replace the
    broken static method with a fixed version.
    """
    try:
        from resemble_enhance.enhancer.lcfm.cfm import Solver

        @staticmethod
        def _fixed_mapping(t, n=4):
            def h(t, a):
                return (a**t - 1) / (a - 1)

            a = float(scipy.optimize.fsolve(lambda a: h(1 / n, a) - 0.5, x0=0)[0])
            t = h(t, a=a)
            return t

        Solver.exponential_decay_mapping = _fixed_mapping
        logger.debug("Patched Resemble Enhance cfm.Solver.exponential_decay_mapping")
    except Exception as e:
        logger.warning("Could not patch resemble_enhance: %s", e)


_patch_resemble_enhance()


def _get_device() -> str:
    """Auto-detect best available device.
    Note: MPS (Apple Silicon) is not used because Resemble Enhance
    has compatibility issues with MPS tensors. Falls back to CPU.
    """
    if torch.cuda.is_available():
        return "cuda"
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

    data, sr = sf.read(str(input_path), dtype="float32")
    wav = torch.from_numpy(data)

    # soundfile returns (samples,) for mono or (samples, channels) for stereo
    if wav.ndim == 2:
        # Resemble Enhance requires 1D mono input — average channels
        wav_mono = wav.mean(dim=1)
    else:
        wav_mono = wav

    # Resemble Enhance expects a 1D tensor (mono waveform)
    enhanced_wav, new_sr = enhance(
        wav_mono.to(device),
        sr,
        device=device,
        nfe=ENHANCE_NFE,
        solver="midpoint",
        lambd=ENHANCE_LAMBD,
        tau=ENHANCE_TAU,
    )

    # enhanced_wav may be 1D — ensure it's (samples,) for soundfile
    out = enhanced_wav.cpu().numpy()
    if out.ndim > 1:
        out = out.squeeze()

    output_path = work_dir / "enhanced.wav"
    sf.write(str(output_path), out, new_sr)

    logger.info("Stage 2 complete → %s", output_path)
    return output_path
