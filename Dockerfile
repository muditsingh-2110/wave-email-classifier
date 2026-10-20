# ── Wave Email Classifier - Dockerfile ───────────────────────────────────────
# Base image: official Python 3.11 slim (small, production-safe)
FROM python:3.11-slim

# Set working directory inside the container
WORKDIR /app

# Copy dependency file first (Docker layer cache — faster rebuilds)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all app files into the container
COPY . .

# Expose the port Flask runs on
EXPOSE 5000

# Start the Flask app
CMD ["python", "api.py"]
