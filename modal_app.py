"""
Fish S2 Pro — Modal Deployment
Serverless TTS on Modal. Pay per second of GPU time.
"""

import modal

app = modal.App("fish-s2-pro-tts")

# ─── Image ──────────────────────────────────────────────────────
# Use the pre-built Fish Speech CUDA Docker image from Docker Hub
fish_speech_image = (
    modal.Image.from_registry(
        "fishaudio/fish-speech:latest-server-cuda",
        add_python="3.12",
    )
    .env({"COMPILE": "0"})  # Set to "1" for faster inference (needs Triton)
)

# ─── Volume ─────────────────────────────────────────────────────
# Persistent storage for model weights (downloaded once, reused forever)
model_volume = modal.Volume.from_name("fish-s2-pro-models", create_if_missing=True)

VOLUME_PATH = "/models"


# ─── API Server ─────────────────────────────────────────────────
@app.function(
    image=fish_speech_image,
    gpu="A10G",           # 24GB VRAM — enough for S2 Pro
    timeout=600,           # 10 min max per request
    scaledown_window=300,  # Stay warm 5 min after last request
    volumes={VOLUME_PATH: model_volume},
    memory=16384,          # 16GB RAM
    # keep_warm=1,        # Uncomment to keep 1 instance always warm (costs money)
)
@modal.web_server(port=8080, startup_timeout=120)
def serve():
    """Run Fish Speech API server."""
    import subprocess
    import os

    # Symlink checkpoints to volume so the server finds them
    checkpoint_dir = "/app/checkpoints"
    volume_ckpt = f"{VOLUME_PATH}/checkpoints"

    # Create checkpoints dir in volume if it doesn't exist
    os.makedirs(volume_ckpt, exist_ok=True)

    # Link if not already linked
    if not os.path.islink(checkpoint_dir):
        if os.path.exists(checkpoint_dir):
            subprocess.run(["rm", "-rf", checkpoint_dir], check=True)
        os.symlink(volume_ckpt, checkpoint_dir)

    # Download model weights if not present
    s2_pro_dir = f"{volume_ckpt}/s2-pro"
    if not os.path.exists(f"{s2_pro_dir}/model.safetensors"):
        print("Downloading S2 Pro model weights...")
        subprocess.run(
            [
                "huggingface-cli", "download",
                "fishaudio/s2-pro",
                "--local-dir", s2_pro_dir,
            ],
            check=True,
        )
        # Commit to volume so next cold start doesn't re-download
        model_volume.commit()

    print("Starting Fish Speech API server on :8080...")
    subprocess.Popen(
        ["uv", "run", "tools/api_server.py", "--listen", "0.0.0.0:8080"],
        cwd="/app",
    )


# ─── Health Check ───────────────────────────────────────────────
@app.function()
@modal.web_endpoint()
def health():
    """Simple health check endpoint."""
    return {"status": "ok", "model": "fish-s2-pro"}
