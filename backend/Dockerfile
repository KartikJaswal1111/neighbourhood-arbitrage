# ── Stage: runtime ────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# Install Python deps first so this layer is cached on code changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Use .env.example as the default config inside the container
# (docker-compose environment: block overrides these at runtime)
RUN cp .env.example .env

EXPOSE 8000

# Seed the DB with demo data, then start the API server
CMD ["sh", "-c", "python seed_data.py && uvicorn main:app --host 0.0.0.0 --port 8000 --reload"]
