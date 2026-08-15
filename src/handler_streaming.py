"""
RunPod Serverless streaming handler for ai4bharat/indic-parler-tts.

A generator handler (yields, never returns) so a client can start
consuming audio chunks before the full response is assembled. Selected
via HANDLER_TYPE=streaming -- see Dockerfile CMD.

Note: the underlying model call is not itself incremental -- generation
runs once via the same tts_engine.synthesize() used by handler_direct.py,
and the resulting WAV bytes are then split into sequential chunks for
progressive delivery over RunPod's generator/streaming transport.
"""

import base64
import logging

import runpod

import tts_engine
import voice_presets

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("handler_streaming")

DEFAULT_CHUNK_SIZE_KB = 256

# Loaded once at import time so the model stays resident in GPU memory
# across invocations on the same warm worker.
MODEL, TOKENIZER, DESCRIPTION_TOKENIZER, SAMPLING_RATE, DEVICE = tts_engine.load_model()
logger.info("Model loaded on %s, sampling_rate=%s", DEVICE, SAMPLING_RATE)


def handler_streaming(job):
    job_input = job.get("input") or {}

    error = voice_presets.validate_input(job_input)
    if error:
        yield {"error": error, "endpoint_type": "streaming"}
        return

    text = job_input["text"]
    preset_key = job_input.get("preset_key")
    custom_description = job_input.get("custom_description")
    speed = job_input.get("speed", "normal")
    chunk_size_kb = job_input.get("chunk_size_kb", DEFAULT_CHUNK_SIZE_KB)

    if custom_description:
        speaker, language, resolved_preset_key = "custom", "unspecified", preset_key
    else:
        preset_info = voice_presets.get_preset_info(preset_key)
        speaker, language = preset_info["speaker"], preset_info["language"]
        resolved_preset_key = preset_key if preset_key in voice_presets.PRESETS else voice_presets.DEFAULT_PRESET_KEY

    # Let the client know the job accepted its parameters before
    # generation (which can take a while) completes.
    yield {
        "status": "generating",
        "text": text,
        "preset_key": resolved_preset_key,
        "speaker": speaker,
        "language": language,
        "endpoint_type": "streaming",
    }

    try:
        description = voice_presets.get_description(preset_key, custom_description)
        description = voice_presets.apply_speed_hint(description, speed)

        audio_arr, sampling_rate = tts_engine.synthesize(
            MODEL, TOKENIZER, DESCRIPTION_TOKENIZER, text, description
        )
        wav_bytes = tts_engine.audio_array_to_wav_bytes(audio_arr, sampling_rate)
    except Exception as exc:
        logger.exception("Streaming handler failed during generation")
        yield {"error": str(exc), "endpoint_type": "streaming"}
        return

    chunk_size_bytes = max(1, int(chunk_size_kb) * 1024)
    total_bytes = len(wav_bytes)
    total_chunks = max(1, (total_bytes + chunk_size_bytes - 1) // chunk_size_bytes)

    for chunk_index in range(total_chunks):
        start = chunk_index * chunk_size_bytes
        end = min(start + chunk_size_bytes, total_bytes)
        chunk = wav_bytes[start:end]

        yield {
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunk_size_bytes": len(chunk),
            "audio_chunk_base64": base64.b64encode(chunk).decode("utf-8"),
            "progress_percent": round(((chunk_index + 1) / total_chunks) * 100, 2),
            "endpoint_type": "streaming",
        }

    yield {
        "status": "completed",
        "total_audio_bytes": total_bytes,
        "chunks_sent": total_chunks,
        "sample_rate": sampling_rate,
        "endpoint_type": "streaming",
    }


runpod.serverless.start({
    "handler": handler_streaming,
    "return_aggregate_stream": True,
})
