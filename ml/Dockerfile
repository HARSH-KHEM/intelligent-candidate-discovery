FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY ml/ ./ml/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "ml.pipeline:app", "--host", "0.0.0.0", "--port", "8001"]
