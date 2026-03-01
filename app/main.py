"""
FastAPI application — Audio Optimizer Microservice.

POST /optimize  →  accepts an audio file + platform, returns optimized WAV.
"""

import logging
import shutil
from pathlib import Path

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from app.config import SUPPORTED_EXTENSIONS, TEMP_DIR, VALID_PLATFORMS
from app.pipeline import run_pipeline

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Audio Optimizer",
    description=(
        "4-stage audio optimization pipeline: "
        "Vocal Isolation → Denoise & Enhance → Reference Mastering → LUFS Normalization"
    ),
    version="1.0.0",
)


@app.post("/optimize")
async def optimize(
    file: UploadFile = File(..., description="Audio file to optimize (wav/mp3/m4a/flac/ogg)"),
    platform: str = Query(
        "youtube",
        description="Target platform for LUFS normalization",
        enum=VALID_PLATFORMS,
    ),
    reference: UploadFile | None = File(
        None,
        description="Optional reference track for mastering (Stage 3)",
    ),
):
    """
    Optimize an audio file through the full 4-stage pipeline.

    - **file**: The audio file to process.
    - **platform**: Target platform — determines LUFS target
      (`youtube`, `podcast`, `broadcast`, `reels`).
    - **reference**: Optional reference track for Stage 3 mastering.
      If omitted, Stage 3 is skipped.
    """
    # --- Validate platform ---
    if platform not in VALID_PLATFORMS:
        return JSONResponse(
            status_code=400,
            content={"error": f"Invalid platform. Choose from: {VALID_PLATFORMS}"},
        )

    # --- Validate file extension ---
    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Unsupported file type '{ext}'. Supported: {sorted(SUPPORTED_EXTENSIONS)}"
            },
        )

    # --- Save uploaded file to temp location ---
    import uuid

    upload_id = uuid.uuid4().hex[:12]
    upload_dir = TEMP_DIR / f"upload_{upload_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    input_path = upload_dir / f"input{ext}"
    with open(input_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # --- Save optional reference ---
    reference_path: Path | None = None
    if reference is not None:
        ref_ext = Path(reference.filename or "").suffix.lower()
        reference_path = upload_dir / f"reference{ref_ext}"
        with open(reference_path, "wb") as f:
            ref_content = await reference.read()
            f.write(ref_content)

    # --- Run pipeline ---
    try:
        logger.info(
            "Received optimization request: file=%s, platform=%s, reference=%s",
            file.filename,
            platform,
            reference.filename if reference else "none",
        )

        final_path = run_pipeline(
            input_path=input_path,
            platform=platform,
            reference_path=reference_path,
        )

        return FileResponse(
            path=str(final_path),
            media_type="audio/wav",
            filename=f"optimized_{platform}.wav",
            background=None,  # don't delete before send completes
        )

    except Exception as e:
        logger.exception("Pipeline failed")
        return JSONResponse(
            status_code=500,
            content={"error": f"Pipeline failed: {str(e)}"},
        )

    finally:
        # Clean up upload directory (pipeline work dir cleaned separately)
        shutil.rmtree(upload_dir, ignore_errors=True)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
