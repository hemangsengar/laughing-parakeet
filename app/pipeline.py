"""
Pipeline orchestrator — runs all 4 stages sequentially.
"""

import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from app.config import TEMP_DIR

logger = logging.getLogger(__name__)


def run_pipeline(
    input_path: Path,
    platform: str,
    reference_path: Path | None = None,
) -> Path:
    """
    Execute the full 4-stage audio optimization pipeline.

    1. Vocal isolation   (Demucs)
    2. Denoise + enhance (Resemble Enhance)
    3. Master to ref     (Matchering) — skipped if no reference
    4. LUFS normalize    (ffmpeg)

    Args:
        input_path:      Path to the uploaded audio file.
        platform:        Target platform (youtube, podcast, broadcast, reels).
        reference_path:  Optional reference track for mastering.

    Returns:
        Path to the final processed WAV file.  The caller is responsible
        for cleaning up the work directory after serving the file.
    """
    # Create a unique working directory for this request
    request_id = uuid.uuid4().hex[:12]
    work_dir = TEMP_DIR / request_id
    work_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Pipeline started [%s] — platform=%s", request_id, platform)

    try:
        # ----- Stage 1: Vocal Isolation -----
        from app.stages.isolate import isolate_vocals

        vocals_path = isolate_vocals(input_path, work_dir)

        # ----- Stage 2: Denoise + Enhance -----
        from app.stages.enhance import enhance_audio

        enhanced_path = enhance_audio(vocals_path, work_dir)

        # ----- Stage 3: Reference Mastering -----
        from app.stages.master import master_audio

        mastered_path = master_audio(enhanced_path, work_dir, reference_path)

        # ----- Stage 4: LUFS Normalization -----
        from app.stages.normalize import normalize_loudness

        final_path = normalize_loudness(mastered_path, work_dir, platform)

        logger.info("Pipeline complete [%s] → %s", request_id, final_path)
        return final_path

    except Exception:
        # Clean up on failure
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
