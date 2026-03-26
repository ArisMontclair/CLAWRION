# Fish S2 Pro Voice Agent

Real-time conversational voice AI. Talk to it like a phone call — no wake words, no typing.

**Pipeline:** Your voice → Whisper (STT) → Smart Turn (knows when you're done) → OpenRouter (brain) → Fish S2 Pro (voice) → Your speakers

---

## SETUP

### 1. Get API Keys

You need two:

| Key | Where to get it | Free? |
|-----|----------------|-------|
| **OpenRouter** | https://openrouter.ai/settings/keys | Pay per use (pennies) |
| **Fish Audio** | https://fish.audio/settings/api | Free tier available |

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

Open `.env` in a text editor and fill in:

```
OPENROUTER_API_KEY=sk-or-v1-paste-your-key-here
FISH_API_KEY=paste-your-key-here
```

Save. Done.

---

## USAGE

### Start the voice agent

```bash
source .venv/bin/activate   # if not already active
python bot.py
```

This starts a local server. Open **http://localhost:7860** in your browser.

### Talk to it

1. Click **"Connect"** in the browser
2. Allow microphone access when prompted
3. **Start talking** — it listens automatically
4. **Pause when done** — Smart Turn detects you're finished (handles long pauses, thinking time)
5. **Listen** — it responds with voice through your speakers

That's it. It's like a phone call.

### Change the voice

Edit `.env`:

```
FISH_VOICE_ID=abc123-reference-id
```

Get a voice ID from https://fish.audio → My Voices → copy the ID. Or leave it blank for the default voice.

### Change the LLM model

Edit `.env`:

```
LLM_MODEL=xiaomi/mimo-v2-pro          # default, good & cheap
LLM_MODEL=anthropic/claude-sonnet-4-20250514  # smarter, costs more
LLM_MODEL=openai/gpt-4o               # alternative
```

Any model on https://openrouter.ai works.

### Use emotion in speech

The AI automatically uses emotion tags for expressive speech. Examples it might say:

- "That's **[excited]** amazing!"
- "**[whisper]** I have a secret."
- "**[sigh]** I don't think that's going to work."

You can also ask it: "Say that more excited" or "whisper the next part."

---

## DEPLOY ON MODAL (optional)

For always-on access from anywhere (not just localhost):

```bash
pip install modal
modal setup              # connect to Modal account (free to sign up)
modal deploy bot.py      # deploys, gives you a public URL
```

Cost: ~$5-15/month for 30 min/day usage. Only charged when someone is talking.

---

## TROUBLESHOOTING

| Problem | Fix |
|---------|-----|
| "No module named pipecat" | Run `pip install -e .` again |
| No sound in browser | Check browser mic/speaker permissions |
| Bot doesn't respond | Check `.env` has valid API keys |
| Slow first response | Whisper downloads model on first run (~3GB). Wait. |
| Bot interrupts you | Smart Turn might need tuning. Edit `bot.py`, adjust VAD params |
