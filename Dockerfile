# syntax=docker/dockerfile:1

FROM nvidia/cuda:12.6.0-cudnn-runtime-ubuntu24.04 AS base

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/models/hf \
    TRANSFORMERS_CACHE=/models/hf \
    HF_HUB_DISABLE_TELEMETRY=1 \
    LLM_MODEL_ID=Qwen/Qwen2.5-3B-Instruct

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-venv \
    python3-pip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3 /usr/local/bin/python

ENV VIRTUAL_ENV=/opt/venv
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install \
        --index-url https://pypi.org/simple \
        --extra-index-url https://download.pytorch.org/whl/cu126 \
        -r requirements.txt

COPY app/__init__.py app/__init__.py
COPY app/config app/config
COPY app/utils/logging.py app/utils/logging.py
COPY app/utils/__init__.py app/utils/__init__.py
COPY download_models.py .
RUN --mount=type=secret,id=HF_TOKEN python download_models.py

COPY app/ app/
COPY kyc_handler.py handler.py llm_handler.py start_kyc.sh start.sh start_llm.sh ./
RUN chmod +x start_kyc.sh start.sh start_llm.sh

CMD ["./start_kyc.sh"]
