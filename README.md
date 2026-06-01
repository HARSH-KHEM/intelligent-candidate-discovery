<p align="center">
  <h1 align="center">🎯 Intelligent Candidate Discovery</h1>
  <p align="center">
    <strong>AI-powered talent ranking that understands meaning, not just keywords.</strong>
  </p>
  <p align="center">
    <a href="#quick-start">Quick Start</a> •
    <a href="#how-it-works">How It Works</a> •
    <a href="#architecture">Architecture</a> •
    <a href="#sample-results">Sample Results</a> •
    <a href="#team">Team</a>
  </p>
  <p align="center">
    <img src="https://img.shields.io/badge/Python-3.11+-blue?logo=python" alt="Python">
    <img src="https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi" alt="FastAPI">
    <img src="https://img.shields.io/badge/React-18+-61DAFB?logo=react" alt="React">
    <img src="https://img.shields.io/badge/MongoDB-7.0-47A248?logo=mongodb" alt="MongoDB">
    <img src="https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker" alt="Docker">
    <img src="https://img.shields.io/badge/INDIA%20RUNS-Hackathon-orange" alt="INDIA RUNS">
  </p>
</p>

---

## 🚀 The Problem

Traditional Applicant Tracking Systems rely on **keyword matching** — they miss great candidates who describe their skills differently and promote résumé stuffers who game the system.

> A candidate who writes "containerized microservices" instead of "Docker" gets filtered out.
> Someone who architected distributed systems for 5 years — but never listed "Kubernetes" — never gets seen.

**Intelligent Candidate Discovery** fixes this by using **semantic AI** to understand what candidates *actually* bring to the table.

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        SYSTEM ARCHITECTURE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐    │
│   │   Frontend    │     │   Backend    │     │  ML Service  │    │
│   │   (React)     │────▶│  (FastAPI)   │────▶│  (Python)    │    │
│   │   Port 3000   │     │  Port 8000   │     │  Port 8001   │    │
│   └──────────────┘     └──────┬───────┘     └──────┬───────┘    │
│                               │                     │             │
│                               ▼                     ▼             │
│                        ┌──────────────┐     ┌──────────────┐    │
│                        │   MongoDB    │     │    FAISS      │    │
│                        │  Port 27017  │     │  Vector Index │    │
│                        └──────────────┘     └──────────────┘    │
│                                                                   │
├─────────────────────────────────────────────────────────────────┤
│                     Docker Compose Network                       │
└─────────────────────────────────────────────────────────────────┘

Data Flow:
  1. Hiring manager uploads Job Description via React dashboard
  2. Backend receives JD → forwards to ML Service
  3. ML Service:
     a. Generates JD embedding (sentence-transformers)
     b. Queries FAISS index for top-K similar candidates
     c. Scores candidates across 4 dimensions
     d. Generates explanations via LLM
  4. Ranked results returned to dashboard with explainability
```

---

## 🧠 How Scoring Works

Every candidate is scored across **4 weighted dimensions**:

| Dimension | Weight | What It Measures |
|-----------|--------|------------------|
| **Semantic Score** | 40% | Vector similarity between candidate profile/resume and JD using transformer embeddings |
| **Experience Score** | 25% | Years of experience fit, role seniority alignment, career trajectory |
| **Behavioral Score** | 20% | Profile activity, recency of updates, community engagement signals |
| **Context Score** | 15% | Location match, industry overlap, education relevance |

```
Final Score = (0.40 × Semantic) + (0.25 × Experience) + (0.20 × Behavioral) + (0.15 × Context)
```

Each candidate receives a **natural-language explanation** of their ranking — no black boxes.

---

## ⚡ Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/HARSH-KHEM/intelligent-candidate-discovery.git
cd intelligent-candidate-discovery

# Set up environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

# Launch everything
docker-compose up --build
```

That's it. Open:
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

### Option 2: Manual Setup

```bash
# Prerequisites: Python 3.11+, Node.js 18+, MongoDB 7.0

# 1. Generate sample data
cd data && python3 generate_sample_data.py && cd ..

# 2. Start ML service
cd ml && pip install -r requirements.txt && python3 -m uvicorn main:app --port 8001 &

# 3. Start backend
cd backend && pip install -r requirements.txt && python3 -m uvicorn main:app --port 8000 &

# 4. Start frontend
cd frontend && npm install && npm start
```

### Option 3: One-Command Evaluation

```bash
# Run the full pipeline on sample data
./scripts/run_evaluation.sh
```

---

## 📊 Sample Results

Running the pipeline on 500 synthetic candidates against a **Senior Backend Engineer** JD:

