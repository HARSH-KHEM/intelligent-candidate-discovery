"""
pipeline.py — End-to-end ML ranking pipeline.

Orchestrates the full flow:
  1. Load candidates (CSV/JSON)
  2. Generate embeddings for JD and candidates
  3. Build FAISS index and retrieve top-K
  4. Score candidates across 4 dimensions
  5. Optionally re-rank with LLM
  6. Export ranked CSV

Also exposes a FastAPI app at /rank for service mode.

Usage (CLI):
    python -m ml.pipeline --jd data/sample_jd.txt --candidates data/candidates.csv --output results.csv

Usage (Service):
    uvicorn ml.pipeline:app --host 0.0.0.0 --port 8001
"""

import argparse
import csv
import json
import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np

from ml.embeddings import EmbeddingEngine
from ml.faiss_index import CandidateIndex
from ml.scorer import CandidateScorer, CandidateScore, parse_jd_metadata
from ml.reranker import LLMReranker
from ml.output_formatter import OutputFormatter

logger = logging.getLogger(__name__)

# ─── Constants ───────────────────────────────────────────────
DEFAULT_TOP_K = 50
DEFAULT_BATCH_SIZE = 64


class RankingPipeline:
    """End-to-end candidate ranking pipeline."""

    def __init__(
        self,
        top_k: int = DEFAULT_TOP_K,
        use_reranker: bool = True,
        batch_size: int = DEFAULT_BATCH_SIZE,
    ):
        """
        Initialize the pipeline components.

        Args:
            top_k: Number of top candidates to return after FAISS retrieval.
            use_reranker: Whether to use LLM re-ranking (requires API key).
            batch_size: Batch size for embedding generation.
        """
        self.top_k = top_k
        self.use_reranker = use_reranker
        self.batch_size = batch_size

        logger.info("Initializing pipeline components...")
        self.embedding_engine = EmbeddingEngine()
        self.candidate_index = CandidateIndex(dim=self.embedding_engine.dim)
        self.scorer = CandidateScorer()
        self.reranker = LLMReranker() if use_reranker else None
        self.formatter = OutputFormatter()
        logger.info("Pipeline initialized.")

    def run(
        self,
        jd_text: str,
        candidates: list[dict],
        output_path: Optional[str] = None,
    ) -> list[dict]:
        """
        Execute the full ranking pipeline.

        Args:
            jd_text: Raw job description text.
            candidates: List of candidate dicts with profile data.
            output_path: Optional path to write the output CSV.

        Returns:
            List of ranked candidate dicts with scores and explanations.
        """
        logger.info(f"Pipeline started. {len(candidates)} candidates, top_k={self.top_k}")

        # ── Step 1: Parse JD metadata ────────────────────────
        jd_data = parse_jd_metadata(jd_text)
        logger.info(f"JD parsed: {jd_data.get('min_years')}-{jd_data.get('max_years')}y, "
                     f"location={jd_data.get('location')}")

        # ── Step 2: Generate embeddings ──────────────────────
        jd_embedding = self.embedding_engine.encode_jd(jd_text)

        # Build candidate text for embedding (combine resume + skills + role)
        candidate_texts = []
        for c in candidates:
            text_parts = [
                c.get("resume_text", ""),
                f"Skills: {', '.join(c.get('skills', []))}",
                f"Role: {c.get('current_role', '')}",
                f"Industry: {c.get('industry', '')}",
            ]
            candidate_texts.append(" ".join(filter(None, text_parts)))

        candidate_embeddings = self.embedding_engine.encode_candidates(
            candidate_texts, batch_size=self.batch_size
        )

        # ── Step 3: Build FAISS index and search ─────────────
        self.candidate_index.reset()
        candidate_ids = [c.get("candidate_id", f"CID-{i}") for i, c in enumerate(candidates)]
        self.candidate_index.add(candidate_embeddings, candidate_ids)

        search_results = self.candidate_index.search(jd_embedding, top_k=len(candidates))

        # Map candidate_id → semantic score
        semantic_scores = {r.candidate_id: r.score for r in search_results}

        # ── Step 4: Multi-signal scoring ─────────────────────
        scored_candidates = self.scorer.score_candidates(
            jd_data, candidates, semantic_scores
        )

        # ── Step 5: Optional LLM re-ranking (top-K only) ────
        if self.reranker and self.use_reranker:
            top_candidates = self._prepare_for_reranking(
                scored_candidates[:self.top_k], candidates
            )
            reranked = self.reranker.rerank(jd_text, top_candidates, top_k=self.top_k)

            # Merge reranked results with remaining candidates
            final_results = []
            for r in reranked:
                final_results.append({
                    "candidate_id": r.candidate_id,
                    "rank": r.rank,
                    "final_score": r.final_score,
                    "semantic_score": r.semantic_score,
                    "experience_score": r.experience_score,
                    "behavioral_score": r.behavioral_score,
                    "context_score": r.context_score,
                    "explanation": r.explanation,
                })

            # Append remaining candidates beyond top-K
            reranked_ids = {r.candidate_id for r in reranked}
            remaining = [
                s for s in scored_candidates
                if s.candidate_id not in reranked_ids
            ]
            for i, s in enumerate(remaining, start=len(final_results) + 1):
                final_results.append({
                    "candidate_id": s.candidate_id,
                    "rank": i,
                    "final_score": s.final_score,
                    "semantic_score": s.semantic_score,
                    "experience_score": s.experience_score,
                    "behavioral_score": s.behavioral_score,
                    "context_score": s.context_score,
                    "explanation": s.explanation,
                })
        else:
            # Use scorer results directly
            final_results = []
            for i, s in enumerate(scored_candidates, start=1):
                final_results.append({
                    "candidate_id": s.candidate_id,
                    "rank": i,
                    "final_score": s.final_score,
                    "semantic_score": s.semantic_score,
                    "experience_score": s.experience_score,
                    "behavioral_score": s.behavioral_score,
                    "context_score": s.context_score,
                    "explanation": s.explanation,
                })

        # ── Step 6: Export results ────────────────────────────
        if output_path:
            self.formatter.to_csv(final_results, output_path)
            logger.info(f"Results exported to {output_path}")

        logger.info(f"Pipeline complete. {len(final_results)} candidates ranked.")
        return final_results

    def _prepare_for_reranking(
        self,
        scored: list[CandidateScore],
        candidates: list[dict],
    ) -> list[dict]:
        """Merge scored results with original candidate data for the reranker."""
        cand_lookup = {c.get("candidate_id"): c for c in candidates}

        merged = []
        for s in scored:
            orig = cand_lookup.get(s.candidate_id, {})
            merged.append({
                "candidate_id": s.candidate_id,
                "current_role": orig.get("current_role", ""),
                "years_experience": orig.get("years_experience", 0),
                "skills": orig.get("skills", []),
                "location": orig.get("location", ""),
                "industry": orig.get("industry", ""),
                "semantic_score": s.semantic_score,
                "experience_score": s.experience_score,
                "behavioral_score": s.behavioral_score,
                "context_score": s.context_score,
                "final_score": s.final_score,
            })

        return merged


