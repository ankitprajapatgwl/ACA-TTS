"""
RunPod Serverless direct handler for ai4bharat/indic-parler-tts.

Waits for generation to finish and returns one complete JSON response
containing the full WAV as base64. Selected via HANDLER_TYPE=direct
(the Dockerfile default) -- see Dockerfile CMD.
"""

import base64
import logging

import runpod

import tts_engine
import voice_presets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("handler_direct")

# Loaded once at import time so the model stays resident in GPU memory
# across invocations on the same warm worker.
MODEL, TOKENIZER, DESCRIPTION_TOKENIZER, SAMPLING_RATE, DEVICE = tts_engine.load_model()
logger.info("Model loaded on %s, sampling_rate=%s", DEVICE, SAMPLING_RATE)


def handler_direct(job):
    job_input = job.get("input") or {}

    try:
        error = voice_presets.validate_input(job_input)
        if error:
            return {"error": error, "endpoint_type": "direct"}

        text = job_input["text"]
        preset_key = job_input.get("preset_key")
        custom_description = job_input.get("custom_description")
        speed = job_input.get("speed", "normal")

        description = voice_presets.get_description(preset_key, custom_description)
        description = voice_presets.apply_speed_hint(description, speed)

        if custom_description:
            speaker, language, resolved_preset_key = "custom", "unspecified", preset_key
        else:
            preset_info = voice_presets.get_preset_info(preset_key)
            speaker, language = preset_info["speaker"], preset_info["language"]
            resolved_preset_key = preset_key if preset_key in voice_presets.PRESETS else voice_presets.DEFAULT_PRESET_KEY

        audio_arr, sampling_rate = tts_engine.synthesize(
            MODEL, TOKENIZER, DESCRIPTION_TOKENIZER, text, description
        )
        wav_bytes = tts_engine.audio_array_to_wav_bytes(audio_arr, sampling_rate)
        audio_base64 = base64.b64encode(wav_bytes).decode("utf-8")

        return {
            "audio_base64": audio_base64,
            "format": "wav",
            "sample_rate": sampling_rate,
            "text": text,
            "preset_key": resolved_preset_key,
            "speaker": speaker,
            "language": language,
            "endpoint_type": "direct",
        }
    except Exception as exc:
        logger.exception("Direct handler failed")
        return {"error": str(exc), "endpoint_type": "direct"}


if __name__ == "__main__":
    # Standalone/local-testing entrypoint (`python src/handler_direct.py`).
    # The container's actual entrypoint is the root-level handler.py, which
    # imports handler_direct without triggering this block.
    runpod.serverless.start({"handler": handler_direct})
