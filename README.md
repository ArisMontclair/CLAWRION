# Fish S2 Pro Voice Agent (Self-Hosted)

Real-time conversational voice AI. Talk to it like a phone call — no wake words, no typing.

**Pipeline:** Your voice → Whisper (STT) → Smart Turn (knows when you're done) → OpenRouter (brain) → **Self-Hosted Fish S2 Pro** (voice) → Your speakers

**Zero cloud TTS fees.** The Fish Speech S2 Pro model runs on your own GPU — no API keys, no usage limits.

---

## SETUP

### 1. Get API Keys

You only need one key:

| Key | Where to get it | Free? |
|-----|----------------|-------|
| **OpenRouter** | https://openrouter.ai/settings/keys | Pay per use (pennies) |

No Fish Audio API key needed — the TTS runs on your own infrastructure.

### 2. Install

```bash
git clone https://github.com/ArisMontclair/modal-fish-s2-pro-deployment.git
cd modal-fish-s2-pro-deployment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Configure

```bash
cp .env.example .env
```

Open `.env` and fill in:

```
OPENROUTER_API_KEY=sk-or-v1-paste-your-key-here
FISH_SPEECH_URL=http://localhost:8080     # or your Modal URL after deploy
```

Save. Done.

---

## USAGE

### Option A: Local (needs a GPU)

**Terminal 1 — Start Fish Speech TTS server:**

```bash
# Clone and run the official Fish Speech server
git clone https://github.com/fishaudio/fish-speech.git
cd fish-speech
pip install -e ".[server]"
python tools/api_server.py \
  --llama-checkpoint-path checkpoints/s2-pro \
  --decoder-checkpoint-path checkpoints/s2-pro/codec.pth \
  --listen 0.0.0.0:8080 --half
```

**Terminal 2 — Start the voice agent:**

```bash
cd modal-fish-s2-pro-deployment
source .venv/bin/activate
python bot.py
```

Open **http://localhost:7860** in your browser. Click Connect. Talk.

### Option B: Modal (GPU in the cloud, no local hardware needed)

**1. Install Modal:**

```bash
pip install modal
modal setup
```

**2. Deploy the Fish Speech TTS server:**

```bash
modal deploy fish_speech_server.py
```

This gives you a URL like `https://your-org--fish-speech-tts-fish-speech-server.modal.run`

**3. Update `.env`:**

```
FISH_SPEECH_URL=https://your-org--fish-speech-tts-fish-speech-server.modal.run
```

**4. Deploy the bot (or run locally):**

```bash
# Either deploy to Modal...
modal deploy bot.py

# ...or run locally (connects to Modal-hosted TTS)
python bot.py
```

**Modal costs:** ~$0.80/hour for A10G GPU. Only charged when someone is talking (with 5-min warm-up).

---

## ARCHITECTURE

```
┌─────────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────────────────┐
│   Browser   │────▶│   Pipecat   │────▶│   OpenRouter │     │  Fish Speech S2 Pro │
│  (WebRTC)   │     │  Bot Agent  │     │     LLM      │     │  (Self-Hosted GPU)  │
│  mic+speaker│◀────│  (STT+Turn) │◀────│              │────▶│    POST /v1/tts     │
└─────────────┘     └─────────────┘     └──────────────┘     └─────────────────────┘
                            │                                          │
                            │            HTTP (no cloud API)           │
                            └──────────────────────────────────────────┘
```

## CHANGELOG

### v0.3.0 — Self-Hosted TTS
- Replaced Fish Audio cloud API with self-hosted Fish Speech S2 Pro
- Added `fish_speech_tts.py` — custom Pipecat TTS service (HTTP)
- Added `fish_speech_server.py` — Modal deployment for TTS server
- Removed `FISH_API_KEY` dependency
- Added `FISH_SPEECH_URL` env var

### v0.2.0 — Pipecat Rebuild
- Full Pipecat pipeline with Smart Turn v3

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| "No module named pipecat" | Run `pip install -e .` again |
| TTS connection refused | Fish Speech server not running. Check `FISH_SPEECH_URL` |
| Slow TTS | First request downloads model (~8GB). Wait. Or use `--compile` flag |
| Out of memory on Modal | S2 Pro needs ~12GB VRAM. A10G (24GB) is sufficient. |
| No sound in browser | Check browser mic/speaker permissions |
