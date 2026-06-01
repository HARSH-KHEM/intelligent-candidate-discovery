"""
rank.py — Ranking API endpoints.

POST /api/rank       — Rank candidates against a JD
GET  /api/rank/{id}/status — Check async job status
"""

import logging
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse

from backend.models.schemas import (
    RankRequest,
    RankResponse,
    JobStatusResponse,
    JobStatus,
    CandidateRankResult,
)
from backend.services.ranking_service import (
    rank_candidates_sync,
    rank_candidates_async,
    process_ranking_job,
    get_job_status,
    get_all_candidates_from_db,
    is_large_batch,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/rank", tags=["Ranking"])


@router.post("", response_model=None)
async def rank_candidates(
    request: RankRequest,
    background_tasks: BackgroundTasks,
):
    """
    Rank candidates against a job description.

    For small batches (< 100 candidates): returns results immediately.
    For large batches (100+ candidates): returns a job_id for async polling.

    If no candidates are provided in the request, fetches from the database.
    """
    jd_text = request.jd_text

    # Get candidates
    if request.candidates:
        candidates = request.candidates
    else:
        candidates = await get_all_candidates_from_db()
        if not candidates:
            raise HTTPException(
                status_code=400,
                detail="No candidates provided and none found in database."
            )

    logger.info(f"Ranking request: {len(candidates)} candidates, top_k={request.top_k}")

    # Small batch → synchronous processing
    if not is_large_batch(candidates):
        try:
            result = await rank_candidates_sync(
                jd_text=jd_text,
                candidates=candidates,
                top_k=request.top_k,
                use_reranker=request.use_reranker,
            )
            return result
        except Exception as e:
            logger.error(f"Ranking failed: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Ranking failed: {str(e)}")

    # Large batch → async processing
    job_id = await rank_candidates_async(
        jd_text=jd_text,
        candidates=candidates,
        top_k=request.top_k,
        use_reranker=request.use_reranker,
    )

    # Schedule background processing
    background_tasks.add_task(
        process_ranking_job,
        job_id=job_id,
        jd_text=jd_text,
        candidates=candidates,
        top_k=request.top_k,
        use_reranker=request.use_reranker,
    )

    return JSONResponse(
        status_code=202,
        content={
            "job_id": job_id,
            "status": "pending",
            "total_candidates": len(candidates),
            "message": f"Large batch ({len(candidates)} candidates) queued for processing. Poll /api/rank/{job_id}/status for updates.",
        },
    )


@router.post("/csv", response_model=None)
async def rank_from_csv(
    background_tasks: BackgroundTasks,
    jd_text: str = Form(..., description="Job description text"),
    file: UploadFile = File(..., description="Candidates CSV file"),
    top_k: int = Form(default=50),
):
    """
    Rank candidates from a CSV file upload.

    Accepts a CSV with columns: candidate_id, name, skills, years_experience,
    current_role, industry, location, education, activity_score,
    profile_updated_date, resume_text
    """
    import csv
    import io

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV.")

    content = await file.read()
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))

    candidates = []
    for row in reader:
        # Parse skills
        if "skills" in row and isinstance(row["skills"], str):
            row["skills"] = [s.strip() for s in row["skills"].split(";") if s.strip()]

        # Parse numeric fields
        for field in ["years_experience"]:
            if field in row:
                try:
                    row[field] = int(row[field])
                except (ValueError, TypeError):
                    row[field] = 0

        for field in ["activity_score"]:
            if field in row:
                try:
                    row[field] = float(row[field])
                except (ValueError, TypeError):
                    row[field] = 0.5

        candidates.append(row)

    if not candidates:
        raise HTTPException(status_code=400, detail="CSV file contains no valid candidates.")

    # Reuse the same logic as the JSON endpoint
    request = RankRequest(jd_text=jd_text, candidates=candidates, top_k=top_k)
    return await rank_candidates(request, background_tasks)


@router.get("/{job_id}/status", response_model=JobStatusResponse)
async def check_job_status(job_id: str):
    """
    Check the status of an async ranking job.

    Returns the current status and results if completed.
    """
    job = get_job_status(job_id)

    if job is None:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found.")

    response = JobStatusResponse(
        job_id=job_id,
        status=JobStatus(job["status"]),
        total_candidates=job.get("total_candidates", 0),
        progress=job.get("progress", 0.0),
        error=job.get("error"),
    )

    if job["status"] == "completed" and "result" in job:
        result = job["result"]
        response.result = RankResponse(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            total_candidates=result["total_candidates"],
            ranked_candidates=[
                CandidateRankResult(**c) for c in result["ranked_candidates"]
            ],
            processing_time_ms=result.get("processing_time_ms"),
        )

    return response
