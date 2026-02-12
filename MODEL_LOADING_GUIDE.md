# Model Loading Guide

Complete guide to setting up all AI models for TalkFlow.

## Quick Diagnosis

Check your logs for these messages:

### ✅ All Models Working
```
✓ VAD initialized
✓ ASR (Whisper) initialized successfully
✓ Translator (Argos) initialized successfully  
✓ TTS (Piper) initialized successfully
✅ Pipeline initialization complete
```

### ⚠ Mock Models (Not Production Ready)
```
⚠ Mock ASR initialized (NOT PRODUCTION READY)
⚠ Mock Translator
⚠ Mock TTS initialized (NOT PRODUCTION READY)
```

If you see "Mock" messages, follow this guide to fix it.

## Model Setup Checklist

- [ ] Whisper ASR model downloaded
- [ ] Argos translation package installed
- [ ] Piper TTS voice files present
- [ ] Internet connection available (for first-time setup)
- [ ] Sufficient disk space (~5GB)

## 1. Whisper ASR Setup

### Automatic Download (Recommended)

Whisper downloads automatically on first use:

```bash
# Just start the application
python run.py

# Watch logs - first run will download:
# "Downloading Whisper model..."
# This takes 5-10 minutes for 'small' model (~500MB)
```

### Manual Verification

```python
# Test Whisper loading
python -c "
from faster_whisper import WhisperModel
model = WhisperModel('small', device='cpu', compute_type='int8')
print('✓ Whisper model loaded successfully')
"
```

### Troubleshooting

**Error: "Model file not found"**
```bash
# Check cache
ls -la ~/.cache/huggingface/hub/

# Force redownload
rm -rf ~/.cache/huggingface/hub/models--guillaumekln--faster-whisper*

# Restart app
python run.py
```

**Error: "Connection timeout"**
```bash
# Slow internet - increase timeout
export HF_HUB_DOWNLOAD_TIMEOUT=1200
python run.py
```

**Error: "Disk space"**
```bash
# Check available space
df -h ~/.cache

# Need at least 2GB free for 'small' model
```

### Using Different Model Sizes

```bash
# Tiny (fastest, ~75MB)
export WHISPER_MODEL_SIZE=tiny

# Base (fast, ~145MB)  
export WHISPER_MODEL_SIZE=base

# Small (recommended, ~500MB) - DEFAULT
export WHISPER_MODEL_SIZE=small

# Medium (better quality, ~1.5GB)
export WHISPER_MODEL_SIZE=medium
```

## 2. Argos Translate Setup

### Automatic Installation

Argos packages install when you select languages:

```bash
# Start app
python run.py

# In browser:
# 1. Select source language (e.g., English)
# 2. Select target language (e.g., Spanish)
# Package downloads automatically
```

### Manual Installation

```bash
# Install argos CLI
pip install argostranslate

# Update package index
argospm update

# Install language pair (e.g., English to Spanish)
argospm install translate-en_es

# Verify
argospm list
```

### Available Language Pairs

```bash
# See all available packages
argospm search

# Common pairs:
# en-es (English → Spanish)
# en-fr (English → French)
# en-de (English → German)
# es-en (Spanish → English)
# fr-en (French → English)
```

### Troubleshooting

**Error: "Package not found"**
```bash
# Update package index
argospm update

# Search for available packages
argospm search | grep en-es

# Install manually
argospm install translate-en_es
```

**Error: "Download failed"**
```bash
# Check internet connection
curl -I https://github.com

# Try direct download
cd ~/.local/share/argos-translate/packages
curl -LO https://argosopentech.nyc3.digitaloceanspaces.com/argospm/index/translate-en_es-1_9.argosmodel
argospm install translate-en_es-1_9.argosmodel
```

## 3. Piper TTS Setup

### Automated Download

```bash
# Use the download script
python download_models.py

# Select option 1 or 3:
# 1. English US (en_US-lessac-medium)
# 3. Both English and Spanish
```

### Manual Download

```bash
# Create directory
mkdir -p models/piper

# Download English US voice
cd models/piper

# Download .onnx model file
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -o en_US-lessac-medium.onnx

# Download .json config file
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -o en_US-lessac-medium.onnx.json

cd ../..
```

### Verify Installation

```bash
# Check files exist
ls -lh models/piper/

# Should see:
# en_US-lessac-medium.onnx       (~50MB)
# en_US-lessac-medium.onnx.json  (~1KB)
```

### Available Voices

**English:**
- `en_US-lessac-medium` (US, recommended)
- `en_US-libritts-high` (US, high quality)
- `en_GB-alan-medium` (UK)

