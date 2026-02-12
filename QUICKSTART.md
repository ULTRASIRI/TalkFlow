# TalkFlow Quick Start Guide

Get TalkFlow running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- 8GB RAM (16GB recommended)
- Internet connection (for model downloads)
- Microphone

## Installation

### 1. Check Python version

**IMPORTANT:** Python 3.13+ is fully supported. Python 3.9-3.12 also work.

```bash
python --version  # or python3 --version
# Should show Python 3.9 or higher
```

### 2. Set up Python environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install dependencies

```bash
# Upgrade pip first (recommended)
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

This will take a few minutes to download and install all packages (~2-3 GB).

**Note:** If you get SSL errors, try:
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt
```

### 4. Download models

**Easy way - Use the automated script:**

```bash
python download_models.py
```

This will:
- Create all required directories
- Download Piper TTS voices (English and/or Spanish)
- Setup the model directory structure
- Provide status of all models

**Manual way (if automatic download fails):**

```bash
# Create directories
mkdir -p models/piper

# Download English US voice
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -o models/piper/en_US-lessac-medium.onnx
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -o models/piper/en_US-lessac-medium.onnx.json
```

**Note on other models:**
- **Whisper (ASR)**: Downloads automatically on first use (~500MB)
- **Argos Translate**: Downloads automatically when you select languages (~150MB per pair)

## Running TalkFlow

### Simple start

```bash
python run.py
```

### Or use uvicorn directly

```bash
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## First Use

1. **Open browser**: Navigate to `http://localhost:8000`

2. **Wait for connection**: Status should change to "Connected" (green dot)

3. **Select languages**:
   - Source: English (or your speaking language)
   - Target: Spanish (or desired translation language)

4. **Start listening**: Click "Start Listening" button

5. **Allow microphone**: Browser will request microphone permission

6. **Speak**: Start speaking in your source language

7. **See results**:
   - Transcription appears in real-time
   - Translation shows below
   - Audio plays automatically (if TTS is configured)
   - Metrics display processing times

## Configuration

Create a `.env` file (copy from `.env.example`):

```bash
cp .env.example .env
```

Edit `.env` to customize:

```bash
# Language settings
SOURCE_LANGUAGE=en
TARGET_LANGUAGE=es

# Performance tuning
WHISPER_MODEL_SIZE=small  # Options: tiny, base, small, medium
WHISPER_BEAM_SIZE=5       # Lower = faster, higher = more accurate

# VAD settings
VAD_ENABLED=true          # Enable voice activity detection
```

## Testing Without Models

For testing the interface without downloading large models:

```bash
# Set environment variable
export USE_MOCK_MODELS=true

# Run application
python run.py
```

This will use mock implementations that return placeholder data.

## Troubleshooting

### Python 3.13 Compatibility
✅ **Fully supported!** The updated requirements.txt works with Python 3.13.

If you're upgrading from an older installation:
```bash
# Remove old virtual environment
rm -rf venv

# Create fresh environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install with latest versions
pip install --upgrade pip
pip install -r requirements.txt
```

### "Module not found" errors
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### "WebSocket connection failed"
- Check if port 8000 is available
- Try a different port: `python run.py --port 8001`
- Check firewall settings

### "Microphone not accessible"
- Grant browser microphone permissions
- Check system audio settings
- Try a different browser

### High CPU/Memory usage
- Use smaller Whisper model (base or tiny)
- Reduce beam size to 3
- Disable VAD for testing

### Models downloading slowly
- First run will download models (may take 10-30 minutes)
- Check internet connection
- Consider downloading models manually

## Performance Tips

For best performance on 8GB RAM systems:

1. **Use small Whisper model with int8**:
   ```bash
   WHISPER_MODEL_SIZE=small
   WHISPER_COMPUTE_TYPE=int8
   ```

2. **Reduce beam size**:
   ```bash
   WHISPER_BEAM_SIZE=3
   ```

3. **Enable VAD**:
   ```bash
   VAD_ENABLED=true
   ```

4. **Close other applications** to free up RAM

## Next Steps

- **Try different languages**: Select from 99+ language pairs
- **Adjust voice**: Change `PIPER_VOICE` to use different TTS voices
- **Tune performance**: Experiment with configuration settings
- **Check metrics**: Monitor latency in the metrics panel

## Common Use Cases

### Live conversation translation
1. Source: English, Target: Spanish
2. Enable VAD for natural pauses
3. Start listening and speak normally

### Presentation translation
1. Disable VAD for continuous processing
2. Use higher beam size for accuracy
3. Monitor transcription for quality

### Learning languages
1. Speak in target language
2. See transcription to check pronunciation
3. Hear TTS output for reference

## Getting Help

- Check `logs/` directory for error details
- Review README.md for full documentation
- Verify all models are properly installed
- Ensure Python version is 3.9+

## Development Mode

For development with auto-reload:

```bash
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python run.py
```

---

**You're ready to go!** 🎉

Start speaking and watch the real-time translation happen.
