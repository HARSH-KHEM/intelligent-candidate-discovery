"""
jobs.py — CRUD endpoints for job descriptions.

GET    /api/jobs          — List all saved JDs
POST   /api/jobs          — Create a new JD
GET    /api/jobs/{id}     — Get a specific JD
DELETE /api/jobs/{id}     — Delete a JD
"""

import logging
from datetime import datetime

from bson import ObjectId
from fastapi import APIRouter, HTTPException

from backend.db.mongo import get_jobs_collection
from backend.models.schemas import (
    JobDescriptionCreate,
    JobDescriptionResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Job Descriptions"])


@router.get("", response_model=list[JobDescriptionResponse])
async def list_jobs(skip: int = 0, limit: int = 50):
    """List all saved job descriptions."""
    collection = get_jobs_collection()
    jobs = []
    cursor = collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        jobs.append(JobDescriptionResponse(**doc))
    return jobs


@router.post("", response_model=JobDescriptionResponse, status_code=201)
async def create_job(job: JobDescriptionCreate):
    """Create a new job description."""
    collection = get_jobs_collection()

    doc = job.model_dump()
    doc["created_at"] = datetime.utcnow()

    result = await collection.insert_one(doc)
    doc["id"] = str(result.inserted_id)

    logger.info(f"Job created: {doc['id']} — {job.title}")
    return JobDescriptionResponse(**doc)


@router.get("/{job_id}", response_model=JobDescriptionResponse)
async def get_job(job_id: str):
    """Get a specific job description by ID."""
    collection = get_jobs_collection()

    try:
        doc = await collection.find_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    if not doc:
        raise HTTPException(status_code=404, detail="Job description not found.")

    doc["id"] = str(doc.pop("_id"))
    return JobDescriptionResponse(**doc)


@router.delete("/{job_id}", status_code=204)
async def delete_job(job_id: str):
    """Delete a job description."""
    collection = get_jobs_collection()

    try:
        result = await collection.delete_one({"_id": ObjectId(job_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid job ID format.")

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job description not found.")

    logger.info(f"Job deleted: {job_id}")
