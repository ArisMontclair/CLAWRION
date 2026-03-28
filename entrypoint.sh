#!/bin/bash
set -e

echo "=== CLAWRION Bot Starting ==="

# Auto-deploy Modal server if credentials are set and no URL is configured
if [ -z "$VOICE_SERVER_URL" ] || [ "$VOICE_SERVER_URL" = "http://localhost:8080" ]; then
    if [ -n "$MODAL_TOKEN_ID" ] && [ -n "$MODAL_TOKEN_SECRET" ]; then
        echo "No VOICE_SERVER_URL set. Deploying to Modal..."
        python deploy_modal.py

        if [ -f /tmp/modal_url ]; then
            export VOICE_SERVER_URL=$(cat /tmp/modal_url)
            echo "VOICE_SERVER_URL=$VOICE_SERVER_URL"
        fi
    else
        echo "WARNING: No VOICE_SERVER_URL and no Modal credentials."
        echo "Set either VOICE_SERVER_URL or MODAL_TOKEN_ID + MODAL_TOKEN_SECRET in .env"
    fi
else
    echo "VOICE_SERVER_URL=$VOICE_SERVER_URL"
fi

echo "Starting bot..."
exec python bot.py
