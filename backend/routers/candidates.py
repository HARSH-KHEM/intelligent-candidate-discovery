"""
candidates.py — CRUD endpoints for candidate profiles.

GET    /api/candidates          — List candidates (paginated)
POST   /api/candidates          — Create a single candidate
POST   /api/candidates/bulk     — Bulk import candidates (JSON array)
GET    /api/candidates/{id}     — Get a candidate by candidate_id
DELETE /api/candidates/{id}     — Delete a candidate
DELETE /api/candidates          — Delete all candidates
"""

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from backend.db.mongo import get_candidates_collection
from backend.models.schemas import (
    CandidateCreate,
    CandidateResponse,
    BulkUploadResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/candidates", tags=["Candidates"])


@router.get("", response_model=list[CandidateResponse])
async def list_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
):
    """List candidates with pagination."""
    collection = get_candidates_collection()
    candidates = []
    cursor = collection.find({}, {"_id": 0}).skip(skip).limit(limit)
    async for doc in cursor:
        candidates.append(CandidateResponse(**doc))
    return candidates


@router.get("/count")
async def count_candidates():
    """Get the total number of candidates."""
    collection = get_candidates_collection()
    count = await collection.count_documents({})
    return {"count": count}


@router.post("", response_model=CandidateResponse, status_code=201)
async def create_candidate(candidate: CandidateCreate):
    """Create a single candidate profile."""
    collection = get_candidates_collection()

    doc = candidate.model_dump()
    if not doc.get("candidate_id"):
        doc["candidate_id"] = f"CID-{uuid.uuid4().hex[:8].upper()}"
    doc["created_at"] = datetime.utcnow()

    # Check for duplicate
    existing = await collection.find_one({"candidate_id": doc["candidate_id"]})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Candidate {doc['candidate_id']} already exists."
        )

    await collection.insert_one(doc)
    doc.pop("_id", None)

    logger.info(f"Candidate created: {doc['candidate_id']}")
    return CandidateResponse(**doc)


@router.post("/bulk", response_model=BulkUploadResponse, status_code=201)
async def bulk_upload_candidates(candidates: list[dict]):
    """
    Bulk import candidates from a JSON array.

    Skips duplicates and returns the count of successfully inserted candidates.
    """
    collection = get_candidates_collection()

    inserted = 0
    for i, c in enumerate(candidates):
        if not c.get("candidate_id"):
            c["candidate_id"] = f"CID-{uuid.uuid4().hex[:8].upper()}"
        c["created_at"] = datetime.utcnow()

        try:
            await collection.replace_one(
                {"candidate_id": c["candidate_id"]},
                c,
                upsert=True,
            )
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert candidate {c.get('candidate_id')}: {e}")

    logger.info(f"Bulk upload: {inserted}/{len(candidates)} candidates inserted.")
    return BulkUploadResponse(
        inserted=inserted,
        total=len(candidates),
        message=f"Successfully imported {inserted} of {len(candidates)} candidates.",
    )


@router.get("/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(candidate_id: str):
    """Get a candidate by their candidate_id."""
    collection = get_candidates_collection()

    doc = await collection.find_one(
        {"candidate_id": candidate_id}, {"_id": 0}
    )

    if not doc:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")

    return CandidateResponse(**doc)


@router.delete("/{candidate_id}", status_code=204)
async def delete_candidate(candidate_id: str):
    """Delete a candidate by their candidate_id."""
    collection = get_candidates_collection()
    result = await collection.delete_one({"candidate_id": candidate_id})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Candidate {candidate_id} not found.")

    logger.info(f"Candidate deleted: {candidate_id}")


@router.delete("", status_code=204)
async def delete_all_candidates():
    """Delete all candidates from the database."""
    collection = get_candidates_collection()
    result = await collection.delete_many({})
    logger.info(f"All candidates deleted: {result.deleted_count} removed.")
