#!/usr/bin/env python3
"""
generate_sample_data.py — Generates 500 realistic synthetic candidate profiles.
Output: data/candidates.json (for MongoDB import) + data/candidates.csv
"""

import json
import csv
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ─── Configuration ───────────────────────────────────────────

NUM_CANDIDATES = 500
OUTPUT_DIR = Path(__file__).parent
SEED = 42

random.seed(SEED)

# ─── Data Pools ──────────────────────────────────────────────

FIRST_NAMES = [
    "Aarav", "Aditi", "Aditya", "Akshay", "Amita", "Ananya", "Arjun", "Arushi",
    "Bhavya", "Chetan", "Deepika", "Devesh", "Diya", "Esha", "Gaurav", "Harini",
    "Harsh", "Ishaan", "Isha", "Jatin", "Kavya", "Kiran", "Kriti", "Lakshmi",
    "Manish", "Meera", "Mohit", "Nandini", "Naveen", "Neha", "Nikhil", "Nisha",
    "Omkar", "Pallavi", "Prateek", "Priya", "Rahul", "Rajesh", "Ramya", "Ravi",
    "Ritika", "Rohit", "Sakshi", "Sameer", "Sandeep", "Shreya", "Sneha", "Sonia",
    "Suresh", "Tanvi", "Varun", "Vidya", "Vikram", "Vinay", "Yash", "Zara",
    "Anil", "Anjali", "Ashwin", "Divya", "Gaurav", "Hemanth", "Jaya", "Karthik",
    "Lavanya", "Madhav", "Nayan", "Pooja", "Rakesh", "Sahil", "Trisha", "Uma",
]

LAST_NAMES = [
    "Agarwal", "Bansal", "Chakraborty", "Desai", "Dutta", "Gupta", "Iyer",
    "Jain", "Joshi", "Kapoor", "Khan", "Kumar", "Malhotra", "Mehta", "Mishra",
    "Nair", "Pandey", "Patel", "Raj", "Rao", "Reddy", "Shah", "Sharma",
    "Singh", "Srinivasan", "Tiwari", "Verma", "Yadav", "Bhat", "Chopra",
    "Goyal", "Hegde", "Kulkarni", "Menon", "Mukherjee", "Naidu", "Pillai",
    "Rajan", "Saxena", "Thakur",
]

SKILLS_POOL = {
    "backend": [
        "Python", "FastAPI", "Django", "Flask", "Go", "Golang", "Java",
        "Spring Boot", "Node.js", "Express.js", "REST APIs", "GraphQL",
        "gRPC", "Microservices", "API Design", "WebSockets",
    ],
    "databases": [
        "PostgreSQL", "MongoDB", "MySQL", "Redis", "Elasticsearch",
        "DynamoDB", "Cassandra", "SQLite", "Neo4j", "InfluxDB",
    ],
    "devops": [
        "Docker", "Kubernetes", "AWS", "GCP", "Azure", "Terraform",
        "CI/CD", "GitHub Actions", "Jenkins", "GitLab CI", "Ansible",
        "Linux", "Nginx", "Prometheus", "Grafana",
    ],
    "ml_data": [
        "Machine Learning", "TensorFlow", "PyTorch", "Scikit-learn",
        "NLP", "Pandas", "NumPy", "Data Pipelines", "Apache Spark",
        "Airflow", "MLOps", "Model Serving",
    ],
    "frontend": [
        "React", "TypeScript", "JavaScript", "Vue.js", "Angular",
        "Next.js", "HTML/CSS", "Tailwind CSS", "Redux",
    ],
    "general": [
        "Git", "Agile", "Scrum", "System Design", "Data Structures",
        "Algorithms", "Problem Solving", "Technical Writing",
        "Code Review", "Mentoring",
    ],
}

ROLES = [
    "Software Engineer", "Senior Software Engineer", "Backend Developer",
    "Senior Backend Developer", "Full Stack Developer", "Platform Engineer",
    "DevOps Engineer", "Senior DevOps Engineer", "Data Engineer",
    "ML Engineer", "Staff Engineer", "Principal Engineer",
    "Engineering Manager", "Tech Lead", "SDE-II", "SDE-III",
    "Solutions Architect", "Cloud Engineer", "Site Reliability Engineer",
    "Software Architect",
]

INDUSTRIES = [
    "Technology", "Fintech", "E-commerce", "Healthcare", "EdTech",
    "SaaS", "Consulting", "Banking", "Automotive", "Telecom",
    "Media", "Gaming", "Logistics", "Insurance", "Cybersecurity",
    "AI/ML", "IoT", "Enterprise Software", "Startup", "Government",
]

LOCATIONS = [
    "Bengaluru", "Hyderabad", "Mumbai", "Pune", "Delhi NCR",
    "Chennai", "Noida", "Gurgaon", "Kolkata", "Ahmedabad",
    "Jaipur", "Kochi", "Chandigarh", "Indore", "Lucknow",
    "Remote — India", "San Francisco, USA", "London, UK",
    "Singapore", "Dubai, UAE",
]

