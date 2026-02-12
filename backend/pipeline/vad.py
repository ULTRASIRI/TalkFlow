"""
Voice Activity Detection (VAD)
Uses WebRTC VAD or Silero VAD for speech detection
"""
import asyncio
import numpy as np
from typing import Optional, Tuple
import torch

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class VoiceActivityDetector:
    """
    Voice Activity Detection using Silero VAD
    Optimized for low-latency speech detection
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 threshold: float = 0.5,
                 min_speech_duration_ms: int = 250,
                 min_silence_duration_ms: int = 300,
                 speech_pad_ms: int = 100):
        """
        Initialize VAD
        
        Args:
            sample_rate: Audio sample rate
            threshold: Speech probability threshold (0-1)
            min_speech_duration_ms: Minimum speech duration to trigger
            min_silence_duration_ms: Minimum silence duration to end speech
            speech_pad_ms: Padding around speech segments
        """
        self.sample_rate = sample_rate
        self.threshold = threshold
        self.min_speech_duration_ms = min_speech_duration_ms
        self.min_silence_duration_ms = min_silence_duration_ms
        self.speech_pad_ms = speech_pad_ms
        
        self.model: Optional[torch.nn.Module] = None
        self.speech_buffer: list = []
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        
        # Frame buffer for accumulating samples
        self.frame_buffer = np.array([], dtype=np.float32)
        
        # VAD frame size (512 for 16kHz, 256 for 8kHz)
        self.vad_frame_size = 512 if sample_rate == 16000 else 256
        
        # Frame duration (assume 30ms frames for state tracking)
        self.frame_duration_ms = 30
        self.min_speech_frames = min_speech_duration_ms // self.frame_duration_ms
        self.min_silence_frames = min_silence_duration_ms // self.frame_duration_ms
        
        logger.info(f"VAD initialized: threshold={threshold}, sample_rate={sample_rate}Hz, frame_size={self.vad_frame_size}")
    
    async def initialize(self):
        """Load VAD model"""
        try:
            # Load Silero VAD model
            self.model, utils = torch.hub.load(
                repo_or_dir='snakers4/silero-vad',
                model='silero_vad',
                force_reload=False,
                onnx=False
            )
            
            self.model.eval()
            logger.info("Silero VAD model loaded successfully")
            
        except Exception as e:
            logger.warning(f"Failed to load Silero VAD: {e}. Using simple energy-based VAD.")
            self.model = None
    
    async def process(self, audio_chunk: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Process audio chunk and detect speech
        
        Args:
            audio_chunk: Audio data (numpy array)
        
        Returns:
            Tuple of (is_speech, speech_segment)
            - is_speech: True if speech detected
            - speech_segment: Complete speech segment when available, None otherwise
        """
        # Convert to float32 if needed
        if audio_chunk.dtype != np.float32:
            audio_chunk = audio_chunk.astype(np.float32) / 32768.0
        
        # Process audio in VAD-compatible frames
        is_speech_detected = False
        
        # Silero VAD requires exactly 512 samples for 16kHz (or 256 for 8kHz)
        vad_frame_size = 512 if self.sample_rate == 16000 else 256
        
        # Process chunk in VAD frames
        for i in range(0, len(audio_chunk), vad_frame_size):
            frame = audio_chunk[i:i + vad_frame_size]
            
            # Only process complete frames
            if len(frame) == vad_frame_size:
                is_speech = await self._detect_speech(frame)
                if is_speech:
                    is_speech_detected = True
        
        # Update state machine
        if is_speech_detected:
            self.speech_frames += 1
            self.silence_frames = 0
            
            # Add to buffer
            self.speech_buffer.append(audio_chunk)
            
            # Start speech if threshold met
            if not self.is_speaking and self.speech_frames >= self.min_speech_frames:
                self.is_speaking = True
                logger.debug("Speech started")
        
        else:
            self.silence_frames += 1
            
            if self.is_speaking:
                # Still add to buffer during silence (for padding)
                self.speech_buffer.append(audio_chunk)
                
                # End speech if silence threshold met
                if self.silence_frames >= self.min_silence_frames:
                    logger.debug(f"Speech ended after {len(self.speech_buffer)} chunks")
                    
                    # Return complete segment
                    segment = np.concatenate(self.speech_buffer) if self.speech_buffer else None
                    
                    # Reset state
                    self.speech_buffer = []
                    self.is_speaking = False
                    self.speech_frames = 0
                    self.silence_frames = 0
                    
                    return True, segment
        
        # No complete segment yet
        return is_speech_detected, None
    
    async def _detect_speech(self, audio_frame: np.ndarray) -> bool:
        """
        Detect if audio frame contains speech
        
        Args:
            audio_frame: Audio data (must be exactly 512 samples for 16kHz or 256 for 8kHz)
        
        Returns:
            True if speech detected
        """
        if self.model is not None:
            # Use Silero VAD
            try:
                # Verify frame size
                required_size = 512 if self.sample_rate == 16000 else 256
                if len(audio_frame) != required_size:
                    logger.warning(f"VAD frame size mismatch: got {len(audio_frame)}, expected {required_size}")
                    return self._energy_based_detection(audio_frame)
                
                # Convert to tensor
                audio_tensor = torch.from_numpy(audio_frame).float()
                
                # Get speech probability
                with torch.no_grad():
                    speech_prob = self.model(audio_tensor, self.sample_rate).item()
                
                return speech_prob > self.threshold
            
            except Exception as e:
                logger.error(f"VAD model error: {e}")
                # Fall back to energy-based detection
                return self._energy_based_detection(audio_frame)
        
        else:
            # Use simple energy-based detection
            return self._energy_based_detection(audio_frame)
    
    def _energy_based_detection(self, audio_chunk: np.ndarray) -> bool:
        """
        Simple energy-based speech detection
        
        Args:
            audio_chunk: Audio data
        
        Returns:
            True if energy above threshold
        """
        # Calculate RMS energy
        rms = np.sqrt(np.mean(audio_chunk ** 2))
        
        # Adaptive threshold (simple heuristic)
        energy_threshold = 0.01  # Adjust based on testing
        
        return rms > energy_threshold
    
    def reset(self):
        """Reset VAD state"""
        self.speech_buffer = []
        self.is_speaking = False
        self.speech_frames = 0
        self.silence_frames = 0
        self.frame_buffer = np.array([], dtype=np.float32)
        logger.debug("VAD state reset")
    
    def get_state(self) -> dict:
        """Get current VAD state"""
        return {
            "is_speaking": self.is_speaking,
            "speech_frames": self.speech_frames,
            "silence_frames": self.silence_frames,
            "buffer_size": len(self.speech_buffer)
        }


