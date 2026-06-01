#!/usr/bin/env python3
"""
Generate sample_output.csv — Simulates the ML pipeline scoring against the sample JD.
Produces a realistic ranked output without requiring OpenAI or the full stack.
"""

import json
import csv
import random
import math
from pathlib import Path

random.seed(42)

DATA_DIR = Path(__file__).parent

# Load candidates
with open(DATA_DIR / "candidates.json") as f:
    candidates = json.load(f)

# Load JD for reference
with open(DATA_DIR / "sample_jd.txt") as f:
    jd_text = f.read().lower()

# ─── Scoring heuristics (simulate the real pipeline) ─────────

# Skills the JD strongly values
JD_PRIMARY_SKILLS = {
    "Python", "FastAPI", "Django", "Go", "Golang",
    "PostgreSQL", "MongoDB", "Redis",
    "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "Kafka", "RabbitMQ", "Microservices", "REST APIs",
    "CI/CD", "GitHub Actions", "Jenkins",
    "System Design", "Data Structures", "Algorithms",
    "Prometheus", "Grafana", "Machine Learning",
}
JD_PRIMARY_SKILLS_LOWER = {s.lower() for s in JD_PRIMARY_SKILLS}

JD_BONUS_SKILLS = {
    "GraphQL", "gRPC", "TensorFlow", "Model Serving",
    "API Design", "Linux", "Nginx", "Elasticsearch",
    "Mentoring", "Code Review", "Technical Writing",
}
JD_BONUS_SKILLS_LOWER = {s.lower() for s in JD_BONUS_SKILLS}

PREFERRED_LOCATIONS = {"bengaluru", "hyderabad", "remote — india", "pune"}
PREFERRED_INDUSTRIES = {"technology", "saas", "fintech", "ai/ml", "startup", "e-commerce"}
PREFERRED_EDUCATION_KEYWORDS = ["iit", "iiit", "bits", "iisc", "nit", "stanford", "cmu", "carnegie"]

BACKEND_ROLES = {
    "backend developer", "senior backend developer", "software engineer",
    "senior software engineer", "platform engineer", "staff engineer",
    "principal engineer", "tech lead", "sde-ii", "sde-iii",
    "software architect", "solutions architect", "site reliability engineer",
}


def semantic_score(candidate):
    """Simulate semantic similarity between candidate resume and JD."""
    skills_lower = {s.lower() for s in candidate["skills"]}
    resume_lower = candidate["resume_text"].lower()

    # Primary skill overlap
    primary_matches = len(skills_lower & JD_PRIMARY_SKILLS_LOWER)
    primary_ratio = primary_matches / len(JD_PRIMARY_SKILLS_LOWER)

    # Bonus skill overlap
    bonus_matches = len(skills_lower & JD_BONUS_SKILLS_LOWER)
    bonus_ratio = bonus_matches / len(JD_BONUS_SKILLS_LOWER)

    # Resume text relevance (keyword density as proxy for embedding similarity)
    jd_keywords = ["distributed", "microservices", "scale", "api", "backend",
                    "latency", "kafka", "pipeline", "cloud", "deploy",
                    "monitor", "mentor", "architecture", "production"]
    text_hits = sum(1 for kw in jd_keywords if kw in resume_lower)
    text_ratio = text_hits / len(jd_keywords)

    score = (primary_ratio * 0.50) + (bonus_ratio * 0.20) + (text_ratio * 0.30)

    # Add slight noise for realism
    score += random.gauss(0, 0.03)
    return round(max(0.0, min(1.0, score)), 4)


def experience_score(candidate):
    """Score based on years of experience and role seniority."""
    yoe = candidate["years_experience"]

    # Ideal range: 5-8 years (per JD), decent: 4-10, acceptable: 3-12
    if 5 <= yoe <= 8:
        exp_fit = 1.0
    elif 4 <= yoe <= 10:
        exp_fit = 0.8
    elif 3 <= yoe <= 12:
        exp_fit = 0.6
    elif yoe >= 13:
        exp_fit = 0.5  # Overqualified
    else:
        exp_fit = 0.3  # Too junior

    # Role relevance
    role_lower = candidate["current_role"].lower()
    if role_lower in BACKEND_ROLES:
        role_fit = 1.0
    elif any(kw in role_lower for kw in ["engineer", "developer", "architect"]):
        role_fit = 0.7
    else:
        role_fit = 0.4

    score = (exp_fit * 0.6) + (role_fit * 0.4) + random.gauss(0, 0.02)
    return round(max(0.0, min(1.0, score)), 4)


