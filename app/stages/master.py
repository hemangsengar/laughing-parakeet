"""
Stage 3 — Reference-based Mastering using Matchering.

Matches EQ, compression, and stereo width of the enhanced audio
to a professional reference track.
"""

import logging
from pathlib import Path

import matchering as mg

logger = logging.getLogger(__name__)


def master_audio(
    input_path: Path,
    work_dir: Path,
    reference_path: Path | None = None,
) -> Path:
    """
    Master the audio against a reference track using Matchering.

    If no reference is provided, this stage is skipped and the input
    path is returned unchanged.

    Args:
        input_path:      Path to the enhanced WAV.
        work_dir:        Temporary working directory for this request.
        reference_path:  Optional path to a reference track.

    Returns:
        Path to the mastered WAV (or the original input if skipped).
    """
    if reference_path is None:
        logger.info("Stage 3 — Skipped (no reference track provided)")
        return input_path

    logger.info("Stage 3 — Mastering against reference: %s", reference_path.name)

    output_path = work_dir / "mastered.wav"

    mg.process(
        target=str(input_path),
        reference=str(reference_path),
        results=[
            mg.pcm24(str(output_path)),
        ],
    )

    logger.info("Stage 3 complete → %s", output_path)
    return output_path
