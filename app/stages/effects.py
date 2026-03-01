"""
Stage 5 — Studio Effects using ffmpeg audio filters.

Applies optional post-processing effects:
  - Wind removal (high-pass filter)
  - 3-band parametric EQ
  - Compression
  - Reverb (echo-based)
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def apply_effects(
    input_path: Path,
    work_dir: Path,
    *,
    wind_removal: dict | None = None,
    eq: dict | None = None,
    compressor: dict | None = None,
    reverb: dict | None = None,
) -> Path:
    """
    Apply studio effects via ffmpeg audio filters.

    All parameters are optional — only enabled effects are applied.
    If no effects are enabled, the input is returned unchanged.

    Args:
        input_path:    Path to the input WAV.
        work_dir:      Temporary working directory.
        wind_removal:  {"enabled": bool, "cutoff": int (Hz)}
        eq:            {"enabled": bool, "low": float dB, "mid": float dB, "high": float dB}
        compressor:    {"enabled": bool, "threshold": float dB, "ratio": float,
                        "attack": float ms, "release": float ms}
        reverb:        {"enabled": bool, "room": float 0-1, "wet": float 0-1}

    Returns:
        Path to the processed WAV (or input_path if no effects applied).
    """
    filters = []

    # Wind removal — high-pass filter
    if wind_removal and wind_removal.get("enabled"):
        cutoff = int(wind_removal.get("cutoff", 80))
        cutoff = max(20, min(cutoff, 500))  # Clamp
        filters.append(f"highpass=f={cutoff}:poles=2")
        logger.info("Effect: wind removal (highpass %d Hz)", cutoff)

    # 3-band EQ
    if eq and eq.get("enabled"):
        low = float(eq.get("low", 0))
        mid = float(eq.get("mid", 0))
        high = float(eq.get("high", 0))
        low = max(-12, min(12, low))
        mid = max(-12, min(12, mid))
        high = max(-12, min(12, high))
        if low != 0:
            filters.append(f"equalizer=f=200:t=h:w=200:g={low}")
        if mid != 0:
            filters.append(f"equalizer=f=1000:t=h:w=800:g={mid}")
        if high != 0:
            filters.append(f"equalizer=f=4000:t=h:w=2000:g={high}")
        logger.info("Effect: EQ (low=%.1f, mid=%.1f, high=%.1f dB)", low, mid, high)

    # Compressor
    if compressor and compressor.get("enabled"):
        threshold = float(compressor.get("threshold", -20))
        ratio = float(compressor.get("ratio", 4))
        attack = float(compressor.get("attack", 5))
        release = float(compressor.get("release", 50))
        threshold = max(-60, min(0, threshold))
        ratio = max(1, min(20, ratio))
        attack = max(0.1, min(100, attack))
        release = max(5, min(2000, release))
        filters.append(
            f"acompressor=threshold={threshold}dB:ratio={ratio}:attack={attack}:release={release}"
        )
        logger.info(
            "Effect: compressor (thresh=%.1fdB, ratio=%.1f, atk=%.1fms, rel=%.1fms)",
            threshold, ratio, attack, release,
        )

    # Reverb (using aecho)
    if reverb and reverb.get("enabled"):
        room = float(reverb.get("room", 0.3))
        wet = float(reverb.get("wet", 0.2))
        room = max(0.05, min(1.0, room))
        wet = max(0.0, min(0.8, wet))
        # aecho: in_gain|out_gain|delays|decays
        delay_ms = int(room * 80)  # 4-80ms
        decay = round(wet * 0.6, 2)  # 0-0.48
        in_gain = round(1.0 - wet * 0.3, 2)
        out_gain = round(0.9 + wet * 0.1, 2)
        filters.append(f"aecho={in_gain}:{out_gain}:{delay_ms}:{decay}")
        logger.info("Effect: reverb (room=%.2f, wet=%.2f)", room, wet)

    # If no effects, return input unchanged
    if not filters:
        logger.info("Stage 5 — No effects enabled, skipping")
        return input_path

    logger.info("Stage 5 — Applying %d effect(s)", len(filters))

    output_path = work_dir / "effects_output.wav"
    filter_chain = ",".join(filters)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-af", filter_chain,
        "-acodec", "pcm_s24le",
        str(output_path),
    ]

    logger.debug("Running: %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.error("ffmpeg effects failed:\n%s", result.stderr)
        raise RuntimeError(f"Effects processing failed (exit {result.returncode})")

    logger.info("Stage 5 complete → %s", output_path)
    return output_path
