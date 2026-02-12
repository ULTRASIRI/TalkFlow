# TalkFlow Installation Guide

Complete installation instructions for Python 3.13 and all modern Python versions.

## ✅ Python 3.13 Fully Supported

This version of TalkFlow is fully compatible with Python 3.13.5 and all Python versions 3.9+.

## Quick Installation (Recommended)

### macOS/Linux:
```bash
# 1. Run automated installer
chmod +x install.sh
./install.sh

# 2. Download models
python download_models.py

# 3. Start application
python run.py
```

### Windows:
```powershell
# 1. Run automated installer
.\install.bat

# 2. Download models
python download_models.py

# 3. Start application
python run.py
```

## Manual Installation

### Step 1: Verify Python

```bash
python --version
# or
python3 --version

# Should show: Python 3.9.x or higher
# Python 3.13.5 is fully supported ✓
```

If Python is not installed:
- **macOS:** `brew install python@3.13`
- **Windows:** Download from [python.org](https://www.python.org/downloads/)
- **Linux:** `sudo apt install python3.13` (Ubuntu/Debian)

### Step 2: Create Virtual Environment

```bash
# Create venv
python -m venv venv

# Activate it
# macOS/Linux:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

Your prompt should now show `(venv)` at the beginning.

### Step 3: Install Dependencies

```bash
# Upgrade pip (important!)
pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

**Expected installation time:** 5-10 minutes  
**Download size:** ~2-3 GB (PyTorch is large)

#### If Installation Fails

**SSL Certificate Errors:**
```bash
pip install --trusted-host pypi.org --trusted-host pypi.python.org -r requirements.txt
```

**Timeout Errors:**
```bash
pip install --default-timeout=1000 -r requirements.txt
```

**Specific Package Errors:**
```bash
# Install packages one by one to identify the issue
pip install fastapi uvicorn websockets
pip install torch torchaudio
pip install faster-whisper
pip install argostranslate
pip install piper-tts
```

### Step 4: Download Models

#### Automated Download (Recommended)

```bash
python download_models.py
```

This interactive script will:
1. Create all necessary directories
2. Download Piper TTS voices (English and/or Spanish)
3. Verify installation
4. Provide next steps

#### Manual Download

If the automated script fails, download manually:

**English US Voice (Required):**
```bash
mkdir -p models/piper
cd models/piper

# Download voice files
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -o en_US-lessac-medium.onnx
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -o en_US-lessac-medium.onnx.json

cd ../..
```

**Spanish Voice (Optional):**
```bash
cd models/piper

curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx" -o es_ES-davefx-medium.onnx
curl -L "https://huggingface.co/rhasspy/piper-voices/resolve/main/es/es_ES/davefx/medium/es_ES-davefx-medium.onnx.json" -o es_ES-davefx-medium.onnx.json

cd ../..
```

**Other Models:**
- **Whisper (ASR):** Downloads automatically on first use (~500MB)
- **Argos Translate:** Downloads automatically when selecting languages (~150MB per pair)

### Step 5: Verify Installation

```bash
python verify.py
```

This will check:
- ✓ Python version
- ✓ All dependencies installed
- ✓ Directory structure
- ✓ Model files present
- ✓ Port availability
- ✓ System memory

Fix any issues marked with ✗ before proceeding.

### Step 6: Start TalkFlow

```bash
python run.py
```

You should see:
```
============================================================
TalkFlow - Real-Time Translation
============================================================

Configuration:
  Host: 127.0.0.1
  Port: 8000
  Source Language: en
  Target Language: es
  VAD Enabled: true

Starting TalkFlow...
Open your browser to: http://127.0.0.1:8000

Press Ctrl+C to stop
------------------------------------------------------------
```

### Step 7: Open Browser

Navigate to: **http://localhost:8000**

You should see the TalkFlow interface with:
- ✓ "Connected" status (green)
- ✓ Language selectors
- ✓ Start/Stop controls
- ✓ Transcription area
- ✓ Translation area
- ✓ Metrics display

## Troubleshooting

### Python 3.13 Issues

**Issue:** "No matching distribution found for torch==2.1.0"

**Solution:** You're using the old requirements.txt. The updated version supports Python 3.13:
```bash
# Ensure you have the latest requirements.txt
cat requirements.txt | grep "torch>="
# Should show: torch>=2.5.0
```

### Port Already in Use

```bash
# Check what's using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Use a different port
TALKFLOW_PORT=8001 python run.py
```

### Models Not Found

```bash
# Check models directory
ls -la models/piper/

# Should see:
# - en_US-lessac-medium.onnx
# - en_US-lessac-medium.onnx.json

# If missing, run:
python download_models.py
```

### Microphone Not Working

1. **Grant Browser Permission:**
   - Click lock icon in address bar
   - Enable microphone permission
   - Refresh page

2. **Check System Settings:**
   - macOS: System Settings → Privacy & Security → Microphone
   - Windows: Settings → Privacy → Microphone
   - Ensure browser has permission

3. **Try Different Browser:**
   - Chrome (best support)
   - Firefox (good support)
   - Safari (macOS only, good support)

### High Memory Usage

For 8GB RAM systems:
```bash
# Use smaller Whisper model
export WHISPER_MODEL_SIZE=base
python run.py

# Or edit .env file
echo "WHISPER_MODEL_SIZE=base" >> .env
```

### Slow Processing

```bash
# Reduce beam size for faster transcription
export WHISPER_BEAM_SIZE=3
python run.py

# Disable VAD for continuous processing
export VAD_ENABLED=false
python run.py
```

## Dependency Information

### Core Dependencies (Required)

- **FastAPI** (>=0.115.0): Web framework
- **Uvicorn** (>=0.32.0): ASGI server
- **WebSockets** (>=13.0): Real-time communication
- **PyTorch** (>=2.5.0): ML framework (works with Python 3.13)
- **faster-whisper** (>=1.1.0): Speech recognition
- **argostranslate** (>=1.9.1): Translation
- **piper-tts** (>=1.2.0): Text-to-speech
- **NumPy** (>=1.26.0): Numerical operations
- **SciPy** (>=1.11.0): Audio processing

### Optional Dependencies

- **numba** (>=0.60.0): Performance optimization
- **psutil** (>=6.0.0): System monitoring (for verify.py)

## Disk Space Requirements

- **Application:** ~200 KB
- **Python packages:** ~2-3 GB
- **Whisper small model:** ~500 MB
- **Piper voice (medium):** ~50 MB per voice
- **Argos language pair:** ~150 MB per pair

**Total minimum:** ~3-4 GB  
**Recommended:** 5-10 GB free space

## Memory Requirements

- **Idle:** ~200 MB
- **Active (Whisper small):** ~800 MB - 1.2 GB
- **Peak usage:** ~1.5 GB

**System RAM:**
- Minimum: 8 GB
- Recommended: 16 GB

## Verification Checklist

Before first use, ensure:

- [ ] Python 3.9+ installed (3.13 fully supported)
- [ ] Virtual environment created and activated
- [ ] All dependencies installed (`pip list | grep -E "fastapi|torch|whisper"`)
- [ ] Models directory created (`ls models/`)
- [ ] At least one Piper voice downloaded (`ls models/piper/`)
- [ ] Port 8000 available
- [ ] Microphone connected
- [ ] Browser supports WebSockets (Chrome, Firefox, Safari)

## Next Steps

After successful installation:

1. **Read Documentation:**
   - `QUICKSTART.md` - Basic usage
   - `README.md` - Full documentation
   - `PROJECT_STRUCTURE.md` - Architecture details

2. **Configure Settings:**
   ```bash
   cp .env.example .env
   # Edit .env for custom configuration
   ```

3. **Test Application:**
   - Start TalkFlow: `python run.py`
   - Open browser: http://localhost:8000
   - Grant microphone permission
   - Select languages
   - Click "Start Listening"
   - Speak and verify transcription/translation

4. **Explore Features:**
   - Try different language pairs
   - Toggle VAD on/off
   - Monitor performance metrics
   - Test TTS audio playback

## Getting Help

If you encounter issues:

1. **Check logs:** `cat logs/talkflow.log`
2. **Run verification:** `python verify.py`
3. **Review troubleshooting:** See above sections
4. **Check documentation:** `README.md`, `QUICKSTART.md`

## Update Instructions

To update TalkFlow:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate

# Update dependencies
pip install --upgrade -r requirements.txt

# Update models (if new versions available)
python download_models.py
```

---

**Installation complete!** You're ready to use TalkFlow for real-time offline translation.

Start the application: `python run.py`  
Open browser: http://localhost:8000
