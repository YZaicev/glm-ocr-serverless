# syntax=docker/dockerfile:1

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    HF_HUB_DISABLE_TELEMETRY=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.12 \
    python3.12-venv \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.12 /usr/local/bin/python

WORKDIR /app

# Install Python dependencies with layer caching
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install torch --index-url https://download.pytorch.org/whl/cu124 \
    && python -m pip install -r requirements.txt

# Download model at build time (never at runtime)
COPY app/__init__.py app/__init__.py
COPY app/config app/config
COPY app/utils/logging.py app/utils/logging.py
COPY app/utils/__init__.py app/utils/__init__.py
COPY download_model.py .
RUN python download_model.py

# Copy application code
COPY app/ app/
COPY handler.py start.sh ./
RUN chmod +x start.sh

CMD ["./start.sh"]
