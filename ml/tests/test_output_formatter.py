"""
test_output_formatter.py — Unit tests for the output formatter.
"""

import csv
import json
import tempfile
import pytest
from ml.output_formatter import OutputFormatter


@pytest.fixture
def formatter():
    return OutputFormatter()


@pytest.fixture
def sample_results():
    return [
        {
            "candidate_id": "CID-0001",
            "rank": 1,
            "final_score": 0.85,
            "semantic_score": 0.82,
            "experience_score": 0.90,
            "behavioral_score": 0.75,
            "context_score": 0.85,
            "explanation": "Strong match.",
        },
        {
            "candidate_id": "CID-0002",
            "rank": 2,
            "final_score": 0.45,
            "semantic_score": 0.30,
            "experience_score": 0.50,
            "behavioral_score": 0.40,
            "context_score": 0.55,
            "explanation": "Moderate match.",
        },
    ]


class TestOutputFormatter:
    def test_to_json(self, formatter, sample_results):
        """JSON output should match input structure."""
        output = formatter.to_json(sample_results)
        assert len(output) == 2
        assert output[0]["candidate_id"] == "CID-0001"
        assert output[0]["rank"] == 1

    def test_to_csv(self, formatter, sample_results):
        """CSV should have header and correct number of rows."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name

        formatter.to_csv(sample_results, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["candidate_id"] == "CID-0001"
        assert float(rows[0]["final_score"]) == 0.85

    def test_csv_has_all_columns(self, formatter, sample_results):
        """CSV should contain all required columns."""
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
            path = f.name

        formatter.to_csv(sample_results, path)

        with open(path) as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

        expected = [
            "candidate_id", "rank", "final_score", "semantic_score",
            "experience_score", "behavioral_score", "context_score", "explanation",
        ]
        assert headers == expected

    def test_scores_rounded(self, formatter):
        """Scores should be rounded to 4 decimal places."""
        results = [{
            "candidate_id": "CID-0001",
            "rank": 1,
            "final_score": 0.123456789,
            "semantic_score": 0.987654321,
            "experience_score": 0.5,
            "behavioral_score": 0.333,
            "context_score": 0.777,
            "explanation": "Test.",
        }]

        output = formatter.to_json(results)
        assert output[0]["final_score"] == 0.1235
        assert output[0]["semantic_score"] == 0.9877

    def test_empty_results(self, formatter):
        """Should handle empty results gracefully."""
        output = formatter.to_json([])
        assert output == []

    def test_json_file_output(self, formatter, sample_results):
        """JSON file output should be valid JSON."""
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            path = f.name

        formatter.to_json_file(sample_results, path)

        with open(path) as f:
            data = json.load(f)

        assert len(data) == 2
