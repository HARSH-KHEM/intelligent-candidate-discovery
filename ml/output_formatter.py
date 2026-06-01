"""
output_formatter.py — Export ranked results as CSV or JSON.

Formats the final output with columns:
  candidate_id, rank, final_score, semantic_score, experience_score,
  behavioral_score, context_score, explanation

Usage:
    from ml.output_formatter import OutputFormatter
    formatter = OutputFormatter()
    formatter.to_csv(results, "output.csv")
    json_data = formatter.to_json(results)
"""

import csv
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# ─── Output Schema ───────────────────────────────────────────
OUTPUT_COLUMNS = [
    "candidate_id",
    "rank",
    "final_score",
    "semantic_score",
    "experience_score",
    "behavioral_score",
    "context_score",
    "explanation",
]


class OutputFormatter:
    """Formats and exports ranked candidate results."""

    def __init__(self, columns: list[str] | None = None):
        self.columns = columns or OUTPUT_COLUMNS

    def to_csv(self, results: list, output_path: str) -> str:
        """
        Write ranked results to a CSV file.

        Args:
            results: List of result objects or dicts with scoring fields.
            output_path: Path to write the CSV file.

        Returns:
            Absolute path to the written file.
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = self._normalize_results(results)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(rows)

        logger.info(f"CSV written: {path} ({len(rows)} rows)")
        return str(path.resolve())

    def to_json(self, results: list) -> list[dict]:
        """
        Convert ranked results to a JSON-serializable list.

        Args:
            results: List of result objects or dicts.

        Returns:
            List of dicts with standardized keys.
        """
        rows = self._normalize_results(results)
        logger.info(f"JSON formatted: {len(rows)} results")
        return rows

    def to_json_file(self, results: list, output_path: str) -> str:
        """Write results to a JSON file."""
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        rows = self.to_json(results)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(rows, f, indent=2, ensure_ascii=False)

        logger.info(f"JSON file written: {path}")
        return str(path.resolve())

    def _normalize_results(self, results: list) -> list[dict]:
        """Convert result objects (dataclasses or dicts) to standardized dicts."""
        rows = []
        for i, r in enumerate(results, start=1):
            if hasattr(r, "__dict__"):
                d = {k: getattr(r, k, None) for k in self.columns}
            elif isinstance(r, dict):
                d = {k: r.get(k, None) for k in self.columns}
            else:
                logger.warning(f"Skipping unknown result type: {type(r)}")
                continue

            # Ensure rank is set
            if d.get("rank") is None:
                d["rank"] = i

            # Round scores to 4 decimal places
            for key in ["final_score", "semantic_score", "experience_score",
                        "behavioral_score", "context_score"]:
                if d.get(key) is not None:
                    d[key] = round(float(d[key]), 4)

            rows.append(d)

        return rows


def main():
    """Test output formatting with sample data."""
    import tempfile

    sample_results = [
        {
            "candidate_id": "CID-0001",
            "rank": 1,
            "final_score": 0.8534,
            "semantic_score": 0.8200,
            "experience_score": 0.9000,
            "behavioral_score": 0.7500,
            "context_score": 0.8500,
            "explanation": "Strong skill alignment with 6y backend experience.",
        },
        {
            "candidate_id": "CID-0003",
            "rank": 2,
            "final_score": 0.7200,
            "semantic_score": 0.6800,
            "experience_score": 0.7500,
            "behavioral_score": 0.7000,
            "context_score": 0.8000,
            "explanation": "Experienced staff engineer with relevant tech stack.",
        },
        {
            "candidate_id": "CID-0002",
            "rank": 3,
            "final_score": 0.3100,
            "semantic_score": 0.2500,
            "experience_score": 0.3000,
            "behavioral_score": 0.4000,
            "context_score": 0.3500,
            "explanation": "Junior frontend developer — limited backend match.",
        },
    ]

    formatter = OutputFormatter()

    # Test JSON
    json_out = formatter.to_json(sample_results)
    print(f"JSON output ({len(json_out)} results):")
    print(json.dumps(json_out[:2], indent=2))

    # Test CSV
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w") as f:
        csv_path = f.name

    formatter.to_csv(sample_results, csv_path)
    print(f"\nCSV written to: {csv_path}")

    # Verify CSV
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            print(f"  {row['rank']:>2}. {row['candidate_id']} → {row['final_score']}")

    print("\n✅ Output formatter test passed.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
