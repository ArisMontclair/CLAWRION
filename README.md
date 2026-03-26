# Fish S2 Pro Voice Agent

Real-time conversational voice AI built with [Pipecat](https://github.com/pipecat-ai/pipecat).

## Pipeline

```
Mic → Whisper STT → Smart Turn v3 → OpenRouter LLM → Fish S2 Pro TTS → Speakers
```

- **STT:** Faster-Whisper (local, GPU) or Deepgram (cloud)
- **Turn Detection:** Smart Turn v3 — knows when you're done vs. thinking
- **LLM:** OpenRouter (MiMo-V2-Pro, Claude, GPT, etc.)
- **TTS:** Fish Audio S2 Pro — SOTA expressive voice with emotion tags
- **Transport:** Daily WebRTC or SmallWebRTC (P2P, no API keys)

## Quick Start

### 1. Install

```bash
git clone https://github.com/ArisMontclair/modal-fish-s2-pro-deployment.git
cd modal-fish-s2-pro-deployment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 2. Configure

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 3. Run Locally (SmallWebRTC, no API keys needed)

```bash
python bot.py
```

Open `http://localhost:7860` in your browser. Click connect. Talk.

### 4. Deploy to Modal

```bash
pip install modal
modal setup
modal deploy bot.py
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENROUTER_API_KEY` | Yes | OpenRouter API key for LLM |
| `FISH_API_KEY` | Yes | Fish Audio API key for TTS |
| `DAILY_API_KEY` | If using Daily | Daily.co API key |
| `DEEPGRAM_API_KEY` | Optional | Use Deepgram STT instead of local Whisper |
| `WHISPER_MODEL` | Optional | Whisper model size (default: large-v3) |

## Emotion Tags

Embed in the LLM system prompt to make the assistant use expressive speech:

```
Use emotion tags in your speech output: [whisper] [excited] [angry] [laughing] [sad] [pause] [emphasis] [sigh]
```

## Architecture

- **bot.py** — Main Pipecat pipeline (CPU-only, lightweight)
- **Whisper** runs on GPU via faster-whisper (included in pipeline)
- **Smart Turn v3** runs on CPU (bundled with Pipecat)
- **Fish S2 Pro** via Fish Audio API (no local GPU needed for TTS)
- **LLM** via OpenRouter API

## Cost (Modal)

| Component | GPU? | Cost |
|-----------|------|------|
| Bot container (pipeline) | CPU only | ~$0.0001/sec |
| Whisper STT | T4 (optional) | ~$0.0002/sec |
| Fish S2 Pro TTS | Via API | ~$0.015/1K chars |
| OpenRouter LLM | Via API | Model-dependent |

Estimated for 30 min/day conversation: **~$5-15/month**

## License

MIT (code). Fish S2 Pro model weights subject to [Fish Audio Research License](https://github.com/fishaudio/fish-speech/blob/main/LICENSE).
