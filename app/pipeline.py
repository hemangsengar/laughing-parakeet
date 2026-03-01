"""
Pipeline orchestrator — runs all 4 stages sequentially.
"""

import logging
import shutil
import subprocess
import uuid
from pathlib import Path

from app.config import TEMP_DIR

logger = logging.getLogger(__name__)


def _convert_to_wav(input_path: Path, work_dir: Path, label: str = "input") -> Path:
    """
    Convert any audio file to WAV using ffmpeg.

    This ensures soundfile/libsndfile can always read the audio,
    regardless of the original format (M4A, MP3, AAC, OGG, etc.).
    """
    output_path = work_dir / f"{label}.wav"

    # If already a WAV, just copy it
    if input_path.suffix.lower() == ".wav":
        shutil.copy2(input_path, output_path)
        return output_path

    logger.info("Converting %s → WAV via ffmpeg", input_path.suffix)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-acodec", "pcm_s24le",   # 24-bit lossless — preserves full decoded quality
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
) -> Path:
    """
    Execute the full 4-stage audio optimization pipeline.

    0. Convert input to WAV      (ffmpeg — handles M4A, MP3, etc.)
    1. Vocal isolation            (Demucs)
    2. Denoise + enhance          (Resemble Enhance)
    3. Master to ref              (Matchering) — skipped if no reference
    4. LUFS normalize             (ffmpeg)

    Args:
        input_path:      Path to the uploaded audio file.
        platform:        Target platform (youtube, podcast, broadcast, reels).
        reference_path:  Optional reference track for mastering.
        on_progress:     Optional callback(stage: int, stage_name: str).

    Returns:
        Path to the final processed WAV file.
    """
    def _progress(stage: int, name: str):
        if on_progress:
            on_progress(stage, name)

    # Create a unique working directory for this request
    request_id = uuid.uuid4().hex[:12]
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Pipeline started [%s] — platform=%s", request_id, platform)

    try:
        # ----- Pre-process: convert to WAV -----
        _progress(0, "Converting to WAV")
        wav_input = _convert_to_wav(input_path, work_dir, "input")

        # Convert reference track too if provided
        wav_reference = None
        if reference_path is not None:
            wav_reference = _convert_to_wav(reference_path, work_dir, "reference")

        # ----- Stage 1: Vocal Isolation -----
        _progress(1, "Isolating vocals")
        from app.stages.isolate import isolate_vocals

        vocals_path = isolate_vocals(wav_input, work_dir)

        # ----- Stage 2: Denoise + Enhance -----
        _progress(2, "Denoising & enhancing")
        from app.stages.enhance import enhance_audio

        enhanced_path = enhance_audio(vocals_path, work_dir)

        # ----- Stage 3: Reference Mastering -----
        _progress(3, "Mastering audio")
        from app.stages.master import master_audio

        mastered_path = master_audio(enhanced_path, work_dir, wav_reference)

        # ----- Stage 4: LUFS Normalization -----
        _progress(4, "Normalizing loudness")
        from app.stages.normalize import normalize_loudness

        final_path = normalize_loudness(mastered_path, work_dir, platform)

        logger.info("Pipeline complete [%s] → %s", request_id, final_path)
        return final_path

    except Exception:
        # Clean up on failure
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
