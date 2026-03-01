"""
Pipeline orchestrator — runs stages sequentially with optional toggles.
"""

import logging
import shutil
import subprocess
import uuid
from pathlib import Path

from app.config import TEMP_DIR

logger = logging.getLogger(__name__)


def _convert_to_wav(input_path: Path, work_dir: Path, label: str = "input") -> Path:
    """Convert any audio file to WAV using ffmpeg (24-bit lossless)."""
    output_path = work_dir / f"{label}.wav"

    if input_path.suffix.lower() == ".wav":
        shutil.copy2(input_path, output_path)
        return output_path

    logger.info("Converting %s → WAV via ffmpeg", input_path.suffix)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-acodec", "pcm_s24le",
        str(output_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        logger.error("ffmpeg conversion failed:\n%s", result.stderr)
        raise RuntimeError(
            f"Could not convert {input_path.suffix} to WAV. "
            f"Make sure ffmpeg is installed."
        )

    return output_path


def run_pipeline(
    input_path: Path,
    platform: str,
    reference_path: Path | None = None,
    on_progress=None,
    config: dict | None = None,
) -> Path:
    """
    Execute the audio optimization pipeline with configurable stages.

    0. Convert input to WAV
    1. Vocal isolation            (toggleable)
    2. Denoise                    (toggleable)
    3. Master to ref              (toggleable, needs reference)
    4. LUFS normalize             (toggleable, custom target)
    5. Studio effects             (wind removal, EQ, compression, reverb)

    Args:
        input_path:      Path to the uploaded audio file.
        platform:        Target platform for LUFS normalization.
        reference_path:  Optional reference track for mastering.
        on_progress:     Optional callback(stage: int, stage_name: str).
        config:          Optional dict with stage toggles and parameters.

    Returns:
        Path to the final processed WAV file.
    """
    cfg = config or {}
    stages = cfg.get("stages", {})
    effects = cfg.get("effects", {})

    def is_enabled(stage_key: str, default: bool = True) -> bool:
        return stages.get(stage_key, {}).get("enabled", default)

    def _progress(stage: int, name: str):
        if on_progress:
            on_progress(stage, name)

    request_id = uuid.uuid4().hex[:12]
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Pipeline started [%s] — platform=%s, config=%s", request_id, platform, cfg)

    try:
        # ----- Pre-process: convert to WAV -----
        _progress(0, "Converting to WAV")
        current = _convert_to_wav(input_path, work_dir, "input")

        wav_reference = None
        if reference_path is not None:
            wav_reference = _convert_to_wav(reference_path, work_dir, "reference")

        # ----- Stage 1: Vocal Isolation -----
        if is_enabled("isolate"):
            _progress(1, "Isolating vocals")
            from app.stages.isolate import isolate_vocals
            current = isolate_vocals(current, work_dir)
        else:
            _progress(1, "Skipping isolation")
            logger.info("Stage 1 — Skipped (disabled)")

        # ----- Stage 2: Denoise -----
        if is_enabled("denoise"):
            _progress(2, "Denoising audio")
            from app.stages.enhance import enhance_audio
            current = enhance_audio(current, work_dir)
        else:
            _progress(2, "Skipping denoise")
            logger.info("Stage 2 — Skipped (disabled)")

        # ----- Stage 3: Reference Mastering -----
        if is_enabled("master"):
            _progress(3, "Mastering audio")
            from app.stages.master import master_audio
            current = master_audio(current, work_dir, wav_reference)
        else:
            _progress(3, "Skipping mastering")
            logger.info("Stage 3 — Skipped (disabled)")

        # ----- Stage 4: LUFS Normalization -----
        if is_enabled("normalize"):
            _progress(4, "Normalizing loudness")
            from app.stages.normalize import normalize_loudness
            # Allow custom LUFS target from config
            custom_lufs = stages.get("normalize", {}).get("lufs")
            current = normalize_loudness(current, work_dir, platform, custom_lufs=custom_lufs)
        else:
            _progress(4, "Skipping normalization")
            logger.info("Stage 4 — Skipped (disabled)")

        # ----- Stage 5: Studio Effects -----
        has_effects = any(
            effects.get(k, {}).get("enabled", False)
            for k in ("wind_removal", "eq", "compressor", "reverb")
        )
        if has_effects:
            _progress(5, "Applying effects")
            from app.stages.effects import apply_effects
            current = apply_effects(
                current,
                work_dir,
                wind_removal=effects.get("wind_removal"),
                eq=effects.get("eq"),
                compressor=effects.get("compressor"),
                reverb=effects.get("reverb"),
            )
        else:
            _progress(5, "No effects")
            logger.info("Stage 5 — No effects enabled")

        logger.info("Pipeline complete [%s] → %s", request_id, current)
        return current

    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
