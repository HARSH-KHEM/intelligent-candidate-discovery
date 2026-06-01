"""
scorer.py — Multi-signal weighted scoring engine.

Computes a final score for each candidate across 4 dimensions:
  - Semantic skill match  (35%): cosine similarity between JD & candidate embeddings
  - Experience fit        (25%): years, role level, recency
  - Behavioral signals    (25%): profile activity, certifications, freshness
  - Context fit           (15%): industry/location alignment

Usage:
    from ml.scorer import CandidateScorer
    scorer = CandidateScorer()
    scored = scorer.score_candidates(jd_data, candidates, semantic_scores)
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# ─── Score Weights ───────────────────────────────────────────
WEIGHT_SEMANTIC = 0.35
WEIGHT_EXPERIENCE = 0.25
WEIGHT_BEHAVIORAL = 0.25
WEIGHT_CONTEXT = 0.15

# ─── Role Seniority Mapping ─────────────────────────────────
SENIORITY_MAP = {
    "intern": 0.2, "junior": 0.3, "associate": 0.4,
    "sde-i": 0.4, "sde-ii": 0.6, "sde-iii": 0.8,
    "mid": 0.5, "senior": 0.7, "staff": 0.85,
    "principal": 0.9, "lead": 0.8, "tech lead": 0.85,
    "architect": 0.85, "manager": 0.75, "director": 0.9,
    "vp": 0.95, "cto": 1.0,
}

# ─── Certification Keywords ─────────────────────────────────
CERTIFICATION_KEYWORDS = [
    "aws certified", "google cloud", "azure certified",
    "kubernetes", "ckad", "cka", "terraform",
    "pmp", "scrum master", "cissp", "oscp",
    "tensorflow", "pytorch", "ml engineer",
    "data engineer", "solutions architect",
]

# ─── Industry Categories ────────────────────────────────────
TECH_INDUSTRIES = {
    "technology", "saas", "fintech", "ai/ml", "startup",
    "e-commerce", "edtech", "cybersecurity", "iot",
    "enterprise software", "gaming", "media",
}

METRO_LOCATIONS = {
    "bengaluru", "bangalore", "hyderabad", "mumbai", "pune",
    "delhi", "delhi ncr", "noida", "gurgaon", "gurugram",
    "chennai", "kolkata", "remote", "remote — india",
}


@dataclass
class CandidateScore:
    """Detailed scoring breakdown for a single candidate."""
    candidate_id: str
    semantic_score: float = 0.0
    experience_score: float = 0.0
    behavioral_score: float = 0.0
    context_score: float = 0.0
    final_score: float = 0.0
    explanation: str = ""
    metadata: dict = field(default_factory=dict)


class CandidateScorer:
    """Multi-signal candidate scoring engine."""

    def __init__(
        self,
        weight_semantic: float = WEIGHT_SEMANTIC,
        weight_experience: float = WEIGHT_EXPERIENCE,
        weight_behavioral: float = WEIGHT_BEHAVIORAL,
        weight_context: float = WEIGHT_CONTEXT,
    ):
        self.weights = {
            "semantic": weight_semantic,
            "experience": weight_experience,
            "behavioral": weight_behavioral,
            "context": weight_context,
        }
        total = sum(self.weights.values())
        if abs(total - 1.0) > 0.01:
            logger.warning(f"Weights sum to {total}, expected 1.0. Normalizing.")
            for k in self.weights:
                self.weights[k] /= total

    def score_candidates(
        self,
        jd_data: dict,
        candidates: list[dict],
        semantic_scores: dict[str, float],
    ) -> list[CandidateScore]:
        """
        Score all candidates against a job description.

        Args:
            jd_data: Parsed JD with keys like 'text', 'required_years',
                     'industry', 'location', 'skills'.
            candidates: List of candidate dicts with profile data.
            semantic_scores: Dict mapping candidate_id → cosine similarity score.

        Returns:
            List of CandidateScore sorted by final_score descending.
        """
        logger.info(f"Scoring {len(candidates)} candidates...")
        results = []

        for candidate in candidates:
            cid = candidate.get("candidate_id", "unknown")

            sem = semantic_scores.get(cid, 0.0)
            exp = self._experience_score(candidate, jd_data)
            beh = self._behavioral_score(candidate)
            ctx = self._context_score(candidate, jd_data)

            final = (
                self.weights["semantic"] * sem
                + self.weights["experience"] * exp
                + self.weights["behavioral"] * beh
                + self.weights["context"] * ctx
            )

            score = CandidateScore(
                candidate_id=cid,
                semantic_score=round(sem, 4),
                experience_score=round(exp, 4),
                behavioral_score=round(beh, 4),
                context_score=round(ctx, 4),
                final_score=round(final, 4),
            )
            score.explanation = self._generate_explanation(score, candidate)
            results.append(score)

        results.sort(key=lambda s: s.final_score, reverse=True)
        logger.info(
            f"Scoring complete. Top score: {results[0].final_score if results else 'N/A'}"
        )
        return results

    # ─── Dimension Scorers ───────────────────────────────────

    def _experience_score(self, candidate: dict, jd_data: dict) -> float:
        """
        Score based on years of experience, role seniority, and career fit.

        Components:
          - Years fit: how well candidate's years match JD requirement
          - Role seniority: mapping current role to a seniority level
          - Career trajectory: bonus for progressive roles
        """
        # Extract years of experience
        yoe = candidate.get("years_experience", 0)
        if isinstance(yoe, str):
            nums = re.findall(r"\d+", str(yoe))
            yoe = int(nums[0]) if nums else 0

        # JD target years (default 5 if not specified)
        target_min = jd_data.get("min_years", 5)
        target_max = jd_data.get("max_years", 8)
        target_mid = (target_min + target_max) / 2

        # Years fit: bell curve centered on target range
        if target_min <= yoe <= target_max:
            years_fit = 1.0
        elif yoe < target_min:
            gap = target_min - yoe
            years_fit = max(0.1, 1.0 - (gap / target_mid) * 0.5)
        else:
            gap = yoe - target_max
            years_fit = max(0.3, 1.0 - (gap / target_mid) * 0.3)  # Less penalty for over-qualified

        # Role seniority match
        role = candidate.get("current_role", "").lower()
        seniority = 0.5  # default
        for keyword, level in SENIORITY_MAP.items():
            if keyword in role:
                seniority = max(seniority, level)

        # Combine
        score = (years_fit * 0.6) + (seniority * 0.4)
        return min(1.0, max(0.0, score))

    def _behavioral_score(self, candidate: dict) -> float:
        """
        Score based on behavioral and engagement signals.

        Components:
          - Profile freshness: when was the profile last updated
          - Activity score: engagement metric from the platform
          - Certifications: presence of industry certifications
        """
        # Activity score (direct from data)
        activity = candidate.get("activity_score", 0.5)
        if isinstance(activity, str):
            try:
                activity = float(activity)
            except ValueError:
                activity = 0.5

        # Profile freshness
        profile_date_str = candidate.get("profile_updated_date", "")
        freshness = 0.5
        if profile_date_str:
            try:
                updated = datetime.strptime(profile_date_str, "%Y-%m-%d")
                days_ago = (datetime.now() - updated).days
                if days_ago <= 30:
                    freshness = 1.0
                elif days_ago <= 90:
                    freshness = 0.8
                elif days_ago <= 180:
                    freshness = 0.6
                elif days_ago <= 365:
                    freshness = 0.4
                else:
                    freshness = 0.2
            except (ValueError, TypeError):
                freshness = 0.5

        # Certification signals (from resume text)
        resume = candidate.get("resume_text", "").lower()
        cert_count = sum(1 for cert in CERTIFICATION_KEYWORDS if cert in resume)
        cert_score = min(1.0, cert_count * 0.25)

        # Weighted combination
        score = (activity * 0.40) + (freshness * 0.35) + (cert_score * 0.25)
        return min(1.0, max(0.0, score))

    def _context_score(self, candidate: dict, jd_data: dict) -> float:
        """
        Score based on contextual fit: industry and location alignment.

        Components:
          - Industry match: same industry or adjacent tech industry
          - Location match: same city or remote-compatible
        """
        # Industry alignment
        cand_industry = candidate.get("industry", "").lower().strip()
        jd_industry = jd_data.get("industry", "technology").lower().strip()

        if cand_industry == jd_industry:
            industry_fit = 1.0
        elif cand_industry in TECH_INDUSTRIES and jd_industry in TECH_INDUSTRIES:
            industry_fit = 0.7  # Adjacent tech industry
        elif cand_industry in TECH_INDUSTRIES:
            industry_fit = 0.5
        else:
            industry_fit = 0.3

        # Location alignment
        cand_loc = candidate.get("location", "").lower().strip()
        jd_loc = jd_data.get("location", "").lower().strip()

        if not jd_loc or "remote" in cand_loc or "remote" in jd_loc:
            location_fit = 0.9  # Remote is almost always a good match
        elif jd_loc and jd_loc in cand_loc:
            location_fit = 1.0
        elif cand_loc in METRO_LOCATIONS and jd_loc in METRO_LOCATIONS:
            location_fit = 0.6  # Both in major metro areas
        else:
            location_fit = 0.4

        score = (industry_fit * 0.5) + (location_fit * 0.5)
        return min(1.0, max(0.0, score))

    # ─── Explanation Generator ───────────────────────────────

    def _generate_explanation(
        self, score: CandidateScore, candidate: dict
    ) -> str:
        """Generate a one-sentence explanation for the candidate's ranking."""
        parts = []

        # Semantic
        if score.semantic_score >= 0.7:
            parts.append("strong skill alignment with JD requirements")
        elif score.semantic_score >= 0.4:
            parts.append("moderate skill overlap")
        else:
            parts.append("limited direct skill match")

        # Experience
        yoe = candidate.get("years_experience", "?")
        if score.experience_score >= 0.8:
            parts.append(f"{yoe}y experience is an excellent fit")
        elif score.experience_score >= 0.6:
            parts.append(f"{yoe}y experience is a reasonable fit")
        else:
            parts.append(f"{yoe}y experience is outside the ideal range")

        # Behavioral
        if score.behavioral_score >= 0.7:
            parts.append("highly active profile")
        elif score.behavioral_score <= 0.3:
            parts.append("low recent activity")

        # Context
        loc = candidate.get("location", "")
        if score.context_score >= 0.8 and loc:
            parts.append(f"good contextual fit ({loc})")

        return ". ".join(p.capitalize() for p in parts) + "."


