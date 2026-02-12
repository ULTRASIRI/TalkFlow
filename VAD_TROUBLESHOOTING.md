# VAD Troubleshooting Guide

Common issues with Voice Activity Detection and their solutions.

## Error: "Provided number of samples is X (Supported values: 256/512)"

### Symptoms
```
ValueError: Provided number of samples is 4096 
(Supported values: 256 for 8000 sample rate, 512 for 16000)
```

### Cause
Silero VAD requires exact frame sizes:
- **16kHz audio:** 512 samples per frame
- **8kHz audio:** 256 samples per frame

### Solution ✓ (Fixed in v2.1)
This is now automatically handled. The system:
1. Buffers incoming audio
2. Segments into proper frame sizes
3. Processes each frame individually

### Verification
```bash
# Check your settings
grep CHUNK_DURATION_MS .env
# Should show: CHUNK_DURATION_MS=128

grep SAMPLE_RATE .env
# Should show: SAMPLE_RATE=16000
```

## VAD Not Detecting Speech

### Symptoms
- No transcription appears
- Metrics show 0ms processing
- "Start Listening" active but nothing happens

### Possible Causes

1. **Microphone Not Working**
   ```bash
   # Test microphone
   # macOS: System Settings → Sound → Input
   # Windows: Settings → Privacy → Microphone
   ```

2. **VAD Threshold Too High**
   ```bash
   # In .env file
   VAD_THRESHOLD=0.5  # Try lower values
   VAD_THRESHOLD=0.3  # More sensitive
   ```

3. **VAD Disabled**
   ```bash
   # Check .env
   VAD_ENABLED=true  # Should be true
   ```

### Solutions

**Test with VAD disabled:**
```bash
# Temporarily disable VAD
export VAD_ENABLED=false
python run.py
```

If this works, VAD configuration needs adjustment.

**Adjust sensitivity:**
```bash
# Lower threshold for more sensitivity
export VAD_THRESHOLD=0.3
python run.py
```

**Check browser console:**
```javascript
// Open browser DevTools (F12)
// Look for WebSocket errors
// Check for audio permission issues
```

## VAD Too Sensitive (False Positives)

### Symptoms
- Detects speech when quiet
- Continuous processing
- High CPU usage

### Solutions

**Increase threshold:**
```bash
# In .env
VAD_THRESHOLD=0.7  # Less sensitive
```

**Increase silence duration:**
```bash
# Require longer silence to end speech
VAD_MIN_SILENCE_DURATION_MS=500  # Default: 300
```

**Add noise gate:**
```bash
# Increase minimum speech duration
VAD_MIN_SPEECH_DURATION_MS=400  # Default: 250
```

## VAD Model Loading Errors

### Symptoms
```
WARNING: Failed to load Silero VAD: ...
WARNING: Using Mock VAD - for testing only
```

### Cause
Silero VAD model download failed

### Solution

**Manual model check:**
```bash
python -c "
import torch
model, utils = torch.hub.load(
    repo_or_dir='snakers4/silero-vad',
    model='silero_vad',
    force_reload=True
)
print('VAD model loaded successfully')
"
```

**Clear cache and retry:**
```bash
# Clear torch hub cache
rm -rf ~/.cache/torch/hub/snakers4_silero-vad_*

# Restart application
python run.py
```

## Sample Rate Mismatch

### Symptoms
```
WARNING: VAD requires 16kHz audio, current rate may cause issues
```

### Cause
Audio sample rate is not 16kHz or 8kHz

### Solution

**Use 16kHz (recommended):**
```bash
# In .env
SAMPLE_RATE=16000
```

**Or use 8kHz:**
```bash
# In .env
SAMPLE_RATE=8000
# VAD will use 256-sample frames
```

## Frame Buffer Issues

### Symptoms
- Choppy audio processing
- Delayed speech detection
- Audio segments cut off

### Diagnosis

**Check buffer settings:**
```bash
# Current settings
grep "BUFFER" .env

# Recommended:
MIN_BUFFER_DURATION_MS=800
MAX_BUFFER_DURATION_MS=1200
BUFFER_OVERLAP_MS=100
```

### Solutions

