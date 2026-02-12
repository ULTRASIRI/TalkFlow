# TalkFlow Project Structure

Complete overview of the TalkFlow application architecture and file organization.

## Directory Tree

```
TalkFlow/
├── backend/                    # Python backend (FastAPI)
│   ├── __init__.py            # Package initialization
│   ├── main.py                # Application entry point
│   ├── config.py              # Configuration management
│   ├── pipeline/              # Processing pipeline
│   │   ├── __init__.py       # Pipeline package
│   │   ├── vad.py            # Voice Activity Detection
│   │   ├── asr.py            # Speech Recognition (Whisper)
│   │   ├── translator.py     # Translation (Argos)
│   │   ├── tts.py            # Text-to-Speech (Piper)
│   │   ├── stabilizer.py     # Text stabilization
│   │   └── orchestrator.py   # Pipeline coordination
│   └── utils/                 # Utility modules
│       ├── __init__.py       # Utils package
│       ├── audio_utils.py    # Audio processing
│       ├── metrics.py        # Performance tracking
│       └── logger.py         # Logging configuration
│
├── frontend/                   # Web frontend
│   ├── index.html            # Main HTML page
│   ├── app.js                # JavaScript application
│   └── styles.css            # CSS styling
│
├── models/                     # AI models directory
│   ├── README.md             # Model documentation
│   ├── whisper/              # Whisper ASR models
│   ├── argos/                # Argos translation models
│   └── piper/                # Piper TTS voices
│
├── README.md                   # Main documentation
├── QUICKSTART.md              # Quick start guide
├── LICENSE                    # MIT License
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── run.py                     # Convenience run script
├── verify.py                  # System verification
├── .env.example              # Environment template
└── .gitignore                # Git ignore rules
```

## Component Architecture

### Backend Components

#### 1. Main Application (main.py)
- FastAPI server setup
- WebSocket endpoint handling
- Route definitions
- Connection management

#### 2. Configuration (config.py)
- Centralized settings
- Environment variable loading
- Model path configuration
- Performance parameters

#### 3. Pipeline Components

**Voice Activity Detection (vad.py)**
- Silero VAD integration
- Speech segment detection
- Silence detection
- Passthrough mode for continuous processing

**Speech Recognition (asr.py)**
- faster-whisper integration
- Optimized int8 quantization
- Async transcription
- Multi-language support

**Translation (translator.py)**
- Argos Translate integration
- Offline neural translation
- Language pair management
- Batch translation support

**Text-to-Speech (tts.py)**
- Piper TTS integration
- High-quality voice synthesis
- Streaming audio generation
- Voice selection

**Text Stabilization (stabilizer.py)**
- Prevents output flickering
- Longest common subsequence
- Phrase buffering
- Progressive display

**Pipeline Orchestrator (orchestrator.py)**
- Component coordination
- End-to-end processing
- State management
- Error handling

#### 4. Utilities

**Audio Processing (audio_utils.py)**
- Format conversions
- Resampling
- Normalization
- WAV file operations

**Metrics Collection (metrics.py)**
- Latency tracking
- Performance monitoring
- Statistical analysis
- Rolling windows

**Logging (logger.py)**
- Structured logging
- Multiple outputs
- Level management
- Context managers

### Frontend Components

#### 1. HTML Interface (index.html)
- Modern, accessible UI
- Language selectors
- Control buttons
- Real-time displays
- Metrics dashboard

#### 2. JavaScript Application (app.js)
- WebSocket communication
- Audio capture (MediaDevices API)
- Real-time UI updates
- State management
- Error handling

#### 3. Styling (styles.css)
- Modern dark theme
- Responsive design
- Smooth animations
- Accessibility features

## Data Flow

```
User Microphone
    ↓
Browser MediaDevices API
    ↓
PCM Audio (16-bit, 16kHz)
    ↓
WebSocket
    ↓
Backend: Audio Buffer
    ↓
VAD (Voice Activity Detection)
    ↓ (speech segments)
ASR (faster-whisper)
    ↓ (text)
Text Stabilizer
    ↓ (stable text)
Translator (Argos)
    ↓ (translated text)
TTS (Piper)
    ↓ (audio bytes)
WebSocket
    ↓
Browser Audio Player
    ↓
User Speakers
```

## Processing Pipeline

