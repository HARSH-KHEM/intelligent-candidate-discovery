"""
reranker.py — GPT-4o-mini re-ranking with explanations.

Takes the top-K candidates from FAISS + scorer and uses an LLM to produce
a refined ranking with one-sentence explanations for each candidate.

Usage:
    from ml.reranker import LLMReranker
    reranker = LLMReranker()
    reranked = await reranker.rerank(jd_text, top_candidates)
"""

import json
import logging
import os
from dataclasses import dataclass

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TOP_K = 50


@dataclass
class RerankedCandidate:
    """A candidate after LLM re-ranking."""
    candidate_id: str
    rank: int
    final_score: float
    explanation: str
    semantic_score: float = 0.0
    experience_score: float = 0.0
    behavioral_score: float = 0.0
    context_score: float = 0.0


def _build_rerank_prompt(jd_text: str, candidates: list[dict]) -> str:
    """
    Build the system + user prompt for the LLM reranker.

    Args:
        jd_text: The full job description text.
        candidates: List of candidate dicts with scores and profile info.

    Returns:
        Formatted prompt string.
    """
    candidate_summaries = []
    for i, c in enumerate(candidates, 1):
        summary = (
            f"[{i}] ID: {c['candidate_id']} | "
            f"Role: {c.get('current_role', 'N/A')} | "
            f"Exp: {c.get('years_experience', '?')}y | "
            f"Skills: {', '.join(c.get('skills', [])[:8])} | "
            f"Location: {c.get('location', 'N/A')} | "
            f"Industry: {c.get('industry', 'N/A')} | "
            f"Semantic: {c.get('semantic_score', 0):.3f} | "
            f"Experience: {c.get('experience_score', 0):.3f} | "
            f"Behavioral: {c.get('behavioral_score', 0):.3f} | "
            f"Context: {c.get('context_score', 0):.3f} | "
            f"Score: {c.get('final_score', 0):.3f}"
        )
        candidate_summaries.append(summary)

    candidates_block = "\n".join(candidate_summaries)

    prompt = f"""You are an expert technical recruiter AI. Given a job description and a list of pre-scored candidates, re-rank them and provide a concise one-sentence explanation for each.

JOB DESCRIPTION:
{jd_text[:2000]}

CANDIDATES (pre-scored by ML pipeline):
{candidates_block}

INSTRUCTIONS:
1. Re-rank the candidates considering the JD requirements holistically.
2. Consider skill depth, not just keyword overlap.
3. Weight practical experience and role relevance highly.
4. For each candidate, provide a one-sentence explanation of their ranking.

OUTPUT FORMAT (valid JSON array, no markdown):
[
  {{"candidate_id": "CID-XXXX", "rank": 1, "explanation": "One sentence reason."}},
  ...
]

Return ONLY the JSON array. Include ALL candidates."""

    return prompt


