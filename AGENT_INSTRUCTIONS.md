# CLAWRION — Agent Instructions

Rules for any agent working on this repo. Read before making changes.

---

## 1. Never pin torch/torchaudio/torchvision separately

**Don't do this:**
```python
.pip_install("torch>=2.6.0", "torchaudio>=2.6.0")
.run_commands("pip install -e '.[server]'")
```

**Do this:**
```python
.run_commands("pip install -e '.[server]'")
```

Fish-speech's `[server]` extras declare exact compatible versions of torch, torchaudio, and all other dependencies. Pre-installing torch separately creates version conflicts because pip tries to satisfy two competing constraints.

This was the root cause of 6+ failed deploys on 2026-03-29. sglang required torch 2.9.1, fish-speech required torch 2.8.0. Removing sglang and letting fish-speech manage everything in one `pip install` resolved it.

**Exception:** If you need a package that's NOT part of fish-speech's dependency tree (like faster-whisper), install it BEFORE the fish-speech install so pip can satisfy both.

---

## 2. Don't use sed for code patches — use Python with verification

**Don't do this:**
```python
.run_commands("sed -i 's/old/new/' /app/fish-speech/some_file.py")
```

`sed -i` exits with code 0 whether or not the pattern was found. If the upstream file changes, the sed silently does nothing and you only find out at runtime.

**Do this:**
```python
.run_commands("""python3 -c "
import pathlib
p = pathlib.Path('/app/fish-speech/some_file.py')
src = p.read_text()
old = '''the exact old text'''
new = '''the replacement text'''
assert old in src, f'Patch target not found in {p}'
p.write_text(src.replace(old, new))
print('Patched successfully')
"
""")
```

Python gives you:
- `assert` to fail the build if the pattern isn't found
- Exact multi-line matching (sed chokes on special characters)
- Clear error messages

---

## 3. Pin dependencies to specific versions

Always pin git clones and pip installs to known-good versions:

```python
# Git: use --branch or checkout a commit
.run_commands("git clone --depth 1 --branch v2.0.0 https://github.com/fishaudio/fish-speech.git /app/fish-speech")

# Pip: use ==
.uv_pip_install("faster-whisper==1.1.1")
```

Unpinned deps break silently when upstream changes. You won't know until the next deploy fails or inference produces wrong results.

---

## 4. Image layer order matters

Modal caches image layers. Put stable, rarely-changing layers first:

```
1. Base image (never changes)
2. apt_install (rarely changes)
3. pip_install stable deps (rarely changes)
4. git clone pinned version (changes only when you bump version)
5. pip install fish-speech (changes when deps change)
6. Model weight download (changes only when model changes)
7. pip_install fastapi/uvicorn (rarely changes)
```

Code changes (server.py) are mounted separately and don't trigger image rebuilds. Only change layers 3-6 when you intentionally want to update dependencies.

---

## 5. The `min_containers` cost trap

`min_containers=1` means the GPU runs 24/7 at ~$0.80/hr = ~$19/day even when nobody is using it.

Use `min_containers=0` (scale to zero) unless you specifically need zero cold starts. The dashboard should poll the lightweight health endpoint (`MODAL_HEALTH_URL`), not the GPU endpoint, to avoid keeping the GPU alive.

---

## 6. Don't deploy in a loop — investigate first

If a deploy fails, DO NOT immediately guess a fix and redeploy. Modal image builds cost money and take minutes.

**Do this instead:**
1. Read the error message fully
2. Check the Modal logs: `modal app logs <app-name> --timestamps`
3. Understand the root cause before touching code
4. Only deploy when you're confident the fix addresses the actual error

On 2026-03-29, 8+ deploys were done in a loop, each fixing one symptom while missing the root cause (manually managing fish-speech's deps). The correct fix was known from the start: remove the manual dep installs and let fish-speech handle it.

---

## 7. Don't strip system deps to "simplify" the image

If the original image had `apt_install("git", "ffmpeg", "build-essential", "clang", "libportaudio2", "portaudio19-dev")`, don't remove packages thinking they're unnecessary. Packages like `clang` and `portaudio19-dev` are needed at build time for compiling pyaudio. Removing them causes build failures that waste a full image rebuild cycle.

Only remove a system dep if you've verified nothing in the dependency tree needs it.

---

## 8. Modal Volumes shadow image files

If you mount a Volume at `/models` and the image also has files at `/models/s2-pro`, the Volume mount hides the image files. The container sees the Volume contents (which may be empty), not the baked-in files.

**Options:**
- Don't mount a volume — bake models into the image (simpler, but image rebuilds re-download)
- Mount the volume at a different path than where image files live
- Download at runtime into the volume if it's empty (fallback pattern)

---

## 9. Check actual installed versions before debugging runtime errors

If something fails at runtime with an import error or version mismatch, check what's actually installed in the container before guessing:

```bash
modal app logs <app-name> | grep "Successfully installed"
```

The install log shows exact versions. Comparing these against what the code expects often reveals the real problem immediately.

---

## 10. Image builds are expensive — cache aggressively

Every image rebuild downloads and installs all packages from scratch. Modal caches layers, but only if the layer definition hasn't changed.

**To minimize rebuilds:**
- Change server.py code (mounted separately) instead of image layers when possible
- Put the most stable layers first (base image, apt, stable pip packages)
- Put changing layers last (model downloads, fish-speech install)
- Don't change the git clone URL/branch unless you intend to update fish-speech
