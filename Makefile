.PHONY: setup run deploy

setup:
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -e .
	@echo ""
	@echo "Done. Copy .env.example to .env and fill in your API keys."
	@echo "  source .venv/bin/activate"
	@echo "  make run"

run:
	python bot.py

deploy:
	modal deploy bot.py
