"""
Stage 4 — LUFS Normalization using ffmpeg loudnorm.

Hits the exact LUFS / true-peak target for the chosen platform.
"""

import logging
import subprocess
from pathlib import Path

from app.config import PLATFORM_TARGETS

logger = logging.getLogger(__name__)


def normalize_loudness(
    input_path: Path,
    work_dir: Path,
    platform: str,
    custom_lufs: int | float | None = None,
) -> Path:
    """
    Normalize audio loudness to the platform's LUFS target using ffmpeg.

    Uses a two-pass loudnorm approach for accurate normalization.

    Args:
        input_path:   Path to the mastered (or enhanced) WAV.
        work_dir:     Temporary working directory.
        platform:     One of the keys in PLATFORM_TARGETS.
        custom_lufs:  Optional custom LUFS target (overrides platform default).

    Returns:
        Path to the final normalized 24-bit WAV.
    """
    target = PLATFORM_TARGETS[platform]
    lufs = int(custom_lufs) if custom_lufs is not None else target["lufs"]
    lufs = max(-60, min(-3, lufs))  # Clamp to safe range
    tp = target["tp"]
    lra = target["lra"]

    logger.info(
        "Stage 4 — Normalizing to %s dB LUFS (TP=%s, LRA=%s) for '%s'",
        lufs, tp, lra, platform,
    )

    output_path = work_dir / "output_final.wav"

    # Single-pass loudnorm (linear normalization)
    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af", f"loudnorm=I={lufs}:TP={tp}:LRA={lra}",
        "-ar", "48000",
        "-acodec", "pcm_s24le",   # 24-bit output
        str(output_path),
    ]

    logger.debug("Running: %s", " ".join(cmd))

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        logger.error("ffmpeg stderr:\n%s", result.stderr)
        raise RuntimeError(f"ffmpeg loudnorm failed (exit {result.returncode})")

    logger.info("Stage 4 complete → %s", output_path)
    return output_path