### Stage 1: Audio Capture
- Browser captures microphone input
- Converts to PCM 16-bit mono
- Sends via WebSocket in chunks

### Stage 2: Voice Activity Detection
- Analyzes audio for speech
- Buffers speech segments
- Detects silence boundaries
- Outputs complete phrases

### Stage 3: Speech Recognition
- Transcribes audio to text
- Uses Whisper model
- Returns confidence scores
- Supports 99 languages

### Stage 4: Text Stabilization
- Prevents flickering output
- Ensures progressive display
- Buffers partial results
- Outputs stable text

### Stage 5: Translation
- Translates text to target language
- Uses Argos neural models
- Preserves context
- Handles idioms

### Stage 6: Text-to-Speech
- Synthesizes natural speech
- Uses Piper neural TTS
- Generates WAV audio
- Adjustable speed/voice

### Stage 7: Audio Playback
- Sends audio via WebSocket
- Browser plays audio
- Displays metrics
- Updates UI

## Key Design Principles

### 1. Offline-First
- All models run locally
- No internet required after setup
- Privacy-focused
- No data sent to cloud

### 2. Low-Latency
- Async processing throughout
- Optimized models (int8)
- Smart buffering
- Parallel execution where possible

### 3. Cross-Platform
- OS-agnostic paths
- Browser-based audio capture
- Python 3.9+ compatibility
- Works on Windows/macOS/Linux

### 4. Modular Design
- Clean separation of concerns
- Pluggable components
- Easy to extend
- Mock implementations for testing

### 5. Resource-Efficient
- Optimized for 8GB RAM
- Quantized models
- Smart memory management
- Configurable performance

## Configuration Options

### Audio Settings
- Sample rate (default: 16kHz)
- Channel count (mono/stereo)
- Chunk duration (buffer size)
- Resampling options

### VAD Settings
- Threshold (speech detection)
- Min speech duration
- Min silence duration
- Speech padding

### ASR Settings
- Model size (tiny to large)
- Compute type (int8, float16)
- Beam size (accuracy vs speed)
- Language selection

### Translation Settings
- Language pairs
- Device (CPU/GPU)
- Batch processing

### TTS Settings
- Voice selection
- Speaker ID
- Speed adjustment
- Quality settings

## Performance Characteristics

### Memory Usage
- Whisper small (int8): ~240MB
- Argos models: ~150MB per pair
- Piper voice: ~50MB
- Total baseline: ~500-800MB

### Latency Targets
- VAD: <10ms
- ASR: 200-500ms
- Translation: 50-150ms
- TTS: 300-600ms
- **Total**: 600-1300ms

### Throughput
- Real-time factor: 0.1-0.3x
- Can process faster than real-time
- Limited by model inference speed

## Extension Points

### Adding New Languages
1. Update language selectors in HTML
2. Download Argos language package
3. Download Piper voice for language
4. Update configuration

### Custom Models
1. Implement model interface
2. Add to pipeline configuration
3. Update model loading logic
4. Test with existing pipeline

### Additional Features
- Recording/playback
- Text editing
- Multiple speakers
- Conversation history
- Export functionality

## Testing Strategy

### Unit Tests
- Individual components
- Mock external dependencies
- Edge case handling
- Error conditions

### Integration Tests
- Pipeline end-to-end
- WebSocket communication
- Audio processing chain
- Model interactions

### Performance Tests
- Latency benchmarks
- Memory profiling
- Throughput testing
- Resource monitoring

## Deployment Options

### Local Desktop
- Run with Python directly
- Package as standalone app
- System tray integration
- Auto-start options

### Docker Container
- Containerized deployment
- Cross-platform consistency
- Easy distribution
- Isolated environment

### Web Server
- Deploy on local network
- Multiple client support
- Centralized processing
- Shared resources

## Security Considerations

### Privacy
- All processing local
- No data transmission
- No logging of transcripts
- Microphone permission control

### Network
- Local-only by default
- HTTPS optional
- CORS configuration
- WebSocket security

## Future Enhancements

### Planned Features
- Multi-speaker support
- Conversation history
- Text correction
- Custom vocabulary
- Batch file processing

### Performance Improvements
- GPU acceleration
- Model caching
- Streaming optimization
- Parallel processing

### UI Enhancements
- Mobile app
- Offline PWA
- Dark/light themes
- Accessibility features

---

**Version:** 1.0.0
**Last Updated:** 2024
