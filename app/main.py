"""
FastAPI application — Audio Optimizer Microservice.

POST /optimize   → start a job, returns { job_id }
GET  /progress   → SSE stream of stage progress
GET  /download   → download the final WAV
GET  /            → frontend UI
"""

import asyncio
import json
import logging
import shutil
import threading
import uuid
from pathlib import Path

from fastapi import FastAPI, File, Query, UploadFile
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from app.config import BASE_DIR, SUPPORTED_EXTENSIONS, TEMP_DIR, VALID_PLATFORMS
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
# Job store  (in-memory — fine for single-instance local use)
# ---------------------------------------------------------------------------
jobs: dict[str, dict] = {}
# Each job: {
#   "status": "queued" | "running" | "done" | "error",
#   "stage": 0-4,
#   "stage_name": str,
#   "progress": 0-100,
#   "error": str | None,
#   "output_path": Path | None,
#   "platform": str,
# }

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

# Serve the frontend UI
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def _run_job(job_id: str, input_path: Path, platform: str, reference_path: Path | None, config: dict | None = None):
    """Run the pipeline in a background thread, updating job progress."""
    job = jobs[job_id]

    def on_progress(stage: int, stage_name: str, status: str = "running"):
        import time as _time
        job["stage"] = stage
        job["stage_name"] = stage_name
        job["status"] = status
        job["stage_times"][str(stage)] = _time.time()
        logger.info("Job %s — Stage %d: %s", job_id, stage, stage_name)

    try:
        job["status"] = "running"
        final_path = run_pipeline(
            input_path=input_path,
            platform=platform,
            reference_path=reference_path,
            on_progress=on_progress,
            config=config,
        )
        job["status"] = "done"
        job["stage"] = 6
        job["stage_name"] = "Complete"
        job["output_path"] = final_path
    except Exception as e:
        logger.exception("Job %s failed", job_id)
        job["status"] = "error"
        job["error"] = str(e)


@app.post("/optimize")
async def optimize(
    file: UploadFile = File(..., description="Audio file to optimize"),
    platform: str = Query("youtube", description="Target platform", enum=VALID_PLATFORMS),
    reference: UploadFile | None = File(None, description="Optional reference track"),
    config: str = Query("{}", description="JSON config for stage toggles and effects"),
):
    """Start an optimization job. Returns a job_id for progress tracking."""
    # Validate
    if platform not in VALID_PLATFORMS:
        return JSONResponse(status_code=400, content={"error": f"Invalid platform. Choose from: {VALID_PLATFORMS}"})

    ext = Path(file.filename or "").suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return JSONResponse(status_code=400, content={"error": f"Unsupported file type '{ext}'."})

    # Save upload
    job_id = uuid.uuid4().hex[:12]
    upload_dir = TEMP_DIR / f"upload_{job_id}"
    upload_dir.mkdir(parents=True, exist_ok=True)

    input_path = upload_dir / f"input{ext}"
    with open(input_path, "wb") as f:
        f.write(await file.read())

    reference_path = None
    if reference is not None:
        ref_ext = Path(reference.filename or "").suffix.lower()
        reference_path = upload_dir / f"reference{ref_ext}"
        with open(reference_path, "wb") as f:
            f.write(await reference.read())

    # Create job
    jobs[job_id] = {
        "status": "queued",
        "stage": 0,
        "stage_name": "Queued",
        "error": None,
        "output_path": None,
        "input_path": str(input_path),
        "filename": file.filename,
        "platform": platform,
        "start_time": __import__('time').time(),
        "stage_times": {},
    }

    # Parse config JSON
    import json as _json
    try:
        parsed_config = _json.loads(config) if config else {}
    except _json.JSONDecodeError:
        parsed_config = {}

    # Run in background thread
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, input_path, platform, reference_path, parsed_config),
        daemon=True,
    )
    thread.start()

    logger.info("Job %s created: file=%s, platform=%s, config=%s", job_id, file.filename, platform, parsed_config)
    return {"job_id": job_id}


@app.get("/progress/{job_id}")
async def progress(job_id: str):
    """
    Server-Sent Events stream for job progress.
    Sends a JSON event every second with current stage info.
    Closes when the job is done or errored.
    """
    if job_id not in jobs:
        return JSONResponse(status_code=404, content={"error": "Job not found"})

    async def event_stream():
        while True:
            job = jobs.get(job_id)
            if job is None:
                break

            data = {
                "status": job["status"],
                "stage": job["stage"],
                "stage_name": job["stage_name"],
                "error": job.get("error"),
            }
            yield f"data: {json.dumps(data)}\n\n"

            if job["status"] in ("done", "error"):
                break

            await asyncio.sleep(1)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/download/{job_id}")
async def download(job_id: str):
    """Download the finished optimized audio file."""
    job = jobs.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    if job["status"] != "done":
        return JSONResponse(status_code=400, content={"error": f"Job is {job['status']}, not done"})

    return FileResponse(
        path=str(job["output_path"]),
        media_type="audio/wav",
        filename=f"optimized_{job['platform']}.wav",
    )


@app.get("/original/{job_id}")
async def original(job_id: str):
    """Serve the original uploaded audio for before/after comparison."""
    job = jobs.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    input_path = Path(job.get("input_path", ""))
    if not input_path.exists():
        return JSONResponse(status_code=404, content={"error": "Original file no longer available"})
    return FileResponse(path=str(input_path), media_type="audio/mpeg")


@app.get("/job/{job_id}")
async def job_info(job_id: str):
    """Get full job metadata including timing."""
    job = jobs.get(job_id)
    if job is None:
        return JSONResponse(status_code=404, content={"error": "Job not found"})
    import time as _time
    return {
        "status": job["status"],
        "stage": job["stage"],
        "stage_name": job["stage_name"],
        "filename": job.get("filename"),
        "platform": job["platform"],
        "error": job.get("error"),
        "stage_times": job.get("stage_times", {}),
        "elapsed": round(_time.time() - job.get("start_time", _time.time()), 1),
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path), media_type="text/html")
    return {"message": "Audio Optimizer API — visit /docs for Swagger UI"}
