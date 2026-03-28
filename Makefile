.PHONY: setup run deploy-tts deploy-bot deploy

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e .
	@echo ""
	@echo "Done. Copy .env.example to .env and fill in your keys."
	@echo "  source .venv/bin/activate"
	@echo "  make run"

run:
	python bot.py

deploy-tts:
	modal deploy fish_speech_server.py

deploy-bot:
	modal deploy bot.py

deploy: deploy-tts deploy-bot
	@echo ""
	@echo "Both Fish Speech TTS server and bot deployed."
	@echo "Update FISH_SPEECH_URL in .env with the Modal TTS endpoint."