class PassthroughVAD:
    """
    Passthrough VAD for when VAD is disabled
    Simply buffers audio to target duration
    """
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 target_duration_ms: int = 1000):
        """
        Initialize passthrough VAD
        
        Args:
            sample_rate: Audio sample rate
            target_duration_ms: Target buffer duration in milliseconds
        """
        self.sample_rate = sample_rate
        self.target_samples = int(sample_rate * target_duration_ms / 1000)
        self.buffer = []
        self.total_samples = 0
        
        logger.info(f"Passthrough VAD initialized: {target_duration_ms}ms buffers")
    
    async def initialize(self):
        """No initialization needed"""
        pass
    
    async def process(self, audio_chunk: np.ndarray) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Buffer audio until target duration reached
        
        Args:
            audio_chunk: Audio data
        
        Returns:
            Tuple of (True, buffered_audio) when buffer full, (False, None) otherwise
        """
        self.buffer.append(audio_chunk)
        self.total_samples += len(audio_chunk)
        
        if self.total_samples >= self.target_samples:
            # Return buffered audio
            segment = np.concatenate(self.buffer)
            
            # Reset buffer
            self.buffer = []
            self.total_samples = 0
            
            return True, segment
        
        return False, None
    
    def reset(self):
        """Reset buffer"""
        self.buffer = []
        self.total_samples = 0
    
    def get_state(self) -> dict:
        """Get current state"""
        return {
            "buffer_size": len(self.buffer),
            "total_samples": self.total_samples,
            "target_samples": self.target_samples
        }
