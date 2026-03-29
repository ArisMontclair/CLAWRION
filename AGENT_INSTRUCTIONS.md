# CLAWRION — Agent Instructions

Rules for any agent working on this repo. Read before making changes.

---

## Architecture

**Stack:** Orpheus TTS (Llama 3B) + Whisper medium, both on a single Modal A10G GPU.

**server.py** — Modal GPU server. TTS and STT only. No LLM inference — all language model logic goes through OpenClaw.

**bot.py** — Runs on Synology via Docker. Handles WebRTC, routes audio to server.py for STT/TTS, routes text to OpenClaw for thinking.

**orpheus_tts.py** — Pipecat TTS service class. Sends `{"text": ..., "voice": ...}` to server.py's `/v1/tts` endpoint.

---

## 1. Don't pre-install torch separately

Orpheus and vLLM manage their own torch dependency. Pre-installing torch separately creates version conflicts.

```python
# CORRECT — let vllm resolve torch
.uv_pip_install("orpheus-speech==0.1.0", "vllm==0.7.3")

# WRONG — pre-installing torch causes conflicts
.uv_pip_install("torch>=2.6.0")
.uv_pip_install("orpheus-speech==0.1.0", "vllm==0.7.3")
```

---

## 2. Pin all dependencies

Always pin to specific versions:

```python
.uv_pip_install("faster-whisper==1.1.1")
.uv_pip_install("orpheus-speech==0.1.0", "vllm==0.7.3")
```

Unpinned deps break silently when upstream changes.

---

## 3. Pre-download models during image build

If the model downloads at runtime on the GPU, every cold start pays for download time at $0.80/hr. Pre-download during image build (CPU, cheap):

```python
.run_commands(
    "python3 -c \"from huggingface_hub import snapshot_download; snapshot_download('model/name')\""
)
```

---

## 4. Don't use sed for code patches — use Python with verification

`sed -i` exits with code 0 whether or not the pattern was found. If upstream changes, the sed silently does nothing.

Use a separate Python script file with `assert` to fail the build if the pattern isn't found. See `patch_torchaudio.py` (deleted, but the pattern is correct).

---

## 5. Image layer order

Modal caches layers. Put stable layers first:

```
1. Base image (never changes)
2. pip_install stable deps (rarely changes)
3. pip_install app deps (changes when versions bump)
4. Model download (changes only when model changes)
5. pip_install web framework (rarely changes)
```

---

## 6. Don't deploy in a loop — investigate first

If a deploy fails, read the error, check `modal app logs`, understand the root cause. Don't guess and redeploy.

---

## 7. Don't strip system deps

Only remove an apt package if you've verified nothing in the dependency tree needs it.

---

## 8. Volumes shadow image files

Mounting a Volume at `/models` hides image files at `/models`. Don't mount at the same path as baked-in files.

---

## 9. `min_containers` cost trap

`min_containers=1` = GPU runs 24/7 at ~$0.80/hr = ~$19/day. Use `min_containers=0` unless you need zero cold starts.

The dashboard should poll `MODAL_HEALTH_URL` (lightweight endpoint), not the GPU endpoint.

---

## 10. Modal deploy output — save the URLs

Every deploy prints two URLs:
- GPU server: `Created web function server => https://xxx--aris-voice-server.modal.run`
- Lightweight health: `Created web function health => https://xxx--health.modal.run`

The bot needs both. Set `VOICE_SERVER_URL` and `MODAL_HEALTH_URL` in `.env`.

---

## 11. Keep bot.py and server.py in sync

If you change the TTS/STT API contract in server.py, update:
- `orpheus_tts.py` (Pipecat TTS service class)
- `bot.py` (the `/speak` endpoint)
- `.env.example` (env var names)

They all call the same `/v1/tts` and `/v1/transcribe` endpoints.