EDUCATION = [
    "B.Tech Computer Science — IIT Bombay",
    "B.Tech Computer Science — IIT Delhi",
    "B.Tech IT — NIT Trichy",
    "B.Tech ECE — NIT Warangal",
    "B.E. Computer Science — BITS Pilani",
    "M.Tech Computer Science — IISc Bangalore",
    "M.Tech AI — IIT Hyderabad",
    "B.Tech CSE — VIT Vellore",
    "B.Tech CSE — SRM University",
    "B.Tech CSE — IIIT Hyderabad",
    "BCA — Christ University",
    "MCA — Jawaharlal Nehru University",
    "B.Sc Computer Science — Delhi University",
    "M.S. Computer Science — Stanford University",
    "M.S. Computer Science — Carnegie Mellon University",
    "B.Tech CSE — DTU Delhi",
    "B.Tech CSE — NSUT Delhi",
    "B.E. IT — Pune University",
    "B.Tech CSE — Manipal Institute",
    "Self-taught / Bootcamp Graduate",
]

RESUME_TEMPLATES = [
    "Experienced {role} with {exp} years building {systems} at {company}. "
    "Proficient in {skill1}, {skill2}, and {skill3}. Led a team of {team} engineers "
    "to deliver {project}. Passionate about {passion}.",

    "Results-driven engineer specializing in {skill1} and {skill2} with {exp} years "
    "of experience in the {industry} industry. Built and scaled {systems} serving "
    "{users} users. Strong background in {skill3} and {skill4}.",

    "{exp}+ years of professional experience as a {role}. Core expertise in "
    "{skill1}, {skill2}, {skill3}. Contributed to open-source projects including "
    "{oss}. {education} graduate with a focus on {focus}.",

    "Senior {role} currently at {company} working on {project}. Tech stack: "
    "{skill1}, {skill2}, {skill3}, {skill4}. Previously at {prev_company} where "
    "I architected {systems}. {exp} years of experience across {industry} and tech.",

    "Full-stack engineer with deep backend expertise. {exp} years working with "
    "{skill1} and {skill2}. Designed event-driven architectures processing {events}/day. "
    "Mentored {team} junior developers. Active speaker at {conference}.",
]

COMPANIES = [
    "Google", "Microsoft", "Amazon", "Flipkart", "Razorpay", "Zerodha",
    "Swiggy", "Zomato", "Paytm", "PhonePe", "Freshworks", "Zoho",
    "Infosys", "TCS", "Wipro", "HCL", "Ola", "CRED", "Meesho",
    "Dream11", "Groww", "Slice", "Jupiter", "INDmoney", "Postman",
    "Atlassian", "Adobe", "Salesforce", "Oracle", "SAP",
    "a fast-growing Series B startup", "an early-stage fintech startup",
    "a Y Combinator-backed startup", "a leading SaaS company",
]

SYSTEMS = [
    "distributed microservices", "real-time data pipelines",
    "payment processing systems", "recommendation engines",
    "search infrastructure", "API gateways", "notification systems",
    "authentication services", "analytics dashboards",
    "inventory management platforms", "order processing systems",
    "CI/CD infrastructure", "monitoring and alerting systems",
]

OSS_PROJECTS = [
    "FastAPI", "Django", "Flask", "Kubernetes", "Prometheus",
    "TensorFlow", "Pandas", "Apache Kafka", "Redis", "Celery",
]

CONFERENCES = [
    "PyCon India", "JSConf", "GopherCon", "KubeCon", "AWS re:Invent",
    "Google I/O Extended", "local tech meetups", "DevOpsDays",
]

PASSIONS = [
    "scalable architecture", "developer experience", "open source",
    "clean code", "performance optimization", "system reliability",
    "data-driven decision making", "mentoring engineers",
]


def generate_skills(bias: str = "balanced") -> list[str]:
    """Generate a realistic skill set with optional domain bias."""
    skills = set()

    if bias == "backend_heavy":
        skills.update(random.sample(SKILLS_POOL["backend"], random.randint(4, 7)))
        skills.update(random.sample(SKILLS_POOL["databases"], random.randint(2, 4)))
        skills.update(random.sample(SKILLS_POOL["devops"], random.randint(2, 4)))
        skills.update(random.sample(SKILLS_POOL["general"], random.randint(1, 3)))
    elif bias == "ml_heavy":
        skills.update(random.sample(SKILLS_POOL["ml_data"], random.randint(4, 6)))
        skills.update(random.sample(SKILLS_POOL["backend"], random.randint(1, 3)))
        skills.update(random.sample(SKILLS_POOL["databases"], random.randint(1, 2)))
        skills.update(random.sample(SKILLS_POOL["general"], random.randint(1, 2)))
    elif bias == "devops_heavy":
        skills.update(random.sample(SKILLS_POOL["devops"], random.randint(5, 8)))
        skills.update(random.sample(SKILLS_POOL["backend"], random.randint(1, 3)))
        skills.update(random.sample(SKILLS_POOL["databases"], random.randint(1, 2)))
    elif bias == "frontend_heavy":
        skills.update(random.sample(SKILLS_POOL["frontend"], random.randint(4, 6)))
        skills.update(random.sample(SKILLS_POOL["backend"], random.randint(1, 2)))
        skills.update(random.sample(SKILLS_POOL["general"], random.randint(1, 3)))
    else:
        for category in SKILLS_POOL.values():
            skills.update(random.sample(category, random.randint(1, 3)))

    return sorted(skills)