**Increase buffer size:**
```bash
# Allow longer audio segments
MAX_BUFFER_DURATION_MS=2000
```

**Add overlap:**
```bash
# Prevent cutting speech
BUFFER_OVERLAP_MS=200
```

## Performance Issues

### Symptoms
- High latency
- Slow processing
- Memory usage growing

### Solutions

**Disable VAD temporarily:**
```bash
# Use passthrough mode
VAD_ENABLED=false
# Processes at fixed intervals
```

**Reduce processing:**
```bash
# Smaller chunks
CHUNK_DURATION_MS=64

# Larger chunks (less frequent processing)
CHUNK_DURATION_MS=256
```

**Monitor performance:**
```bash
# Check VAD latency in browser
# Should be < 10ms per chunk
```

## Browser-Specific Issues

### Chrome
- ✅ Best support
- Issue: Microphone permission modal
- Solution: Grant permission and reload

### Firefox
- ✅ Good support
- Issue: WebSocket buffer limits
- Solution: Reduce chunk size

### Safari (macOS)
- ✅ Good support
- Issue: Audio context suspension
- Solution: User interaction required before audio

## Advanced Debugging

### Enable Debug Logging

```bash
# In .env or command line
LOG_LEVEL=DEBUG
python run.py
```

### Monitor VAD State

```python
# In Python console during runtime
import asyncio
from backend.pipeline.vad import VoiceActivityDetector

# Get VAD instance from orchestrator
vad_state = orchestrator.vad.get_state()
print(vad_state)
# Shows: is_speaking, speech_frames, silence_frames, buffer_size
```

### Test VAD Directly

```python
import numpy as np
from backend.pipeline.vad import VoiceActivityDetector

# Create VAD
vad = VoiceActivityDetector(sample_rate=16000)
asyncio.run(vad.initialize())

# Test with 512-sample frame
audio_frame = np.random.randn(512).astype(np.float32) * 0.1
is_speech, segment = asyncio.run(vad.process(audio_frame))
print(f"Speech detected: {is_speech}")
```

## Configuration Reference

### Optimal Settings (Default v2.1)

```bash
# Audio
SAMPLE_RATE=16000
CHANNELS=1
CHUNK_DURATION_MS=128

# VAD
VAD_ENABLED=true
VAD_THRESHOLD=0.5
VAD_MIN_SPEECH_DURATION_MS=250
VAD_MIN_SILENCE_DURATION_MS=300
VAD_SPEECH_PAD_MS=100
```

### Low-Latency Settings

```bash
CHUNK_DURATION_MS=64
VAD_MIN_SPEECH_DURATION_MS=150
VAD_MIN_SILENCE_DURATION_MS=200
```

### High-Accuracy Settings

```bash
CHUNK_DURATION_MS=256
VAD_THRESHOLD=0.6
VAD_MIN_SPEECH_DURATION_MS=400
VAD_MIN_SILENCE_DURATION_MS=500
```

### Noisy Environment

```bash
VAD_THRESHOLD=0.7
VAD_MIN_SPEECH_DURATION_MS=500
# Helps filter background noise
```

## Getting Help

If issues persist:

1. **Check logs:**
   ```bash
   tail -f logs/talkflow.log
   ```

2. **Run verification:**
   ```bash
   python verify.py
   ```

3. **Test without VAD:**
   ```bash
   VAD_ENABLED=false python run.py
   ```

4. **Check model loading:**
   ```bash
   python -c "import torch; print(torch.__version__)"
   python -c "import torch; torch.hub.list('snakers4/silero-vad')"
   ```

## Quick Fixes Summary

| Issue | Quick Fix |
|-------|-----------|
| Frame size error | ✓ Fixed in v2.1 |
| Not detecting speech | Lower VAD_THRESHOLD to 0.3 |
| Too sensitive | Raise VAD_THRESHOLD to 0.7 |
| Model loading fails | Clear cache: `rm -rf ~/.cache/torch/hub/` |
| High latency | Reduce CHUNK_DURATION_MS to 64 |
| Choppy audio | Increase MAX_BUFFER_DURATION_MS |

---

**Version:** 2.1  
**Last Updated:** February 12, 2026
