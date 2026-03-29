"""Patch fish-speech reference_loader.py to fix torchaudio list_audio_backends().

In v2.0.0-beta, the code directly calls torchaudio.list_audio_backends() which
was removed in torchaudio 2.8. This wraps it in a try/except.
"""
import pathlib
import sys

target = pathlib.Path("/app/fish-speech/fish_speech/inference_engine/reference_loader.py")
src = target.read_text()

old = """        # Define the torchaudio backend
        backends = torchaudio.list_audio_backends()
        if "ffmpeg" in backends:
            self.backend = "ffmpeg"
        else:
            self.backend = "soundfile\""""

new = """        # Define the torchaudio backend
        try:
            backends = torchaudio.list_audio_backends()
            self.backend = "ffmpeg" if "ffmpeg" in backends else "soundfile"
        except (AttributeError, UnboundLocalError):
            self.backend = "soundfile\""""

if old not in src:
    print(f"ERROR: Patch target not found in {target}")
    print("Showing actual content around 'torchaudio':")
    for i, line in enumerate(src.splitlines(), 1):
        if 'torchaudio' in line or 'backend' in line.lower():
            print(f"  {i}: {line}")
    sys.exit(1)

target.write_text(src.replace(old, new))
print(f"Patched {target} successfully")