def generate_resume_text(candidate: dict) -> str:
    """Generate a semi-realistic resume paragraph."""
    template = random.choice(RESUME_TEMPLATES)
    skills = candidate["skills"]

    placeholders = {
        "role": candidate["current_role"],
        "exp": str(candidate["years_experience"]),
        "skill1": skills[0] if len(skills) > 0 else "Python",
        "skill2": skills[1] if len(skills) > 1 else "Docker",
        "skill3": skills[2] if len(skills) > 2 else "PostgreSQL",
        "skill4": skills[3] if len(skills) > 3 else "Redis",
        "company": random.choice(COMPANIES),
        "prev_company": random.choice(COMPANIES),
        "industry": candidate["industry"],
        "systems": random.choice(SYSTEMS),
        "project": random.choice(SYSTEMS),
        "team": str(random.randint(3, 15)),
        "users": random.choice(["100K", "500K", "1M", "5M", "10M", "50M"]),
        "events": random.choice(["10K", "100K", "1M", "10M"]),
        "oss": random.choice(OSS_PROJECTS),
        "education": candidate["education"].split("—")[0].strip(),
        "focus": random.choice(["distributed systems", "AI/ML", "software engineering", "data science"]),
        "passion": random.choice(PASSIONS),
        "conference": random.choice(CONFERENCES),
    }

    text = template
    for key, value in placeholders.items():
        text = text.replace("{" + key + "}", value)

    return text


def generate_candidate(idx: int) -> dict:
    """Generate a single candidate profile."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)

    # Bias skill distribution for realism
    bias = random.choices(
        ["backend_heavy", "ml_heavy", "devops_heavy", "frontend_heavy", "balanced"],
        weights=[35, 15, 15, 15, 20],
        k=1,
    )[0]

    years_exp = random.choices(
        range(1, 21),
        weights=[3, 5, 7, 8, 10, 10, 9, 8, 7, 6, 5, 4, 4, 3, 3, 2, 2, 1, 1, 1],
        k=1,
    )[0]

    # Higher experience → higher activity score on average
    base_activity = min(random.gauss(0.5 + years_exp * 0.02, 0.15), 1.0)
    activity_score = round(max(0.05, min(1.0, base_activity)), 2)

    # Profile update date — more active candidates update more recently
    days_ago = int(random.expovariate(1 / (30 + (1 - activity_score) * 300)))
    days_ago = min(days_ago, 730)  # Cap at 2 years
    profile_date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")

    candidate = {
        "candidate_id": f"CID-{idx:04d}",
        "name": f"{first} {last}",
        "skills": [],
        "years_experience": years_exp,
        "current_role": random.choice(ROLES),
        "industry": random.choice(INDUSTRIES),
        "location": random.choice(LOCATIONS),
        "education": random.choice(EDUCATION),
        "activity_score": activity_score,
        "profile_updated_date": profile_date,
        "resume_text": "",
    }

    candidate["skills"] = generate_skills(bias)
    candidate["resume_text"] = generate_resume_text(candidate)

    return candidate


def main():
    print(f"🚀 Generating {NUM_CANDIDATES} synthetic candidate profiles...")

    candidates = [generate_candidate(i + 1) for i in range(NUM_CANDIDATES)]

    # Write JSON (for MongoDB import)
    json_path = OUTPUT_DIR / "candidates.json"
    with open(json_path, "w") as f:
        json.dump(candidates, f, indent=2, ensure_ascii=False)
    print(f"✅ JSON written to {json_path}")

    # Write CSV
    csv_path = OUTPUT_DIR / "candidates.csv"
    fieldnames = [
        "candidate_id", "name", "skills", "years_experience", "current_role",
        "industry", "location", "education", "activity_score",
        "profile_updated_date", "resume_text",
    ]
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for c in candidates:
            row = c.copy()
            row["skills"] = "; ".join(row["skills"])
            writer.writerow(row)
    print(f"✅ CSV written to {csv_path}")

    # Stats
    avg_skills = sum(len(c["skills"]) for c in candidates) / len(candidates)
    avg_exp = sum(c["years_experience"] for c in candidates) / len(candidates)
    print(f"\n📊 Stats:")
    print(f"   Candidates:    {len(candidates)}")
    print(f"   Avg skills:    {avg_skills:.1f}")
    print(f"   Avg experience: {avg_exp:.1f} years")
    print(f"   Locations:     {len(set(c['location'] for c in candidates))}")
    print(f"   Industries:    {len(set(c['industry'] for c in candidates))}")


if __name__ == "__main__":
    main()
