# RunPod base image: CUDA + PyTorch + Python already set up, so we only
# need to add our own dependencies and the model weights on top.
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# git is required for the parler_tts git+https install below. ffmpeg is
# NOT needed: soundfile reads/writes WAV via bundled libsndfile, not ffmpeg.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY handler.py .

# ai4bharat/indic-parler-tts is a gated Hugging Face model -- downloading
# it requires an authenticated HF_TOKEN, which RunPod's GitHub-integration
# build has no way to inject into this build step. So the model is NOT
# downloaded here at build time; src/tts_engine.py downloads it on first
# use instead, authenticated with HF_TOKEN set as a RunPod endpoint
# environment variable (injected at runtime only, never baked into the
# image -- see README's Model caching section). hf_transfer speeds up
# that first-use download.
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# Per-endpoint switch: each RunPod endpoint built from this same repo sets
# its own HANDLER_TYPE env var (direct | streaming). handler.py reads it
# and picks the right handler in Python.
ENV HANDLER_TYPE=direct

# A single, static exec-form CMD pointing at one file -- unlike a shell
# `if/then/else` CMD, this is trivially resolvable by RunPod's deploy-time
# check for runpod.serverless.start(), which handler.py always calls.
CMD ["python", "-u", "handler.py"]
