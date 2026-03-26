# Fish S2 Pro — Modal Deployment

## What

Serverless Fish Audio S2 Pro TTS running on Modal. You pay only for GPU time when generating speech. No servers, no maintenance, scales to zero.

## Cost

| Usage Level | GPU | Estimated Monthly |
|-------------|-----|-------------------|
| Light (30 min/day) | A10G | ~$8-12 |
| Medium (2h/day) | A10G | ~$30-40 |
| Heavy (8h/day) | A10G | ~$100 |

The A10G (24GB) is $0.000306/second on Modal.

## Setup

### 1. Install Modal

```bash
pip install modal
modal setup
```

### 2. Deploy

```bash
modal deploy modal_app.py
```

First deploy takes ~5-10 minutes (downloads 8GB model weights into persistent volume). Subsequent deploys are instant — weights are cached.

### 3. Your endpoint

After deploy, Modal gives you:
```
https://your-workspace--fish-s2-pro-tts-serve.modal.run
```

## API Usage

### Generate Speech

```bash
curl -X POST https://your-endpoint/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello! [excited] This is amazing!",
    "format": "wav"
  }' \
  --output speech.wav
```

### With Voice Cloning

Upload a reference audio (10-30 seconds of the target voice):

```bash
curl -X POST https://your-endpoint/v1/tts \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is my cloned voice.",
    "reference_audio_base64": "'"$(base64 -w0 reference.wav)"'",
    "format": "wav"
  }' \
  --output cloned.wav
```

### OpenAI-Compatible Endpoint

Fish Speech exposes an OpenAI-compatible API:

```bash
curl -X POST https://your-endpoint/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{
    "model": "fish-speech-s2-pro",
    "input": "Hello world!",
    "voice": "alloy",
    "response_format": "wav"
  }' \
  --output speech.wav
```

## Emotion Tags

Embed in text for expressive speech:

- `[whisper]` `[excited]` `[angry]` `[laughing]`
- `[sad]` `[shocked]` `[pause]` `[emphasis]`
- `[sigh]` `[shouting]` `[low voice]` `[singing]`

Full list: [Fish Audio docs](https://speech.fish.audio/inference/)

## Cold Starts

First request after idle: **~15-30 seconds** (model loading).
Subsequent requests (warm): **~100ms** TTFA, **RTF ~0.3x**.

To eliminate cold starts, uncomment `keep_warm=1` in `modal_app.py` (adds ~$15-20/month).

## Local Testing

```bash
modal serve modal_app.py  # hot-reload dev mode
```

## Architecture

```
Your App → HTTPS → Modal Edge → A10G GPU → Fish S2 Pro → Audio
                                      │
                              Model cached in Volume
                              (downloaded once)
```
