# Hugging Face Token Setup for RunPod

`ai4bharat/indic-parler-tts` is a **gated** Hugging Face model — downloading
it (even from code) requires accepting its terms and using an authenticated
access token. This repo downloads the model at container **startup**, not at
Docker build time (see `README.md` → "Model caching" for why), so both
RunPod endpoints need an `HF_TOKEN` environment variable before they can
serve a single request.

This guide is the full step-by-step for creating that token and setting it
on RunPod. Do this once per endpoint (direct **and** streaming — each is a
separate endpoint with its own environment variables).

---

## Step 1 — Create/log in to a Hugging Face account

1. Go to https://huggingface.co/join (or https://huggingface.co/login if
   you already have an account).
2. Sign up or log in.

---

## Step 2 — Accept the model's terms (the "gate")

1. While logged in, open https://huggingface.co/ai4bharat/indic-parler-tts.
2. If you see a notice asking you to share your contact information /
   agree to the license before accessing files, fill it in and submit it.
   Access is granted immediately (no manual approval wait, for this model).
3. Confirm you now see the "Files and versions" tab without a gate prompt.

> If you skip this step, your token will still authenticate you to
> Hugging Face, but downloading the model will fail with a 401/403
> "access to model ... is restricted" error, because *your account*
> hasn't accepted the gate yet — the token alone isn't enough.

---

## Step 3 — Create an access token

1. Go to https://huggingface.co/settings/tokens.
2. Click **Create new token**.
3. Give it a name (e.g. `runpod-indic-tts`).
4. Token type: **Read** is sufficient — this repo only downloads model
   files, it never uploads or writes to the Hub.
5. Click **Create token**, then **copy the token value immediately**
   (it starts with `hf_...`). Hugging Face only shows it once; if you lose
   it, delete it and create a new one.

Keep this token secret — treat it like a password. Don't commit it to the
repo, paste it into a public issue, or share it outside RunPod's
environment-variable field below.

---

## Step 4 — Add `HF_TOKEN` to each RunPod endpoint

You have two endpoints from this one repo (`indic-tts-direct` and
`indic-tts-streaming`, or whatever you named them) — **`HF_TOKEN` must be
set on both**, since each endpoint's workers load the model independently.

### If you're creating a new endpoint

1. RunPod console → **Serverless** → **+ New Endpoint** → **GitHub Repo**.
2. While configuring the endpoint, find the **Environment Variables**
   section.
3. Add a variable:
   - Key: `HF_TOKEN`
   - Value: the `hf_...` token you copied in Step 3.
4. Add the other required variable too: `HANDLER_TYPE=direct` (or
   `streaming` for the second endpoint).
5. Finish the rest of the endpoint configuration (GPU, workers, etc.) and
   deploy.

### If the endpoint already exists

1. RunPod console → **Serverless** → select the endpoint.
2. Open its settings (usually an **Edit** or gear/settings icon on the
   endpoint's page).
3. Find **Environment Variables**.
4. Add:
   - Key: `HF_TOKEN`
   - Value: the `hf_...` token you copied in Step 3.
5. Save. RunPod will apply the new environment variable to workers going
   forward — a manual redeploy or a fresh push to `main` ensures new
   workers pick it up immediately rather than waiting for natural
   worker recycling.

Repeat this for **both** endpoints. It's the same token both times, just
set as an environment variable on each endpoint separately (RunPod
endpoint environment variables aren't shared across endpoints).

---

## Step 5 — (Recommended) Attach a Network Volume

Without a network volume, **every new worker** re-downloads the model on
its first request — slow, and repeated per worker. A network volume lets
the download happen once, ever, shared across every worker on both
endpoints.

1. RunPod console → **Storage** → **Network Volumes** → **+ New Network
   Volume**.
2. Create it in the **same region** as the GPU pool your endpoints use
   (a volume can only attach to endpoints in its own region).
3. Open each endpoint's settings → find the **Network Volume** option →
   attach the volume you just created.
4. Do this for both the direct and streaming endpoints, so they share one
   cached copy of the model (it mounts at `/runpod-volume` — `tts_engine.py`
   detects this automatically and caches there when present).

---

## Step 6 — Verify

1. Trigger a fresh deploy (push a commit to `main`, or use the endpoint's
   manual rebuild/redeploy option).
2. Once built, send a test request using `test_input_direct.json` (direct
   endpoint) or `test_input_streaming.json` (streaming endpoint) — see
   `README.md` → "Example clients" for `curl`/Python snippets.
3. The first request after a fresh worker starts will be slower (model
   download); a response with `audio_base64` (direct) or a `completed`
   status (streaming) confirms `HF_TOKEN` and the gate are working.

---

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Worker fails to start / crashes immediately, no requests served | `HF_TOKEN` isn't set on this endpoint, or is set on only one of the two endpoints. |
| `401` / `403` / "access to model ... is restricted" in worker logs | Your Hugging Face **account** hasn't accepted the model's gate yet (Step 2) — the token itself can still be valid. |
| Works on one endpoint but not the other | `HF_TOKEN` was only added to one endpoint's environment variables — repeat Step 4 on the other. |
| Every cold start is slow, not just the first ever request | No network volume attached (or the two endpoints are on volumes/regions that don't match) — see Step 5. |
| Token stopped working after previously working | Token was deleted/revoked on the Hugging Face tokens page — create a new one and update it on both endpoints (Step 4). |