def load_candidates_csv(filepath: str) -> list[dict]:
    """Load candidates from a CSV file."""
    candidates = []
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse skills from semicolon-separated string
            if "skills" in row and isinstance(row["skills"], str):
                row["skills"] = [s.strip() for s in row["skills"].split(";") if s.strip()]

            # Parse numeric fields
            for field in ["years_experience", "activity_score"]:
                if field in row:
                    try:
                        row[field] = float(row[field])
                        if field == "years_experience":
                            row[field] = int(row[field])
                    except (ValueError, TypeError):
                        pass

            candidates.append(row)

    return candidates


def load_candidates_json(filepath: str) -> list[dict]:
    """Load candidates from a JSON file."""
    with open(filepath, encoding="utf-8") as f:
        return json.load(f)


# ═══════════════════════════════════════════════════════════════
# FastAPI Service Mode
# ═══════════════════════════════════════════════════════════════

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Intelligent Candidate Discovery — ML Service",
    description="AI-powered candidate ranking pipeline",
    version="1.0.0",
)

# Global pipeline instance (loaded on first request)
_pipeline: Optional[RankingPipeline] = None


def get_pipeline() -> RankingPipeline:
    """Get or create the singleton pipeline instance."""
    global _pipeline
    if _pipeline is None:
        _pipeline = RankingPipeline(
            top_k=int(os.environ.get("TOP_K_CANDIDATES", 50)),
            use_reranker=bool(os.environ.get("OPENAI_API_KEY")),
        )
    return _pipeline


class RankRequest(BaseModel):
    jd_text: str
    candidates: list[dict]
    top_k: int = 50


class HealthResponse(BaseModel):
    status: str
    service: str


@app.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(status="healthy", service="ml-pipeline")


@app.post("/rank")
def rank_candidates(request: RankRequest):
    """
    Rank candidates against a job description.

    Returns a list of candidates sorted by rank with scores and explanations.
    """
    try:
        pipeline = get_pipeline()
        results = pipeline.run(
            jd_text=request.jd_text,
            candidates=request.candidates,
        )
        return {"ranked_candidates": results, "total": len(results)}
    except Exception as e:
        logger.error(f"Ranking failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════
# CLI Mode
# ═══════════════════════════════════════════════════════════════

def main():
    """Run the pipeline from the command line."""
    parser = argparse.ArgumentParser(
        description="Intelligent Candidate Discovery — ML Pipeline"
    )
    parser.add_argument(
        "--jd", required=True,
        help="Path to job description text file"
    )
    parser.add_argument(
        "--candidates", required=True,
        help="Path to candidates file (CSV or JSON)"
    )
    parser.add_argument(
        "--output", default="data/ranked_output.csv",
        help="Output CSV path (default: data/ranked_output.csv)"
    )
    parser.add_argument(
        "--top-k", type=int, default=DEFAULT_TOP_K,
        help=f"Number of top candidates (default: {DEFAULT_TOP_K})"
    )
    parser.add_argument(
        "--no-rerank", action="store_true",
        help="Skip LLM re-ranking"
    )

    args = parser.parse_args()

    # Load JD
    with open(args.jd, encoding="utf-8") as f:
        jd_text = f.read()

    # Load candidates
    cand_path = args.candidates
    if cand_path.endswith(".json"):
        candidates = load_candidates_json(cand_path)
    else:
        candidates = load_candidates_csv(cand_path)

    print(f"📄 JD loaded: {len(jd_text)} chars")
    print(f"👥 Candidates loaded: {len(candidates)}")

    # Run pipeline
    pipeline = RankingPipeline(
        top_k=args.top_k,
        use_reranker=not args.no_rerank,
    )

    results = pipeline.run(
        jd_text=jd_text,
        candidates=candidates,
        output_path=args.output,
    )

    # Print top 10
    print(f"\n🏆 Top {min(10, len(results))} Results:")
    print("-" * 80)
    for r in results[:10]:
        print(f"  #{r['rank']:>3}  {r['candidate_id']}  "
              f"score={r['final_score']:.4f}  "
              f"| {r['explanation'][:60]}...")

    print(f"\n✅ Pipeline complete. Output: {args.output}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    main()
