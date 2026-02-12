# TalkFlow

Real-time, offline translation application with speech-to-speech capabilities.

## Features

- **Real-Time Translation**: Live speech translation with minimal latency
- **Offline Operation**: Works completely offline once models are downloaded
- **Voice Activity Detection**: Smart detection of speech segments
- **High-Quality TTS**: Natural-sounding synthesized speech output
- **Cross-Platform**: Runs on Windows and macOS
- **Optimized Performance**: Designed for 8GB RAM systems

## Architecture

```
Audio Input (Browser) 
    → WebSocket 
    → VAD (Voice Activity Detection)
    → ASR (faster-whisper)
    → Translation (Argos Translate)
    → TTS (Piper)
    → Audio Output
```

## Requirements

- Python 3.9 or higher
- 8GB RAM minimum (16GB recommended)
- Modern web browser with WebSocket support
- Microphone access

## Installation

1. **Clone or extract the repository**

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Download models**

   The application requires three types of models:

   ### Whisper (ASR)
   Models will be downloaded automatically on first run, or you can pre-download:
   ```bash
   # Models are downloaded to ~/.cache/huggingface/hub/
   # The 'small' model (~500MB) is used by default
   ```

   ### Argos Translate (Translation)
   Language packages are downloaded on demand:
   ```bash
   # Packages are downloaded when you select a language pair
   # Each package is ~100-200MB
   ```

   ### Piper (TTS)
   Download voices from: https://github.com/rhasspy/piper/releases
   ```bash
   # Example: Download en_US-lessac-medium
   # Place .onnx and .onnx.json files in models/piper/
   ```

## Configuration

Configuration is managed through environment variables or the `config.py` file.

Key settings:
- `SAMPLE_RATE`: Audio sample rate (default: 16000)
- `WHISPER_MODEL_SIZE`: Whisper model size (default: small)
- `WHISPER_COMPUTE_TYPE`: Quantization level (default: int8)
- `SOURCE_LANGUAGE`: Source language code (default: en)
- `TARGET_LANGUAGE`: Target language code (default: es)

## Usage

1. **Start the application**
   ```bash
   python -m backend.main
   ```

2. **Open your browser**
   Navigate to: `http://localhost:8000`

3. **Select languages**
   - Choose source language (language you'll speak)
   - Choose target language (language for translation)

4. **Start listening**
   - Click "Start Listening"
   - Allow microphone access when prompted
   - Begin speaking

5. **View results**
   - Transcription appears in real-time
   - Translation is displayed below
   - Synthesized audio plays automatically
   - Performance metrics are shown at the bottom

## Performance Optimization

The application is optimized for low-latency processing:

- **Quantized Models**: int8 quantization reduces memory usage
- **Phrase-based Chunking**: 0.8-1.2s buffers for optimal processing
- **Asynchronous Processing**: Non-blocking pipeline operations
- **Smart VAD**: Reduces unnecessary processing

Expected latencies on M2 Mac / 8GB RAM:
- VAD: <10ms
- ASR: 200-500ms
- Translation: 50-150ms
- TTS: 300-600ms
- **Total**: 600-1300ms

## Troubleshooting

### Models not loading
- Check that model paths in `config.py` are correct
- Ensure sufficient disk space for model downloads
- Check internet connection for initial downloads

### High latency
- Reduce `WHISPER_BEAM_SIZE` to 3 (faster but less accurate)
- Disable VAD for continuous processing
- Use smaller Whisper model (tiny/base)

### Audio issues
- Check microphone permissions in browser
- Verify audio input device in system settings
- Try refreshing the browser page

### WebSocket disconnections
- Check firewall settings
- Ensure port 8000 is not blocked
- Look for proxy/VPN issues

## Project Structure

```
TalkFlow/
├── backend/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── pipeline/
│   │   ├── vad.py             # Voice Activity Detection
│   │   ├── asr.py             # Automatic Speech Recognition
│   │   ├── translator.py      # Translation
│   │   ├── tts.py             # Text-to-Speech
│   │   ├── stabilizer.py      # Text stabilization
│   │   └── orchestrator.py    # Pipeline coordination
│   └── utils/
│       ├── audio_utils.py     # Audio processing utilities
│       ├── metrics.py         # Performance metrics
│       └── logger.py          # Logging configuration
├── frontend/
│   ├── index.html             # Main HTML page
│   ├── app.js                 # JavaScript application
│   └── styles.css             # Styling
├── models/
│   ├── whisper/               # Whisper models
│   ├── argos/                 # Argos translation models
│   └── piper/                 # Piper TTS voices
└── requirements.txt           # Python dependencies
```

## Supported Languages

### ASR (Whisper)
Supports 99 languages including:
- English (en), Spanish (es), French (fr), German (de)
- Italian (it), Portuguese (pt), Russian (ru), Japanese (ja)
- Chinese (zh), Arabic (ar), and many more

### Translation (Argos)
Supports 100+ language pairs. Most common:
- English ↔ Spanish, French, German, Italian, Portuguese
- Spanish ↔ French, Italian, Portuguese
- And many more combinations

### TTS (Piper)
Supports multiple languages with various voice options:
- English: US, UK, Australia
- Spanish: Spain, Latin America
- French, German, Italian, Portuguese, and more

## API Endpoints

- `GET /` - Main application page
- `GET /api/health` - Health check
- `GET /api/config` - Get current configuration
- `POST /api/config` - Update configuration
- `WebSocket /ws` - Real-time audio processing

## Development

### Running in development mode
```bash
# With auto-reload
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

### Environment variables
```bash
export LOG_LEVEL=DEBUG
export WHISPER_MODEL_SIZE=base
export ENABLE_METRICS=true
```

### Testing
```bash
# The application includes mock implementations for testing
# Set USE_MOCK_MODELS=true to test without downloading models
```

## License

This project uses several open-source components:
- faster-whisper: MIT License
- Argos Translate: MIT License
- Piper TTS: MIT License
- Silero VAD: MIT License

## Contributing

Contributions are welcome! Please ensure:
- Code follows existing style
- All components remain offline-capable
- Performance optimizations maintain quality
- Cross-platform compatibility is preserved

## Acknowledgments

- OpenAI Whisper team for the ASR model
- Argos Translate for offline translation
- Piper/Rhasspy for high-quality TTS
- Silero team for VAD model

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs in `logs/` directory
3. Ensure all dependencies are installed correctly
4. Verify model files are present and valid

---

**TalkFlow v1.0.0** - Offline Real-Time Translation
