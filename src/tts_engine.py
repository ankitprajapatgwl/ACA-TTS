"""
Shared model-loading and generation core for ai4bharat/indic-parler-tts.

Imported by both handler_direct.py and handler_streaming.py so the two
RunPod endpoints never duplicate model-loading or generation logic --
the only difference between them is response shape/timing (see the
handler files).
"""

import io

import numpy as np
import soundfile as sf
import torch
from parler_tts import ParlerTTSForConditionalGeneration
from transformers import AutoTokenizer

MODEL_NAME = "ai4bharat/indic-parler-tts"


def load_model():
    """
    Load the model and both tokenizers once. Relies on HF_HOME (set at
    Docker build time) already containing the cached weights, and on
    HF_HUB_OFFLINE=1 (set at runtime) to guarantee this never reaches out
    to the network -- it fails fast if a file is missing rather than
    silently downloading it.

    Returns (model, tokenizer, description_tokenizer, sampling_rate, device).
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"

    model = ParlerTTSForConditionalGeneration.from_pretrained(MODEL_NAME).to(device)
    model.eval()

    # Tokenizer for the TEXT PROMPT (what is spoken).
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    # Tokenizer for the DESCRIPTION (voice characteristics) -- separate
    # from the prompt tokenizer per the model card. Using one tokenizer
    # for both silently degrades quality.
    description_tokenizer = AutoTokenizer.from_pretrained(
        model.config.text_encoder._name_or_path
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
