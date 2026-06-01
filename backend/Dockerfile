FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY backend/requirements.txt backend-reqs.txt
COPY ml/requirements.txt ml-reqs.txt
RUN pip install --no-cache-dir -r backend-reqs.txt -r ml-reqs.txt

# Copy source code
COPY backend/ ./backend/
COPY ml/ ./ml/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
