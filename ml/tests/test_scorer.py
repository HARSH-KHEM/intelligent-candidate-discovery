"""
test_scorer.py — Unit tests for the multi-signal scorer.
"""

import pytest
from ml.scorer import CandidateScorer, parse_jd_metadata


# ─── Fixtures ────────────────────────────────────────────────

@pytest.fixture
def scorer():
    return CandidateScorer()


@pytest.fixture
def jd_data():
    return {
        "text": "Senior Backend Engineer",
        "min_years": 5,
        "max_years": 8,
        "industry": "technology",
        "location": "bengaluru",
    }


@pytest.fixture
def sample_candidates():
    return [
        {
            "candidate_id": "CID-0001",
            "years_experience": 6,
            "current_role": "Senior Backend Developer",
            "industry": "SaaS",
            "location": "Bengaluru",
            "activity_score": 0.85,
            "profile_updated_date": "2026-05-20",
            "resume_text": "Senior backend dev with AWS Certified.",
        },
        {
            "candidate_id": "CID-0002",
            "years_experience": 2,
            "current_role": "Junior Developer",
            "industry": "Media",
            "location": "London, UK",
            "activity_score": 0.3,
            "profile_updated_date": "2025-01-15",
            "resume_text": "React developer focused on UI.",
        },
    ]


# ─── Tests ───────────────────────────────────────────────────

class TestCandidateScorer:
    def test_scoring_returns_results(self, scorer, jd_data, sample_candidates):
        """Scorer should return a result for each candidate."""
        sem_scores = {"CID-0001": 0.8, "CID-0002": 0.2}
        results = scorer.score_candidates(jd_data, sample_candidates, sem_scores)

        assert len(results) == 2

    def test_results_sorted_descending(self, scorer, jd_data, sample_candidates):
        """Results should be sorted by final_score descending."""
        sem_scores = {"CID-0001": 0.8, "CID-0002": 0.2}
        results = scorer.score_candidates(jd_data, sample_candidates, sem_scores)

        assert results[0].final_score >= results[1].final_score

    def test_better_candidate_scores_higher(self, scorer, jd_data, sample_candidates):
        """The senior backend developer should score higher than the junior."""
        sem_scores = {"CID-0001": 0.8, "CID-0002": 0.2}
        results = scorer.score_candidates(jd_data, sample_candidates, sem_scores)

        assert results[0].candidate_id == "CID-0001"

    def test_scores_in_valid_range(self, scorer, jd_data, sample_candidates):
        """All scores should be between 0 and 1."""
        sem_scores = {"CID-0001": 0.8, "CID-0002": 0.2}
        results = scorer.score_candidates(jd_data, sample_candidates, sem_scores)

        for r in results:
            assert 0.0 <= r.final_score <= 1.0
            assert 0.0 <= r.semantic_score <= 1.0
            assert 0.0 <= r.experience_score <= 1.0
            assert 0.0 <= r.behavioral_score <= 1.0
            assert 0.0 <= r.context_score <= 1.0

    def test_explanation_not_empty(self, scorer, jd_data, sample_candidates):
        """Each result should have a non-empty explanation."""
        sem_scores = {"CID-0001": 0.8, "CID-0002": 0.2}
        results = scorer.score_candidates(jd_data, sample_candidates, sem_scores)

        for r in results:
            assert r.explanation
            assert len(r.explanation) > 10

    def test_custom_weights(self, jd_data, sample_candidates):
        """Custom weights should affect final scores."""
        sem_scores = {"CID-0001": 0.9, "CID-0002": 0.1}

        scorer_semantic_heavy = CandidateScorer(
            weight_semantic=0.9, weight_experience=0.05,
            weight_behavioral=0.025, weight_context=0.025,
        )
        results = scorer_semantic_heavy.score_candidates(
            jd_data, sample_candidates, sem_scores
        )

        # With 90% semantic weight, the gap should be huge
        assert results[0].final_score - results[1].final_score > 0.3

    def test_empty_candidates(self, scorer, jd_data):
        """Should handle empty candidate list gracefully."""
        results = scorer.score_candidates(jd_data, [], {})
        assert results == []


class TestParseJdMetadata:
    def test_extracts_year_range(self):
        """Should extract min-max years from JD text."""
        jd = "Looking for 5-8 years of experience in backend development."
        result = parse_jd_metadata(jd)
        assert result["min_years"] == 5
        assert result["max_years"] == 8

    def test_extracts_single_years(self):
        """Should handle '5+ years' format."""
        jd = "Requires 5+ years of Python experience."
        result = parse_jd_metadata(jd)
        assert result["min_years"] == 5

    def test_extracts_location(self):
        """Should detect location from JD text."""
        jd = "Position based in Bengaluru with hybrid work."
        result = parse_jd_metadata(jd)
        assert "bengaluru" in result["location"].lower()

    def test_defaults_for_missing_data(self):
        """Should provide defaults when data is missing."""
        jd = "We need an engineer."
        result = parse_jd_metadata(jd)
        assert result["min_years"] == 3
        assert result["max_years"] == 8
