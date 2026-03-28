FROM node:22-slim AS openclaw
RUN npm install -g openclaw@latest

FROM python:3.12-slim

WORKDIR /app

# Copy OpenClaw CLI from node stage
COPY --from=openclaw /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=openclaw /usr/local/bin/openclaw /usr/local/bin/openclaw

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

EXPOSE 7860

CMD ["python", "bot.py"]
