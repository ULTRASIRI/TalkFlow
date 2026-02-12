# TalkFlow Models Directory

This directory contains the AI models used by TalkFlow.

## Directory Structure

```
models/
├── whisper/      # Whisper ASR models
├── argos/        # Argos translation models
└── piper/        # Piper TTS voices
```

## Model Downloads

### 1. Whisper (Automatic Speech Recognition)

Whisper models are automatically downloaded on first use. They are cached in:
- Linux/Mac: `~/.cache/huggingface/hub/`
- Windows: `%USERPROFILE%\.cache\huggingface\hub\`

**Available models:**
- `tiny` (~75MB) - Fastest, lowest accuracy
- `base` (~145MB) - Fast, good for simple speech
- `small` (~500MB) - **Recommended**, good balance
- `medium` (~1.5GB) - Better accuracy, slower
- `large` (~3GB) - Best accuracy, slowest

**Default:** `small` with `int8` quantization (~240MB effective size)

### 2. Argos Translate (Translation)

Argos translation packages are downloaded on-demand when you select a language pair.

**Installation:**
```bash
# Packages are automatically installed via argostranslate
# Each language pair is ~100-200MB
```

**Popular language pairs:**
- English ↔ Spanish
- English ↔ French
- English ↔ German
- English ↔ Italian
- English ↔ Portuguese
- Spanish ↔ French
- And many more...

**Storage location:**
- Linux/Mac: `~/.local/share/argos-translate/packages/`
- Windows: `%APPDATA%\argos-translate\packages\`

### 3. Piper (Text-to-Speech)

Piper voices must be downloaded manually from:
https://github.com/rhasspy/piper/releases

**Installation steps:**

1. **Download voices** (choose quality level):
   - `low` quality: ~10-20MB per voice (faster)
   - `medium` quality: ~30-50MB per voice (recommended)
   - `high` quality: ~100-150MB per voice (best quality)

2. **English (US) - Recommended starter:**
   ```bash
   # Download en_US-lessac-medium
   # You need both files:
   # - en_US-lessac-medium.onnx
   # - en_US-lessac-medium.onnx.json
   ```

3. **Place files** in `models/piper/`:
   ```
   models/piper/
   ├── en_US-lessac-medium.onnx
   ├── en_US-lessac-medium.onnx.json
   └── ... (other voices)
   ```

**Available voices by language:**

- **English:**
  - `en_US-lessac-medium` (US, male)
  - `en_US-libritts-high` (US, multiple speakers)
  - `en_GB-alan-medium` (UK, male)

- **Spanish:**
  - `es_ES-mls_10246-low` (Spain)
  - `es_MX-ald-medium` (Mexico)

- **French:**
  - `fr_FR-mls_1840-low` (France)

- **German:**
  - `de_DE-thorsten-medium` (Germany)

- **And many more languages...**

**Configuration:**
Update `PIPER_VOICE` in `.env` to change the voice:
```bash
PIPER_VOICE=en_US-lessac-medium
```

## Disk Space Requirements

**Minimum setup (~1GB):**
- Whisper small: ~240MB (quantized)
- 1 Argos language pair: ~150MB
- 1 Piper voice (medium): ~50MB

**Recommended setup (~2GB):**
- Whisper small: ~240MB
- 3 Argos language pairs: ~450MB
- 3 Piper voices (medium): ~150MB

**Full setup (~10GB+):**
- Whisper medium: ~1.5GB
- Multiple Argos pairs: ~3GB
- Multiple Piper voices: ~1GB

## Manual Model Placement

If you want to use custom model locations, set these environment variables:

```bash
export WHISPER_MODEL_PATH=/custom/path/to/whisper
export ARGOS_MODEL_PATH=/custom/path/to/argos
export PIPER_MODEL_PATH=/custom/path/to/piper
```

## Troubleshooting

### Whisper models not loading
- Check internet connection (for first download)
- Verify sufficient disk space
- Check HuggingFace cache directory permissions

### Argos translation fails
- Ensure the language pair is supported
- Check internet connection (for first download)
- Verify package installation: `argostranslate-cli list`

### Piper TTS not working
- Verify `.onnx` and `.onnx.json` files are both present
- Check file names match exactly
- Ensure voice name in config matches filename

### Out of disk space
- Use smaller Whisper model (base or tiny)
- Install only needed language pairs
- Use low-quality Piper voices

## Performance Notes

- **Whisper int8 quantization** reduces memory by ~50% with minimal accuracy loss
- **Argos models** are relatively small and fast
- **Piper voices**: Medium quality offers best balance of size/quality

## Updating Models

Models are generally stable, but updates may be available:

**Whisper:**
```bash
# Clear cache and redownload
rm -rf ~/.cache/huggingface/hub/
# Restart TalkFlow to redownload
```

**Argos:**
```bash
# Update package index
argostranslate-cli update
```

**Piper:**
- Check GitHub releases for new voices
- Download and replace .onnx files
