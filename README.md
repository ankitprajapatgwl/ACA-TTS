# Indic Parler-TTS — RunPod Serverless

Deploys [`ai4bharat/indic-parler-tts`](https://huggingface.co/ai4bharat/indic-parler-tts)
as a RunPod Serverless worker, built and deployed straight from this
GitHub repository (RunPod's GitHub Repo integration — no manual Docker
build/push).

One repo, one Dockerfile, **two RunPod endpoints**:

| Endpoint | Handler function | Behavior |
|---|---|---|
| **Direct** | `src/handler_direct.py` | Waits for generation, returns one complete JSON response with the full WAV as base64. |
| **Streaming** | `src/handler_streaming.py` | Generator handler — yields a status object, then sequential base64 audio chunks, then a completion object. |

Both endpoints share the same model-loading and generation code
(`src/tts_engine.py`) and the same voice preset system
(`src/voice_presets.py`); only response shape/timing differs. Which
handler a given RunPod endpoint runs is selected purely by the
`HANDLER_TYPE` environment variable set on that endpoint (`direct` or
`streaming`) — see [Deploying two endpoints](#deploying-two-endpoints-from-one-repo).

The container's actual entrypoint is the single root-level `handler.py`.
It reads `HANDLER_TYPE` and imports the matching handler module, and it's
the one place `runpod.serverless.start()` is called inside the built
image. This exists specifically so RunPod's GitHub deploy-time check has
one static file to resolve: a Dockerfile `CMD` that shell-branches
between two files (`if [ "$HANDLER_TYPE" = ... ]`) gives that check
nothing concrete to point at, which can surface as a false
"`runpod.serverless.start()` handler not found" error even though the
call exists in the repo. `src/handler_direct.py` and
`src/handler_streaming.py` each still call `runpod.serverless.start()`
themselves too, guarded behind `if __name__ == "__main__":`, so either
can also be run standalone for local testing
(`python src/handler_direct.py test_input_direct.json`).

Input/output is JSON. Voices are selected via a small **preset system**
built only from the model's real, official named speakers (see
[Voice presets](#voice-presets)), or fully overridden with a custom
description string.

---

## Correct model usage

Indic Parler-TTS requires **two separate tokenizers**: one for the
spoken text (`prompt`), one for the voice `description`. Using a single
shared tokenizer for both silently degrades output quality. `tts_engine.py`
implements the official dual-tokenizer call:

```python
description_input_ids = description_tokenizer(description, return_tensors="pt").to(device)
prompt_input_ids = tokenizer(prompt, return_tensors="pt").to(device)

generation = model.generate(
    input_ids=description_input_ids.input_ids,
    attention_mask=description_input_ids.attention_mask,
    prompt_input_ids=prompt_input_ids.input_ids,
    prompt_attention_mask=prompt_input_ids.attention_mask,
)
```

Notes carried through from the official model card:

- The model auto-detects spoken language from the `prompt` text itself.
- Naming a **real, official speaker** in the description (e.g. "Divya's
  voice is...") gives consistent, repeatable results. Inventing a name
  does not.
- `"very clear audio"` in a description asks for high-quality, low-noise
  output; `"very noisy audio"` intentionally adds background noise.
- Punctuation (commas) in the prompt text controls natural pausing.
- Never prepend nationality/accent words before a *named* speaker (e.g.
  don't say "an Indian Divya") — that can destabilize the voice. Accent
  customization is only for generic, unnamed speaker descriptions.
- The actual output sample rate is always read from
  `model.config.sampling_rate` at load time (never hardcoded), and that
  same value is reused in both handlers' responses.

---

## Voice presets

`src/voice_presets.py` is a data-driven preset table. Every preset uses a
**real, official speaker name** from the model card's 18 officially
supported languages — no invented personas. For a given preset key, the
exact same description string is sent to the model on every request,
which is what guarantees a repeatable voice/tone across calls.

There is at least one preset per officially-supported language that has
published speaker names, plus 2–4 pace/tone variants for the most
commonly used languages (Hindi, English, Bengali, Marathi, Tamil, Telugu).

> Kashmiri is mentioned on the model card as unofficially supported, but
> no named speakers are published for it, so no preset exists for it here
> (inventing a name is explicitly out of scope). Chhattisgarhi and
> Punjabi are also unofficially supported but *do* have published
> speaker names, so they have presets.

| `preset_key` | Language | Speaker |
|---|---|---|
| `assamese_male_narrator` | Assamese | Amit |
| `bengali_male_narrator` | Bengali | Arjun |
| `bengali_female_narrator` | Bengali | Aditi |
| `bengali_male_casual` | Bengali | Tapan |
| `bengali_female_formal` | Bengali | Rashmi |
| `bodo_male_narrator` | Bodo | Bikram |
| `chhattisgarhi_male_narrator` | Chhattisgarhi | Bhanu |
| `dogri_male_narrator` | Dogri | Karan |
| `english_male_narrator` | English | Thoma |
| `english_female_narrator` | English | Mary |
| `english_male_casual` | English | Dinesh |
| `english_female_calm` | English | Meera |
| `gujarati_male_narrator` | Gujarati | Yash |
| `hindi_male_narrator` | Hindi | Rohit |
| `hindi_female_teacher` | Hindi | Divya |
| `hindi_male_casual` | Hindi | Aman |
| `hindi_female_formal` | Hindi | Rani |
| `kannada_male_narrator` | Kannada | Suresh |
| `malayalam_female_narrator` | Malayalam | Anjali |
| `manipuri_male_narrator` | Manipuri | Laishram |
| `marathi_male_narrator` | Marathi | Sanjay |
| `marathi_female_narrator` | Marathi | Sunita |
| `marathi_male_casual` | Marathi | Nikhil |
| `marathi_female_calm` | Marathi | Radha |
| `nepali_female_narrator` | Nepali | Amrita |
| `odia_male_narrator` | Odia | Manas |
| `punjabi_male_narrator` | Punjabi | Divjot |
| `sanskrit_male_narrator` | Sanskrit | Aryan |
| `tamil_female_narrator` | Tamil | Jaya |
| `tamil_female_casual` | Tamil | Kavitha |
| `telugu_male_narrator` | Telugu | Prakash |
| `telugu_female_narrator` | Telugu | Lalitha |
| `telugu_male_casual` | Telugu | Kiran |

Call `voice_presets.list_presets()` at runtime for the full table
(language, speaker, and the exact description string) programmatically.

**Resolution order** (`voice_presets.get_description`):
1. `custom_description`, if given, is used verbatim (full override).
2. Else `preset_key`, if recognized, returns that preset's fixed description.
3. Else falls back to `hindi_male_narrator` (a Hindi recommended speaker),
   logging a warning — an unrecognized `preset_key` never raises or fails
   the request.

`speed` (`"slow" | "normal" | "fast"`) appends a relative pace clause
(e.g. "The delivery is slightly faster-paced than usual.") on top of the
resolved description, so it never contradicts the preset's own pace
wording.

### Adding a new preset

Edit `src/voice_presets.py` only:

1. Add an entry to `PRESETS` with a new `preset_key`.
2. `speaker` **must** be a real name from that language's roster in the
   `LANGUAGES` table (do not invent a name).
3. Write `description` in the same style as the existing entries —
   mention pace, pitch, expressivity, and recording quality, and include
   the literal phrase `"very clear audio"`.
4. Keep the description string fixed once added — don't regenerate it
   per request, or you lose the voice-consistency guarantee.

Ten languages officially support emotion tags (Assamese, Bengali, Bodo,
Dogri, Kannada, Malayalam, Marathi, Sanskrit, Nepali, Tamil) — see
`LANGUAGES[...]["emotion_support"]`. This is optional/advanced: append a
clause like `"...speaking in a Happy tone."` to a `custom_description`
for one of these languages if you want it; it is not applied by default.

---

## Model caching (no re-download per run)

**Default/primary approach for this build:** the model and both
tokenizers are downloaded **once, at Docker build time**, into a fixed
`HF_HOME=/app/hf_cache` path baked into the image layer (see the
`Dockerfile`'s `RUN python -c "..."` step). `ENV HF_HOME` /
`TRANSFORMERS_CACHE` are set *before* that step so build-time caching and
runtime loading agree on the same path.

At runtime, `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1` are set (after
the build-time download step, so they don't block that step itself).
This means:

- Workers never hit the network for weights on cold start or per-request.
- If a required file were ever missing from the image, loading fails
  loudly and immediately instead of silently re-downloading it.

The model is also loaded once at **module import time** in each handler
file (`MODEL, TOKENIZER, ... = tts_engine.load_model()` at the top of
`handler_direct.py` / `handler_streaming.py`), so it stays resident in
GPU memory across invocations on the same warm worker. This is separate
from the "no re-download" guarantee above but equally important for
cold-start latency.

**Build-time budget:** RunPod's GitHub-integration build step has a
documented **30-minute timeout**. `ai4bharat/indic-parler-tts` plus its
frozen `flan-t5-large` description encoder (770M params) is a genuinely
multi-GB download (roughly 6–8GB), on top of the base image pull and
dependency install — tight but normally within budget. `requirements.txt`
includes `hf_transfer`, and the Dockerfile sets
`HF_HUB_ENABLE_HF_TRANSFER=1` right before the build-time download step,
which uses a Rust-based downloader that's meaningfully faster than the
default on high-bandwidth networks. `torch` is deliberately **not** listed
in `requirements.txt` — the `runpod/pytorch` base image already ships a
matching torch+CUDA build, so pinning it again would risk pip fetching
another multi-GB wheel for no benefit.

**If the build still times out:** per RunPod's own docs, the two
supported paths are (1) pre-build the image locally/in CI and push it to
a container registry instead of using GitHub-integration builds, or
(2) switch from baking the model into the image to a **network volume**
cache. In that setup the model would be expected under
`/runpod-volume/huggingface-cache/hub/` per RunPod's model-caching
convention, `tts_engine.load_model()` would allow a network fetch on
first cold start instead of running `HF_HUB_OFFLINE=1` unconditionally,
and the Dockerfile's build-time download step would be dropped entirely.
That's a real architecture change (slower first cold start, a network
volume to attach in the console) and is **not** implemented here — baking
into the image remains this repo's default.

---

## Request / response shapes

### Direct endpoint (`HANDLER_TYPE=direct`)

Request:
```json
{
  "input": {
    "text": "नमस्ते, आप कैसे हैं?",
    "preset_key": "hindi_male_narrator",
    "custom_description": null,
    "speed": "normal"
  }
}
```

Response (success):
```json
{
  "audio_base64": "UklGRi...",
  "format": "wav",
  "sample_rate": 44100,
  "text": "नमस्ते, आप कैसे हैं?",
  "preset_key": "hindi_male_narrator",
  "speaker": "Rohit",
  "language": "hindi",
  "endpoint_type": "direct"
}
```

Response (failure) — generation errors are caught and returned as a
readable payload, the job never raises:
```json
{ "error": "...", "endpoint_type": "direct" }
```

### Streaming endpoint (`HANDLER_TYPE=streaming`)

Request: same shape as direct, plus optional `chunk_size_kb` (default `256`):
```json
{
  "input": {
    "text": "शिक्षा बहुत महत्वपूर्ण है।",
    "preset_key": "hindi_female_teacher",
    "chunk_size_kb": 256
  }
}
```

Yielded objects, in order:
```json
{"status": "generating", "text": "...", "preset_key": "hindi_female_teacher", "speaker": "Divya", "language": "hindi", "endpoint_type": "streaming"}
{"chunk_index": 0, "total_chunks": 12, "chunk_size_bytes": 262144, "audio_chunk_base64": "...", "progress_percent": 8.33, "endpoint_type": "streaming"}
...
{"chunk_index": 11, "total_chunks": 12, "chunk_size_bytes": 81920, "audio_chunk_base64": "...", "progress_percent": 100.0, "endpoint_type": "streaming"}
{"status": "completed", "total_audio_bytes": 3063808, "chunks_sent": 12, "sample_rate": 44100, "endpoint_type": "streaming"}
```

On error, a single `{"error": "...", "endpoint_type": "streaming"}` object
is yielded and the stream ends cleanly (no raised exception).

---

## Deploying two endpoints from one repo

1. Push this repo to GitHub (branch `main`).
2. In RunPod → **Serverless** → **+ New Endpoint** → **GitHub Repo** →
   select this repo → branch `main` → Dockerfile path `./Dockerfile`.
   - Name it e.g. `indic-tts-direct`.
   - Endpoint environment variable: `HANDLER_TYPE=direct`.
   - GPU: 1x A40/A6000 or similar, 16GB+ VRAM.
   - Container disk: 20–30GB (large enough for the baked-in model).
   - Set min/max workers, deploy.
3. Repeat **+ New Endpoint** → **GitHub Repo** → same repo, same branch.
   - Name it e.g. `indic-tts-streaming`.
   - Endpoint environment variable: `HANDLER_TYPE=streaming`.
   - Configure GPU/worker settings independently — streaming jobs hold
     connections open longer, so consider fewer max workers.
   - Deploy.
4. Both endpoints get distinct Endpoint IDs but track the same
   repo/branch/Dockerfile — a single `git push` to `main` triggers a
   rebuild for both.

---

## Example clients

### `curl` — direct endpoint

```bash
curl -X POST "https://api.runpod.ai/v2/<DIRECT_ENDPOINT_ID>/runsync" \
  -H "Authorization: Bearer $RUNPOD_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
        "input": {
          "text": "नमस्ते दुनिया, यह एक परीक्षण संदेश है।",
          "preset_key": "hindi_male_narrator",
          "speed": "normal"
        }
      }'
```

### Python (`runpod` SDK) — streaming endpoint

```python
import base64
import runpod

runpod.api_key = "YOUR_RUNPOD_API_KEY"
endpoint = runpod.Endpoint("<STREAMING_ENDPOINT_ID>")

run_request = endpoint.run({
    "text": "शिक्षा बहुत महत्वपूर्ण है।",
    "preset_key": "hindi_female_teacher",
    "chunk_size_kb": 256,
})

audio_bytes = bytearray()
for event in run_request.stream():
    if "audio_chunk_base64" in event:
        audio_bytes.extend(base64.b64decode(event["audio_chunk_base64"]))
        print(f"progress: {event['progress_percent']}%")
    elif event.get("status") == "completed":
        print("done:", event)
    elif "error" in event:
        print("error:", event["error"])

with open("out.wav", "wb") as f:
    f.write(audio_bytes)

print(run_request.status())
```

---

## Repository structure

```
indic-tts-runpod/
├── handler.py                 # container entrypoint: picks a handler by HANDLER_TYPE
├── src/
│   ├── handler_direct.py      # direct endpoint handler
│   ├── handler_streaming.py   # streaming endpoint handler
│   ├── tts_engine.py          # shared model load + generation core
│   └── voice_presets.py       # preset table + description resolution
├── Dockerfile                 # single Dockerfile for both endpoints
├── requirements.txt
├── test_input_direct.json
├── test_input_streaming.json
└── README.md
```