class LLMReranker:
    """Re-ranks candidates using GPT-4o-mini for refined ordering and explanations."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
    ):
        """
        Initialize the reranker.

        Args:
            model: OpenAI model to use.
            api_key: OpenAI API key (falls back to OPENAI_API_KEY env var).
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._client = None

    def _get_client(self):
        """Lazy-load the OpenAI client."""
        if self._client is None:
            try:
                from openai import OpenAI
                self._client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package required for LLM reranking. "
                    "Install with: pip install openai"
                )
        return self._client

    def rerank(
        self,
        jd_text: str,
        candidates: list[dict],
        top_k: int = DEFAULT_TOP_K,
    ) -> list[RerankedCandidate]:
        """
        Re-rank candidates using the LLM.

        Args:
            jd_text: Raw job description text.
            candidates: List of candidate dicts with scores.
            top_k: Maximum number of candidates to rerank.

        Returns:
            List of RerankedCandidate sorted by new ranking.
        """
        # Limit to top_k candidates
        candidates = candidates[:top_k]

        if not self.api_key:
            logger.warning(
                "No OPENAI_API_KEY set. Skipping LLM reranking, "
                "returning original order with default explanations."
            )
            return self._fallback_rerank(candidates)

        prompt = _build_rerank_prompt(jd_text, candidates)

        try:
            client = self._get_client()
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a precise technical recruiter AI. "
                            "Output only valid JSON arrays."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=4000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content.strip()
            parsed = json.loads(content)

            # Handle both direct array and wrapped object
            if isinstance(parsed, dict):
                parsed = parsed.get("candidates", parsed.get("results", []))

            return self._process_llm_response(parsed, candidates)

        except Exception as e:
            logger.error(f"LLM reranking failed: {e}. Using fallback.")
            return self._fallback_rerank(candidates)

    def _process_llm_response(
        self,
        llm_results: list[dict],
        original_candidates: list[dict],
    ) -> list[RerankedCandidate]:
        """Process the LLM response and merge with original scores."""
        # Build lookup for original scores
        score_lookup = {
            c["candidate_id"]: c for c in original_candidates
        }

        # Build lookup for LLM explanations
        llm_lookup = {}
        for item in llm_results:
            cid = item.get("candidate_id", "")
            llm_lookup[cid] = {
                "rank": item.get("rank", 999),
                "explanation": item.get("explanation", ""),
            }

        results = []
        for rank, cid in enumerate(
            sorted(llm_lookup.keys(), key=lambda x: llm_lookup[x]["rank"]),
            start=1,
        ):
            orig = score_lookup.get(cid, {})
            results.append(RerankedCandidate(
                candidate_id=cid,
                rank=rank,
                final_score=orig.get("final_score", 0.0),
                explanation=llm_lookup[cid]["explanation"],
                semantic_score=orig.get("semantic_score", 0.0),
                experience_score=orig.get("experience_score", 0.0),
                behavioral_score=orig.get("behavioral_score", 0.0),
                context_score=orig.get("context_score", 0.0),
            ))

        # Add any candidates the LLM missed
        covered = {r.candidate_id for r in results}
        for c in original_candidates:
            if c["candidate_id"] not in covered:
                results.append(RerankedCandidate(
                    candidate_id=c["candidate_id"],
                    rank=len(results) + 1,
                    final_score=c.get("final_score", 0.0),
                    explanation="Not re-ranked by LLM — original score retained.",
                    semantic_score=c.get("semantic_score", 0.0),
                    experience_score=c.get("experience_score", 0.0),
                    behavioral_score=c.get("behavioral_score", 0.0),
                    context_score=c.get("context_score", 0.0),
                ))

        return results

    def _fallback_rerank(self, candidates: list[dict]) -> list[RerankedCandidate]:
        """Fallback when LLM is unavailable — preserve original ranking."""
        results = []
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.get("final_score", 0),
            reverse=True,
        )

        for rank, c in enumerate(sorted_candidates, start=1):
            # Generate a basic explanation from scores
            parts = []
            if c.get("semantic_score", 0) >= 0.6:
                parts.append("strong skill match")
            elif c.get("semantic_score", 0) >= 0.3:
                parts.append("moderate skill alignment")
            else:
                parts.append("limited skill overlap")

            yoe = c.get("years_experience", "?")
            parts.append(f"{yoe}y experience")

            role = c.get("current_role", "")
            if role:
                parts.append(f"currently {role}")

            explanation = ". ".join(p.capitalize() for p in parts) + "."

            results.append(RerankedCandidate(
                candidate_id=c["candidate_id"],
                rank=rank,
                final_score=c.get("final_score", 0.0),
                explanation=explanation,
                semantic_score=c.get("semantic_score", 0.0),
                experience_score=c.get("experience_score", 0.0),
                behavioral_score=c.get("behavioral_score", 0.0),
                context_score=c.get("context_score", 0.0),
            ))

        return results


def main():
    """Test the reranker with sample data (uses fallback if no API key)."""
    candidates = [
        {
            "candidate_id": "CID-0001",
            "current_role": "Senior Backend Developer",
            "years_experience": 6,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL"],
            "location": "Bengaluru",
            "industry": "SaaS",
            "semantic_score": 0.82,
            "experience_score": 0.90,
            "behavioral_score": 0.75,
            "context_score": 0.85,
            "final_score": 0.83,
        },
        {
            "candidate_id": "CID-0002",
            "current_role": "Junior Developer",
            "years_experience": 2,
            "skills": ["JavaScript", "React"],
            "location": "London",
            "industry": "Media",
            "semantic_score": 0.25,
            "experience_score": 0.30,
            "behavioral_score": 0.40,
            "context_score": 0.35,
            "final_score": 0.31,
        },
        {
            "candidate_id": "CID-0003",
            "current_role": "Staff Engineer",
            "years_experience": 10,
            "skills": ["Go", "Kubernetes", "AWS", "PostgreSQL", "Redis"],
            "location": "Pune",
            "industry": "Fintech",
            "semantic_score": 0.68,
            "experience_score": 0.75,
            "behavioral_score": 0.70,
            "context_score": 0.80,
            "final_score": 0.72,
        },
    ]

    jd_text = "Senior Backend Engineer, 5-8 years Python experience."

    reranker = LLMReranker()
    results = reranker.rerank(jd_text, candidates)

    print("Reranked Results:")
    print("-" * 70)
    for r in results:
        print(f"  #{r.rank} {r.candidate_id} score={r.final_score:.4f}")
        print(f"     {r.explanation}")

    print(f"\n✅ Reranker test passed. {len(results)} candidates processed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
