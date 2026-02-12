# TalkFlow Patch Notes

## v2.1 - VAD Frame Size Fix (2026-02-12)

### Critical Bug Fix: Silero VAD Frame Size Error

**Problem:**
The Silero VAD model requires exact frame sizes for inference:
- 512 samples for 16kHz audio
- 256 samples for 8kHz audio

The application was sending 4096-sample chunks, causing this error:
```
ValueError: Provided number of samples is 4096 
(Supported values: 256 for 8000 sample rate, 512 for 16000)
```

**Root Cause:**
1. Frontend sent 4096-sample buffers (256ms at 16kHz)
2. Backend passed entire buffer to VAD model
3. VAD model validation rejected non-standard frame size
4. TorchScript execution halted

**Solution:**
Implemented frame-based streaming architecture:

1. **Frontend Changes (app.js):**
   - Reduced ScriptProcessor buffer: 4096 → 2048 samples
   - Better alignment with VAD requirements
   - Lower latency (256ms → 128ms)

2. **Backend Changes (vad.py):**
   - Added frame buffer for sample accumulation
   - Chunk processing into 512-sample frames
   - Process multiple frames per input chunk
   - Maintain remainder samples for next iteration

3. **Configuration (config.py):**
   - Updated default chunk duration: 1000ms → 128ms
   - Better real-time responsiveness
   - Optimal VAD frame alignment

### Technical Implementation

**Before:**
```python
# Single large chunk → VAD
audio_chunk = [4096 samples]  # ✗ INVALID
vad_model(audio_chunk)         # ValueError
```

**After:**
```python
# Chunk → Frame segmentation → VAD
audio_chunk = [2048 samples]
for i in range(0, len(chunk), 512):
    frame = chunk[i:i+512]
    if len(frame) == 512:      # ✓ VALID
        vad_model(frame)        # Success
```

### Performance Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Buffer size | 4096 samples | 2048 samples | -50% |
| Latency | 256ms | 128ms | -50% |
| VAD calls/chunk | 1 (failed) | 4 (success) | +300% |
| Frame alignment | 0% | 100% | +100% |

### Benefits

1. **Stability:** VAD no longer crashes
2. **Lower Latency:** Faster audio processing
3. **Better Detection:** More frequent VAD updates
4. **Real-time:** Improved responsiveness

### Backward Compatibility

✅ Fully backward compatible
- Existing configurations still work
- Default values updated for optimal performance
- No breaking changes to API

### Migration Guide

**Automatic (Recommended):**
No action needed - defaults are optimized.

**Manual (Optional):**
If you have custom `.env` settings:

```bash
# Old settings (still work but not optimal)
CHUNK_DURATION_MS=1000

# New recommended settings
CHUNK_DURATION_MS=128  # Better VAD alignment
```

### Additional Fixes

1. **Frame Buffer Management:**
   - Accumulates partial frames
   - Ensures no sample loss
   - Maintains audio continuity

2. **Error Handling:**
   - Graceful fallback to energy-based VAD
   - Detailed logging for debugging
   - Warning for frame size mismatches

3. **State Management:**
   - Frame buffer reset on VAD reset
   - Proper cleanup on stop
   - Memory leak prevention

### Testing Performed

- ✅ 16kHz audio with 512-sample frames
- ✅ 8kHz audio with 256-sample frames
- ✅ Variable input chunk sizes
- ✅ Continuous streaming
- ✅ Speech detection accuracy
- ✅ Memory stability over time

### Known Limitations

1. **Sample Rate:** Must be 16kHz or 8kHz for Silero VAD
2. **Frame Size:** Fixed at 512 (16kHz) or 256 (8kHz)
3. **Buffer Alignment:** Input chunks should be multiples of frame size

### Files Changed

```
backend/pipeline/vad.py         # Frame-based processing
backend/config.py               # Default chunk size
frontend/app.js                 # Audio buffer size
```

### Next Steps

Future enhancements:
- [ ] Support for variable sample rates
- [ ] Adaptive frame buffering
- [ ] GPU acceleration for VAD
- [ ] Alternative VAD models

---

## Previous Versions

### v2.0 - Python 3.13 Support (2026-02-12)

- ✅ Updated dependencies for Python 3.13
- ✅ Automated model downloader
- ✅ Installation scripts
- ✅ Comprehensive documentation

### v1.0 - Initial Release

- ✅ Complete translation pipeline
- ✅ Offline operation
- ✅ Cross-platform support
- ✅ Real-time processing

---

**Current Version:** v2.1  
**Release Date:** February 12, 2026  
**Status:** Stable
