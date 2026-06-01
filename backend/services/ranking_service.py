"""
ranking_service.py — Business logic layer between API routes and ML pipeline.

Handles synchronous and asynchronous ranking, job tracking, and result storage.
"""

import json
import logging
import time
import uuid
from datetime import datetime
from typing import Optional

from backend.db.mongo import (
    get_candidates_collection,
    get_results_collection,
)

logger = logging.getLogger(__name__)

# ─── In-Memory Job Tracker (for async jobs) ─────────────────
_jobs: dict[str, dict] = {}

# Threshold for async processing
ASYNC_THRESHOLD = 100


def _generate_job_id() -> str:
    """Generate a unique job ID."""
    return f"job-{uuid.uuid4().hex[:12]}"


async def get_all_candidates_from_db() -> list[dict]:
    """Fetch all candidates from MongoDB."""
    collection = get_candidates_collection()
    candidates = []
    async for doc in collection.find({}, {"_id": 0}):
        candidates.append(doc)
    return candidates


async def rank_candidates_sync(
    jd_text: str,
    candidates: list[dict],
    top_k: int = 50,
    use_reranker: bool = True,
) -> dict:
    """
    Run the ranking pipeline synchronously (for small batches < 100).

    Returns the full ranking result.
    """
    job_id = _generate_job_id()
    start_time = time.time()

    _jobs[job_id] = {
        "status": "processing",
        "total_candidates": len(candidates),
        "progress": 0.0,
        "created_at": datetime.utcnow().isoformat(),
    }

    try:
        # Import ML pipeline (lazy to avoid loading models at import time)
        from ml.pipeline import RankingPipeline

        pipeline = RankingPipeline(
            top_k=top_k,
            use_reranker=use_reranker,
        )

        results = pipeline.run(jd_text=jd_text, candidates=candidates)

        elapsed_ms = (time.time() - start_time) * 1000

        result = {
            "job_id": job_id,
            "status": "completed",
            "total_candidates": len(results),
            "ranked_candidates": results,
            "processing_time_ms": round(elapsed_ms, 2),
        }

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["progress"] = 100.0
        _jobs[job_id]["result"] = result

        # Store result in MongoDB
        try:
            collection = get_results_collection()
            await collection.replace_one(
                {"job_id": job_id},
                {**result, "created_at": datetime.utcnow()},
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Failed to store result in DB: {e}")

        return result

    except Exception as e:
        logger.error(f"Ranking failed for job {job_id}: {e}", exc_info=True)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)
        raise


async def rank_candidates_async(
    jd_text: str,
    candidates: list[dict],
    top_k: int = 50,
    use_reranker: bool = True,
) -> str:
    """
    Start an async ranking job (for large batches 100+).

    Returns the job_id immediately for polling.
    """
    job_id = _generate_job_id()

    _jobs[job_id] = {
        "status": "pending",
        "total_candidates": len(candidates),
        "progress": 0.0,
        "created_at": datetime.utcnow().isoformat(),
    }

    # The actual processing is triggered via BackgroundTasks in the router
    return job_id


async def process_ranking_job(
    job_id: str,
    jd_text: str,
    candidates: list[dict],
    top_k: int = 50,
    use_reranker: bool = True,
):
    """
    Background task to process a ranking job.

    This is called by FastAPI's BackgroundTasks.
    """
    _jobs[job_id]["status"] = "processing"
    start_time = time.time()

    try:
        from ml.pipeline import RankingPipeline

        pipeline = RankingPipeline(
            top_k=top_k,
            use_reranker=use_reranker,
        )

        results = pipeline.run(jd_text=jd_text, candidates=candidates)

        elapsed_ms = (time.time() - start_time) * 1000

        result = {
            "job_id": job_id,
            "status": "completed",
            "total_candidates": len(results),
            "ranked_candidates": results,
            "processing_time_ms": round(elapsed_ms, 2),
        }

        _jobs[job_id]["status"] = "completed"
        _jobs[job_id]["progress"] = 100.0
        _jobs[job_id]["result"] = result

        # Store in MongoDB
        try:
            collection = get_results_collection()
            await collection.replace_one(
                {"job_id": job_id},
                {**result, "created_at": datetime.utcnow()},
                upsert=True,
            )
        except Exception as e:
            logger.warning(f"Failed to store async result: {e}")

    except Exception as e:
        logger.error(f"Async ranking failed for {job_id}: {e}", exc_info=True)
        _jobs[job_id]["status"] = "failed"
        _jobs[job_id]["error"] = str(e)


def get_job_status(job_id: str) -> Optional[dict]:
    """Get the current status of a ranking job."""
    return _jobs.get(job_id)


def is_large_batch(candidates: list) -> bool:
    """Check if the batch should be processed asynchronously."""
    return len(candidates) >= ASYNC_THRESHOLD
