"""
main.py — FastAPI application entry point.

Intelligent Candidate Discovery — Backend API
Provides REST endpoints for ranking candidates against job descriptions.

Run:
    uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
"""

import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to Python path so ml/ can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.db.mongo import connect_db, close_db
from backend.routers import rank, jobs, candidates
from backend.models.schemas import HealthResponse

# ─── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ─── Lifespan ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: connect to DB on startup, close on shutdown."""
    logger.info("🚀 Starting Intelligent Candidate Discovery API...")
    try:
        await connect_db()
        logger.info("✅ MongoDB connected.")
    except Exception as e:
        logger.warning(f"⚠️  MongoDB connection failed: {e}. API will start without DB.")
    yield
    await close_db()
    logger.info("👋 API shutdown complete.")


# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="Intelligent Candidate Discovery",
    description=(
        "AI-powered candidate ranking API. Upload a job description and "
        "get candidates ranked by semantic similarity, experience fit, "
        "behavioral signals, and contextual relevance."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://frontend:3000",
        "*",  # Allow all for hackathon demo
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────
app.include_router(rank.router)
app.include_router(jobs.router)
app.include_router(candidates.router)


# ─── Root & Health ───────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root():
    """API root — redirect to docs."""
    return {
        "name": "Intelligent Candidate Discovery API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint for Docker and load balancers."""
    try:
        from backend.db.mongo import get_db
        db = get_db()
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"

    return HealthResponse(
        status="healthy",
        service="backend",
        version="1.0.0",
        mongodb=mongo_status,
    )


# ─── CLI Entry Point ────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=os.environ.get("BACKEND_HOST", "0.0.0.0"),
        port=int(os.environ.get("BACKEND_PORT", 8000)),
        reload=True,
    )
