"""
Shared model-loading and generation core for ai4bharat/indic-parler-tts.

Imported by both handler_direct.py and handler_streaming.py so the two
RunPod endpoints never duplicate model-loading or generation logic --
the only difference between them is response shape/timing (see the
handler files).
"""

import io
import os

# ai4bharat/indic-parler-tts is a gated Hugging Face model (requires
# accepting its terms + an access token). RunPod's GitHub-integration
# Docker build has no way to inject that token into the build step, so
# the model can't be baked into the image at build time -- it's instead
# downloaded on first use, authenticated with HF_TOKEN (an endpoint-level
# runtime env var, never baked into the image, per RunPod's own guidance
# on handling secrets). HF_HOME must be set before transformers/parler_tts
# are imported, since huggingface_hub reads it once at import time.
#
# If a RunPod network volume is attached (mounted at /runpod-volume), the
# cache lives there so the download happens once total, not once per
# worker; otherwise it falls back to local (ephemeral) container storage.
if os.path.isdir("/runpod-volume"):
    os.environ["HF_HOME"] = "/runpod-volume/huggingface-cache"
else:
    os.environ["HF_HOME"] = "/app/hf_cache"
os.environ["TRANSFORMERS_CACHE"] = os.environ["HF_HOME"]

import numpy as np
import soundfile as sf
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL_NAME = "ai4bharat/indic-parler-tts"


def load_model():
    """
    Load the model and both tokenizers once. Authenticates with HF_TOKEN
    (required -- see module docstring) and downloads on first use if not
    already present under HF_HOME, then reuses the cache on every
    subsequent load.

    Returns (model, tokenizer, description_tokenizer, sampling_rate, device).
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    hf_token = os.environ.get("HF_TOKEN")

    model = ParlerTTSForConditionalGeneration.from_pretrained(
        MODEL_NAME, token=hf_token
    ).to(device)
    model.eval()

    # Tokenizer for the TEXT PROMPT (what is spoken).
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, token=hf_token)

    # Tokenizer for the DESCRIPTION (voice characteristics) -- separate
    # from the prompt tokenizer per the model card. Using one tokenizer
    # for both silently degrades quality.
    description_tokenizer = AutoTokenizer.from_pretrained(
        model.config.text_encoder._name_or_path, token=hf_token
    )

    # Read the real sampling rate from the model config instead of
    # hardcoding 24000, so it stays correct if the model config changes.
    sampling_rate = model.config.sampling_rate

    return model, tokenizer, description_tokenizer, sampling_rate, device


def synthesize(model, tokenizer, description_tokenizer, prompt: str, description: str):
    """
    Run the dual-tokenizer generation call. Returns (audio_array, sampling_rate).
    """
    device = model.device

    description_input_ids = description_tokenizer(description, return_tensors="pt").to(device)
    prompt_input_ids = tokenizer(prompt, return_tensors="pt").to(device)

    with torch.no_grad():
        generation = model.generate(
            input_ids=description_input_ids.input_ids,
            attention_mask=description_input_ids.attention_mask,
            prompt_input_ids=prompt_input_ids.input_ids,
            prompt_attention_mask=prompt_input_ids.attention_mask,
        )

    audio_arr = generation.cpu().numpy().squeeze()
    return audio_arr, model.config.sampling_rate


def audio_array_to_wav_bytes(audio_arr: np.ndarray, sampling_rate: int) -> bytes:
    """Encode a numpy audio array to in-memory WAV bytes via soundfile."""
    buffer = io.BytesIO()
    sf.write(buffer, audio_arr, sampling_rate, format="WAV")
    return buffer.getvalue()