def behavioral_score(candidate):
    """Score based on activity and engagement signals."""
    activity = candidate["activity_score"]

    # Profile freshness
    from datetime import datetime
    updated = datetime.strptime(candidate["profile_updated_date"], "%Y-%m-%d")
    days_since = (datetime.now() - updated).days

    if days_since <= 30:
        freshness = 1.0
    elif days_since <= 90:
        freshness = 0.8
    elif days_since <= 180:
        freshness = 0.6
    elif days_since <= 365:
        freshness = 0.4
    else:
        freshness = 0.2

    score = (activity * 0.6) + (freshness * 0.4) + random.gauss(0, 0.02)
    return round(max(0.0, min(1.0, score)), 4)


def context_score(candidate):
    """Score based on location, industry, and education fit."""
    loc = candidate["location"].lower()
    ind = candidate["industry"].lower()
    edu = candidate["education"].lower()

    loc_fit = 1.0 if loc in PREFERRED_LOCATIONS else 0.5
    ind_fit = 1.0 if ind in PREFERRED_INDUSTRIES else 0.5
    edu_fit = 1.0 if any(kw in edu for kw in PREFERRED_EDUCATION_KEYWORDS) else 0.5

    score = (loc_fit * 0.4) + (ind_fit * 0.3) + (edu_fit * 0.3) + random.gauss(0, 0.02)
    return round(max(0.0, min(1.0, score)), 4)


def generate_explanation(candidate, scores):
    """Generate a natural-language explanation for the ranking."""
    parts = []

    if scores["semantic"] >= 0.7:
        top_skills = [s for s in candidate["skills"]
                      if s.lower() in JD_PRIMARY_SKILLS_LOWER][:4]
        parts.append(f"Strong skill alignment ({', '.join(top_skills)})")
    elif scores["semantic"] >= 0.4:
        parts.append("Moderate skill overlap with JD requirements")
    else:
        parts.append("Limited direct skill match with JD")

    yoe = candidate["years_experience"]
    if 5 <= yoe <= 8:
        parts.append(f"{yoe}y experience matches the 5-8y requirement")
    elif yoe > 8:
        parts.append(f"{yoe}y experience (exceeds requirement, strong seniority)")
    else:
        parts.append(f"{yoe}y experience (below 5-8y target range)")

    if scores["behavioral"] >= 0.7:
        parts.append("highly active profile with recent updates")
    elif scores["behavioral"] <= 0.3:
        parts.append("low recent activity")

    if candidate["location"].lower() in PREFERRED_LOCATIONS:
        parts.append(f"location match ({candidate['location']})")

    return ". ".join(parts) + "."


# ─── Score all candidates ────────────────────────────────────

WEIGHTS = {
    "semantic": 0.40,
    "experience": 0.25,
    "behavioral": 0.20,
    "context": 0.15,
}

results = []
for c in candidates:
    scores = {
        "semantic": semantic_score(c),
        "experience": experience_score(c),
        "behavioral": behavioral_score(c),
        "context": context_score(c),
    }

    final = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    final = round(max(0.0, min(1.0, final)), 4)

    explanation = generate_explanation(c, scores)

    results.append({
        "candidate_id": c["candidate_id"],
        "final_score": final,
        "semantic_score": scores["semantic"],
        "experience_score": scores["experience"],
        "behavioral_score": scores["behavioral"],
        "context_score": scores["context"],
        "explanation": explanation,
    })

# Sort by final score descending
results.sort(key=lambda x: x["final_score"], reverse=True)

# Assign ranks
for i, r in enumerate(results, 1):
    r["rank"] = i

# ─── Write CSV ───────────────────────────────────────────────

output_path = DATA_DIR / "sample_output.csv"
fieldnames = [
    "candidate_id", "rank", "final_score", "semantic_score",
    "experience_score", "behavioral_score", "context_score", "explanation",
]

with open(output_path, "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"✅ Ranked output written to {output_path}")
print(f"   Total candidates ranked: {len(results)}")
print(f"   Top candidate: {results[0]['candidate_id']} (score: {results[0]['final_score']})")
print(f"   Bottom candidate: {results[-1]['candidate_id']} (score: {results[-1]['final_score']})")
print(f"\n🏆 Top 10:")
for r in results[:10]:
    print(f"   #{r['rank']:>3}  {r['candidate_id']}  score={r['final_score']:.4f}  | {r['explanation'][:70]}...")