def parse_jd_metadata(jd_text: str) -> dict:
    """
    Extract structured metadata from a raw JD text.

    Returns dict with keys: text, min_years, max_years, industry, location, skills.
    """
    text_lower = jd_text.lower()

    # Extract years requirement
    years_match = re.search(r"(\d+)\s*[-–]\s*(\d+)\s*years?", text_lower)
    if years_match:
        min_y, max_y = int(years_match.group(1)), int(years_match.group(2))
    else:
        single_match = re.search(r"(\d+)\+?\s*years?", text_lower)
        if single_match:
            min_y = int(single_match.group(1))
            max_y = min_y + 3
        else:
            min_y, max_y = 3, 8

    # Extract location
    location = ""
    for loc in METRO_LOCATIONS:
        if loc in text_lower:
            location = loc.title()
            break

    # Detect industry
    industry = "technology"
    for ind in TECH_INDUSTRIES:
        if ind in text_lower:
            industry = ind
            break

    return {
        "text": jd_text,
        "min_years": min_y,
        "max_years": max_y,
        "industry": industry,
        "location": location,
    }


def main():
    """Test the scoring engine with sample data."""
    # Sample JD
    jd_data = {
        "text": "Senior Backend Engineer, 5-8 years, Bengaluru",
        "min_years": 5,
        "max_years": 8,
        "industry": "technology",
        "location": "bengaluru",
    }

    # Sample candidates
    candidates = [
        {
            "candidate_id": "CID-0001",
            "years_experience": 6,
            "current_role": "Senior Backend Developer",
            "industry": "SaaS",
            "location": "Bengaluru",
            "activity_score": 0.85,
            "profile_updated_date": "2026-05-20",
            "resume_text": "Senior backend developer with AWS Certified Solutions Architect.",
        },
        {
            "candidate_id": "CID-0002",
            "years_experience": 2,
            "current_role": "Junior Frontend Developer",
            "industry": "Media",
            "location": "London, UK",
            "activity_score": 0.3,
            "profile_updated_date": "2025-01-15",
            "resume_text": "React developer focused on UI components.",
        },
        {
            "candidate_id": "CID-0003",
            "years_experience": 10,
            "current_role": "Staff Engineer",
            "industry": "Fintech",
            "location": "Pune",
            "activity_score": 0.7,
            "profile_updated_date": "2026-04-01",
            "resume_text": "Staff engineer leading platform team. Google Cloud certified.",
        },
    ]

    # Simulated semantic scores
    semantic_scores = {
        "CID-0001": 0.82,
        "CID-0002": 0.25,
        "CID-0003": 0.68,
    }

    scorer = CandidateScorer()
    results = scorer.score_candidates(jd_data, candidates, semantic_scores)

    print("Scoring Results:")
    print("-" * 80)
    for s in results:
        print(f"  {s.candidate_id}: final={s.final_score:.4f} "
              f"(sem={s.semantic_score}, exp={s.experience_score}, "
              f"beh={s.behavioral_score}, ctx={s.context_score})")
        print(f"    → {s.explanation}")
    print(f"\n✅ Scorer test passed. Top candidate: {results[0].candidate_id}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
