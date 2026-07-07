# syntax=docker/dockerfile:1

FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    HF_HUB_DISABLE_TELEMETRY=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/local/bin/python

# Use a virtual environment to avoid PEP 668 (externally-managed-environment).
ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

# Install Python dependencies with layer caching
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install \
        --index-url https://pypi.org/simple \
        --extra-index-url https://download.pytorch.org/whl/cu126 \
        -r requirements.txt

# Download model at build time (never at runtime)
COPY app/__init__.py app/__init__.py
COPY app/config app/config
COPY app/utils/logging.py app/utils/logging.py
COPY app/utils/__init__.py app/utils/__init__.py
COPY download_model.py .
RUN --mount=type=secret,id=HF_TOKEN python download_model.py

# Copy application code
COPY app/ app/
COPY handler.py start.sh ./
RUN chmod +x start.sh

CMD ["./start.sh"]