**Spanish:**
- `es_ES-davefx-medium` (Spain)
- `es_MX-ald-medium` (Mexico)

**Other Languages:**
- French: `fr_FR-mls_1840-low`
- German: `de_DE-thorsten-medium`
- Italian: `it_IT-paola-medium`
- Portuguese: `pt_BR-faber-medium`

Full list: https://huggingface.co/rhasspy/piper-voices/tree/main

### Configuration

```bash
# In .env file
PIPER_VOICE=en_US-lessac-medium  # Must match filename without .onnx
```

### Troubleshooting

**Error: "Voice file not found"**
```bash
# Check file exists
ls models/piper/en_US-lessac-medium.onnx

# Check filename matches config
grep PIPER_VOICE .env

# Files must be:
# - filename.onnx
# - filename.onnx.json
# Both must exist
```

**Error: "'PiperVoice' object has no attribute 'synthesize_stream_raw'"**
✅ **Fixed in v2.2** - The code now handles different Piper API versions automatically.

**Error: "Model loading failed"**
```bash
# Test Piper directly
python -c "
from piper import PiperVoice
voice = PiperVoice.load('models/piper/en_US-lessac-medium.onnx')
print('✓ Piper voice loaded')
"
```

## Complete Setup Script

Run this to set everything up:

```bash
#!/bin/bash

echo "Setting up TalkFlow models..."

# 1. Install dependencies
pip install -r requirements.txt

# 2. Download Piper voice
python download_models.py

# 3. Install Argos package
pip install argostranslate
argospm update
argospm install translate-en_es

# 4. Verify setup
python verify.py

# 5. Start application (Whisper downloads on first run)
echo "Starting TalkFlow - Whisper will download on first use..."
python run.py
```

## Testing Models

### Test Whisper
```python
from faster_whisper import WhisperModel
import numpy as np

model = WhisperModel("small", device="cpu", compute_type="int8")
audio = np.random.randn(16000).astype(np.float32)  # 1 second
segments, info = model.transcribe(audio)
print("✓ Whisper working")
```

### Test Argos
```python
import argostranslate.translate

translated = argostranslate.translate.translate(
    "Hello world", "en", "es"
)
print(f"✓ Argos working: {translated}")
```

### Test Piper
```python
from piper import PiperVoice

voice = PiperVoice.load("models/piper/en_US-lessac-medium.onnx")
audio = voice.synthesize("Hello world")
print("✓ Piper working")
```

## Disk Space Requirements

| Component | Size | Location |
|-----------|------|----------|
| Whisper small | ~500MB | `~/.cache/huggingface/hub/` |
| Argos en-es | ~150MB | `~/.local/share/argos-translate/` |
| Piper voice | ~50MB | `models/piper/` |
| **Total** | **~700MB** | |

Additional models:
- Whisper medium: ~1.5GB
- Each Argos pair: ~150MB
- Each Piper voice: ~50MB

## Common Issues

### "Using Mock ASR"

**Cause:** Whisper model not downloaded

**Fix:**
1. Ensure internet connection
2. Wait for model download (first run)
3. Check disk space
4. Check logs for download progress

### "Using Mock Translator"

**Cause:** Argos package not installed

**Fix:**
```bash
argospm update
argospm install translate-en_es
```

### "Using Mock TTS"

**Cause:** Piper voice files missing

**Fix:**
```bash
python download_models.py
# Select option 1 or 3
```

### All Mocks Active

**Cause:** First-time setup incomplete

**Fix:**
```bash
# Run complete setup
./install.sh  # or install.bat
python download_models.py
python run.py
```

## Production Checklist

Before deploying, verify:

```bash
# Check logs for ✓ symbols (not ⚠)
python run.py 2>&1 | grep "✓"

# Should see:
# ✓ VAD initialized
# ✓ ASR (Whisper) initialized successfully
# ✓ Translator (Argos) initialized successfully
# ✓ TTS (Piper) initialized successfully
# ✅ Pipeline initialization complete
```

No "Mock" or "⚠" symbols = Production ready!

## Getting Help

If models still won't load:

1. **Check logs:**
   ```bash
   tail -f logs/talkflow.log
   ```

2. **Run verification:**
   ```bash
   python verify.py
   ```

3. **Test components individually:**
   - Use test scripts above
   - Isolate which model fails

4. **Check GitHub issues:**
   - faster-whisper
   - argostranslate
   - piper-tts

---

**Last Updated:** v2.2  
**Status:** Production Ready (when all ✓ appear)