| Rank | Candidate | Final Score | Semantic | Experience | Behavioral | Context | Key Insight |
|------|-----------|-------------|----------|------------|------------|---------|-------------|
| 1 | CID-0161 | 0.6497 | 0.37 | 1.00 | 0.67 | 0.79 | 6y exp, ideal range match |
| 2 | CID-0425 | 0.6290 | 0.17 | 1.00 | 0.92 | 0.85 | Highly active, Bengaluru |
| 3 | CID-0006 | 0.6210 | 0.19 | 0.97 | 0.97 | 0.71 | 7y exp, very active profile |
| 4 | CID-0482 | 0.6178 | 0.27 | 1.00 | 0.84 | 0.62 | 6y exp, strong engagement |
| 5 | CID-0194 | 0.6177 | 0.29 | 0.66 | 0.93 | 1.00 | 12y senior, perfect context |

> Full ranked output: [`data/sample_output.csv`](data/sample_output.csv) (500 candidates)

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **ML/AI** | Python, sentence-transformers, FAISS, OpenAI GPT-4o | Embeddings, vector search, scoring, explanations |
| **Backend** | FastAPI, Pydantic, Motor (async MongoDB) | REST API, validation, data access |
| **Frontend** | React 18, Axios, Recharts | Dashboard, JD upload, results visualization |
| **Database** | MongoDB 7.0 | Candidate profiles, job descriptions, results |
| **Infrastructure** | Docker, Docker Compose | Container orchestration, one-command deployment |

---

## 📁 Project Structure

```
intelligent-candidate-discovery/
├── ml/                          # ML scoring service
│   ├── embeddings.py            # Sentence-transformer embeddings
│   ├── faiss_index.py           # FAISS vector index management
│   ├── scorer.py                # 4-dimension scoring engine
│   ├── reranker.py              # Re-ranking with LLM explanations
│   ├── pipeline.py              # End-to-end ranking pipeline
│   ├── output_formatter.py      # CSV/JSON output formatting
│   ├── requirements.txt
│   └── Dockerfile
├── backend/                     # FastAPI backend
│   ├── main.py                  # API entrypoint
│   ├── routers/                 # API route handlers
│   ├── models/                  # Pydantic data models
│   ├── db/                      # MongoDB connection & queries
│   ├── services/                # Business logic
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                    # React dashboard
│   ├── src/
│   │   ├── pages/               # Page components
│   │   ├── components/          # Reusable UI components
│   │   └── services/            # API client
│   └── Dockerfile
├── data/                        # Sample data & outputs
│   ├── generate_sample_data.py  # Synthetic candidate generator
│   ├── generate_sample_output.py# Pre-generate ranked output
│   ├── sample_jd.txt            # Sample job description
│   ├── sample_output.csv        # Pre-generated ranked results
│   ├── candidates.json          # Generated candidate profiles
│   └── candidates.csv           # Generated profiles (CSV)
├── scripts/
│   └── run_evaluation.sh        # One-command evaluation
├── docs/
│   ├── linkedin_post.txt        # Social media post
│   └── linkedin_article.md      # LinkedIn article
├── docker-compose.yml           # Service orchestration
├── .env.example                 # Environment template
└── README.md                    # This file
```

---

## 🔒 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGODB_URI` | MongoDB connection string | `mongodb://mongodb:27017/candidate_discovery` |
| `OPENAI_API_KEY` | OpenAI API key for embeddings & explanations | — (required) |
| `MODEL_NAME` | LLM model for explanations | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Embedding model name | `text-embedding-3-small` |
| `WEIGHT_SEMANTIC` | Semantic score weight | `0.40` |
| `WEIGHT_EXPERIENCE` | Experience score weight | `0.25` |
| `WEIGHT_BEHAVIORAL` | Behavioral score weight | `0.20` |
| `WEIGHT_CONTEXT` | Context score weight | `0.15` |

See [`.env.example`](.env.example) for the full list.

---

## 🧪 Evaluation

```bash
# Generate synthetic data
python3 data/generate_sample_data.py

# Generate pre-computed rankings (no API key needed)
python3 data/generate_sample_output.py

# Run full pipeline with Docker
./scripts/run_evaluation.sh
```

---

## 👥 Team

| Role | Contributor |
|------|------------|
| **Agent 1** | ML Pipeline — Embeddings, FAISS, Scoring Engine |
| **Agent 2** | Backend — FastAPI, MongoDB, REST APIs |
| **Agent 3** | Frontend — React Dashboard, Visualizations |
| **Agent 4** | Data Prep, DevOps, Docker, Documentation |

Built for the **INDIA RUNS Hackathon** on [Hack2Skill](https://hack2skill.com) — Track 01: Data & AI Challenge.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>Built with ❤️ at INDIA RUNS Hackathon 2026</strong>
</p>
