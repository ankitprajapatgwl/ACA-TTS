# RunPod base image: CUDA + PyTorch + Python already set up, so we only
# need to add our own dependencies and the model weights on top.
FROM runpod/pytorch:2.4.0-py3.11-cuda12.4.1-devel-ubuntu22.04

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Fixed cache path, set BEFORE the build-time download step below, so the
# same path is used to populate the cache at build time and to read from
# it at runtime -- this is what lets weights be baked into the image layer
# instead of re-downloaded on every worker start.
ENV HF_HOME=/app/hf_cache \
    TRANSFORMERS_CACHE=/app/hf_cache

# git is required for the parler_tts git+https install below. ffmpeg is
# NOT needed: soundfile reads/writes WAV via bundled libsndfile, not ffmpeg.
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY handler.py .

# The model + its flan-t5-large description encoder together are a real
# multi-GB download, against RunPod's documented 30-minute build timeout --
# hf_transfer's Rust-based downloader is enabled just for this step to stay
# well inside that budget.
ENV HF_HUB_ENABLE_HF_TRANSFER=1

# Download the model + both tokenizers ONCE, at build time, into HF_HOME.
# This layer is cached in the final image, so no worker ever downloads
# weights again at cold start or per-request.
RUN python -c "\
from parler_tts import ParlerTTSForConditionalGeneration; \
from transformers import AutoTokenizer; \
model = ParlerTTSForConditionalGeneration.from_pretrained('ai4bharat/indic-parler-tts'); \
AutoTokenizer.from_pretrained('ai4bharat/indic-parler-tts'); \
AutoTokenizer.from_pretrained(model.config.text_encoder._name_or_path); \
print('Model and tokenizers cached at build time.')"

# From here on (i.e. at runtime, once the image is built), forbid any
# network call to Hugging Face. This both prevents accidental
# re-downloads and makes a missing file fail loudly instead of silently
# re-fetching it.
ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1

# Per-endpoint switch: each RunPod endpoint built from this same repo sets
# its own HANDLER_TYPE env var (direct | streaming). handler.py reads it
# and picks the right handler in Python.
ENV HANDLER_TYPE=direct

# A single, static exec-form CMD pointing at one file -- unlike a shell
# `if/then/else` CMD, this is trivially resolvable by RunPod's deploy-time
# check for runpod.serverless.start(), which handler.py always calls.
CMD ["python", "-u", "handler.py"]
