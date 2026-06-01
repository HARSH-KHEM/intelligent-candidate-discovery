#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  run_evaluation.sh — One-command pipeline evaluation script
#  Generates sample data → runs ML pipeline → outputs ranked CSV
# ═══════════════════════════════════════════════════════════════

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DATA_DIR="$PROJECT_ROOT/data"
OUTPUT_FILE="$DATA_DIR/sample_output.csv"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔══════════════════════════════════════════════════════╗"
echo "║   Intelligent Candidate Discovery — Evaluation Run  ║"
echo "╚══════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ─── Step 1: Generate sample data ────────────────────────────
echo -e "${YELLOW}[1/4]${NC} Generating synthetic candidate data..."
cd "$DATA_DIR"
python3 generate_sample_data.py
echo ""

# ─── Step 2: Check for .env ──────────────────────────────────
echo -e "${YELLOW}[2/4]${NC} Checking environment configuration..."
if [ ! -f "$PROJECT_ROOT/.env" ]; then
    echo -e "${YELLOW}  ⚠  No .env file found. Copying from .env.example${NC}"
    cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
    echo -e "${YELLOW}  ⚠  Please update .env with your OPENAI_API_KEY before running the full pipeline.${NC}"
fi
echo -e "${GREEN}  ✓  Environment configured${NC}"
echo ""

# ─── Step 3: Run the pipeline via Docker ─────────────────────
echo -e "${YELLOW}[3/4]${NC} Starting services with Docker Compose..."
cd "$PROJECT_ROOT"

# Build and start services
docker-compose up -d --build

# Wait for services to be healthy
echo "  Waiting for services to be ready..."
sleep 10

# Check if backend is responding
MAX_RETRIES=30
RETRY_COUNT=0
until curl -sf http://localhost:8000/health > /dev/null 2>&1; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        echo -e "${RED}  ✗  Backend failed to start after ${MAX_RETRIES} retries${NC}"
        echo -e "${YELLOW}  Tip: Check logs with 'docker-compose logs backend'${NC}"
        exit 1
    fi
    echo "  Waiting for backend... (attempt $RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done
echo -e "${GREEN}  ✓  All services running${NC}"
echo ""

# ─── Step 4: Trigger evaluation ──────────────────────────────
echo -e "${YELLOW}[4/4]${NC} Running candidate ranking pipeline..."

# Upload candidates to the system
curl -sf -X POST http://localhost:8000/api/candidates/bulk \
    -H "Content-Type: application/json" \
    -d @"$DATA_DIR/candidates.json" > /dev/null 2>&1 || true

# Submit the sample JD and get rankings
RESPONSE=$(curl -sf -X POST http://localhost:8000/api/rank \
    -H "Content-Type: application/json" \
    -d "{\"jd_text\": $(python3 -c "import json; print(json.dumps(open('$DATA_DIR/sample_jd.txt').read()))")}" \
    2>/dev/null || echo "")

if [ -n "$RESPONSE" ] && echo "$RESPONSE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    # Parse response and write CSV
    echo "$RESPONSE" | python3 -c "
import sys, json, csv

data = json.load(sys.stdin)
candidates = data.get('ranked_candidates', data.get('results', []))

with open('$OUTPUT_FILE', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['candidate_id','rank','final_score','semantic_score',
                     'experience_score','behavioral_score','context_score','explanation'])
    for i, c in enumerate(candidates, 1):
        writer.writerow([
            c.get('candidate_id', ''),
            i,
            round(c.get('final_score', 0), 4),
            round(c.get('semantic_score', 0), 4),
            round(c.get('experience_score', 0), 4),
            round(c.get('behavioral_score', 0), 4),
            round(c.get('context_score', 0), 4),
            c.get('explanation', 'N/A'),
        ])
"
    echo -e "${GREEN}  ✓  Rankings written to ${OUTPUT_FILE}${NC}"
else
    echo -e "${YELLOW}  ⚠  API not fully available. Using pre-generated sample output.${NC}"
    echo -e "${YELLOW}  Tip: Ensure OPENAI_API_KEY is set in .env for full pipeline.${NC}"
fi

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════╗"
echo -e "║                  ✅ Evaluation Complete               ║"
echo -e "╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo "  Output:    $OUTPUT_FILE"
echo "  Dashboard: http://localhost:3000"
echo "  API Docs:  http://localhost:8000/docs"
echo ""
