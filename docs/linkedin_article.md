# How We Built an AI That Ranks Candidates Better Than Keywords

## The Problem Nobody Talks About

Every recruiter knows the pain. You post a job for "Senior Backend Engineer" and get 400 applications. Your ATS filters by keywords — "Python," "Docker," "Kubernetes" — and spits out 80 resumes. But here's the dirty secret: **keyword matching misses great candidates and promotes résumé stuffers.**

A candidate who writes "containerized microservices" instead of "Docker" gets filtered out. Someone who spent three years architecting distributed systems at a startup — but never listed "Kubernetes" on their profile — never makes it past the first screen.

We set out to fix this at the **INDIA RUNS hackathon**.

## Our Approach: Semantic Understanding Over String Matching

Instead of matching strings, we match *meaning*. Our system, **Intelligent Candidate Discovery**, uses transformer-based language models to convert both job descriptions and candidate profiles into high-dimensional vector embeddings.

When a hiring manager uploads a JD, we don't search for keywords. We compute the semantic distance between the JD and every candidate in the database using FAISS (Facebook AI Similarity Search). A candidate who describes "building event-driven data pipelines on AWS" is correctly matched to a JD asking for "distributed backend systems on cloud infrastructure" — even though they share almost no keywords.

But semantic similarity alone isn't enough.

## The Four-Dimensional Scoring Engine

We realized that a great hire isn't just about skills on paper. Our system scores candidates across four dimensions:

1. **Semantic Score (40%)** — How closely does the candidate's experience match the JD's requirements at a meaning level?
2. **Experience Score (25%)** — Does their career trajectory (years, seniority, industry) align with the role?
3. **Behavioral Score (20%)** — Are they actively engaged? Do they update their profile, contribute to communities, or show learning signals?
4. **Context Score (15%)** — Location fit, industry overlap, education relevance, and other contextual factors.

Each candidate receives a weighted final score between 0 and 1, along with a **natural-language explanation** of why they ranked where they did. No black boxes.

## The Tech Stack

We built the entire platform in 27 days:

- **ML Layer**: Python, sentence-transformers, FAISS, OpenAI GPT-4o for explanation generation
- **Backend**: FastAPI serving REST APIs, MongoDB for candidate storage
- **Frontend**: React dashboard for hiring managers to upload JDs, view rankings, and read explanations
- **Infrastructure**: Docker Compose for one-command deployment, with all services on a shared network

The system processes 500 candidates in under 10 seconds and returns a ranked, explainable shortlist.

## Key Learnings

**1. Embeddings are powerful but not sufficient.** Pure vector similarity over-indexes on language style. Adding structured scoring dimensions (experience, behavior) dramatically improved result quality.

**2. Explainability is non-negotiable.** Hiring managers won't trust a score without a reason. Generating per-candidate explanations using an LLM turned our tool from a demo into something people actually wanted to use.

**3. Synthetic data is an underrated superpower.** We generated 500 realistic candidate profiles with varied backgrounds, skill distributions, and career stages. This let us test edge cases and validate scoring fairness before going near real data.

## What's Next

We're exploring fine-tuning domain-specific embedding models for different industries, adding bias detection dashboards, and integrating with existing ATS platforms via APIs.

The future of recruiting isn't about better keyword filters. It's about systems that understand people the way a great recruiter does — but at scale, in seconds, and without unconscious bias.

---

*Built at the INDIA RUNS Hackathon on Hack2Skill. Proud of what our team accomplished.*

*#IndiaRuns #AI #Hackathon #Hiring #NLP #MachineLearning*
