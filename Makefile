.PHONY: setup run docker-build docker-up docker-down deploy-stt deploy-tts deploy

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

docker-build:
	docker compose build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

deploy-stt:
	modal deploy stt_server.py

deploy-tts:
	modal deploy tts_server.py

deploy-modal: deploy-stt deploy-tts
	@echo ""
	@echo "Modal GPU services deployed. Update .env with the URLs."
