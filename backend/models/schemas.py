"""
schemas.py — Pydantic models for the Intelligent Candidate Discovery API.

Defines request/response models for candidates, job descriptions, and ranking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ───────────────────────────────────────────────────

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# ─── Candidate Models ───────────────────────────────────────

class CandidateBase(BaseModel):
    """Base candidate profile fields."""
    name: str = Field(..., min_length=1, max_length=200)
    skills: list[str] = Field(default_factory=list)
    years_experience: int = Field(default=0, ge=0, le=50)
    current_role: str = ""
    industry: str = ""
    location: str = ""
    education: str = ""
    activity_score: float = Field(default=0.5, ge=0.0, le=1.0)
    profile_updated_date: str = ""
    resume_text: str = ""


class CandidateCreate(CandidateBase):
    """Model for creating a new candidate."""
    candidate_id: Optional[str] = None  # Auto-generated if not provided


class CandidateResponse(CandidateBase):
    """Candidate returned from the API."""
    candidate_id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Job Description Models ─────────────────────────────────

class JobDescriptionBase(BaseModel):
    """Base job description fields."""
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(..., min_length=10)
    company: str = ""
    location: str = ""
    min_years: int = Field(default=0, ge=0)
    max_years: int = Field(default=20, ge=0)


class JobDescriptionCreate(JobDescriptionBase):
    """Model for creating a new job description."""
    pass


class JobDescriptionResponse(JobDescriptionBase):
    """Job description returned from the API."""
    id: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Ranking Models ─────────────────────────────────────────

class RankRequest(BaseModel):
    """Request to rank candidates against a JD."""
    jd_text: str = Field(..., min_length=10, description="Job description text")
    candidates: Optional[list[dict]] = Field(
        default=None,
        description="Optional inline candidates. If not provided, uses DB candidates.",
    )
    top_k: int = Field(default=50, ge=1, le=500)
    use_reranker: bool = Field(default=True, description="Whether to use LLM re-ranking")


class CandidateRankResult(BaseModel):
    """Ranking result for a single candidate."""
    candidate_id: str
    rank: int
    final_score: float = Field(ge=0.0, le=1.0)
    semantic_score: float = Field(ge=0.0, le=1.0)
    experience_score: float = Field(ge=0.0, le=1.0)
    behavioral_score: float = Field(ge=0.0, le=1.0)
    context_score: float = Field(ge=0.0, le=1.0)
    explanation: str = ""


class RankResponse(BaseModel):
    """Response with ranked candidates."""
    job_id: str
    status: JobStatus
    total_candidates: int
    ranked_candidates: list[CandidateRankResult] = []
    processing_time_ms: Optional[float] = None


class JobStatusResponse(BaseModel):
    """Response for checking job status."""
    job_id: str
    status: JobStatus
    total_candidates: int = 0
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    result: Optional[RankResponse] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None


# ─── Bulk Upload ─────────────────────────────────────────────

class BulkUploadResponse(BaseModel):
    """Response for bulk candidate upload."""
    inserted: int
    total: int
    message: str


# ─── Health ──────────────────────────────────────────────────

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    service: str = "backend"
    version: str = "1.0.0"
    mongodb: str = "connected"
