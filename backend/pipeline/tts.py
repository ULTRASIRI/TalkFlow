"""
Text-to-Speech (TTS)
Uses Piper for high-quality offline speech synthesis
"""
import asyncio
import numpy as np
from typing import Optional
from pathlib import Path
import wave
import io

try:
    from piper import PiperVoice
    PIPER_AVAILABLE = True
except ImportError:
    PIPER_AVAILABLE = False

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class TTSEngine:
    """
    Text-to-Speech engine using Piper
    Fast, offline neural TTS
    """
    
    def __init__(self,
                 model_path: Path,
                 voice: str = "en_US-lessac-medium",
                 speaker: int = 0,
                 length_scale: float = 1.0,
                 noise_scale: float = 0.667,
                 noise_w: float = 0.8):
        """
        Initialize TTS engine
        
        Args:
            model_path: Path to Piper models
            voice: Voice model name
            speaker: Speaker ID (for multi-speaker models)
            length_scale: Speech speed (1.0 = normal)
            noise_scale: Variability in speech
            noise_w: Variability in duration
        """
        self.model_path = model_path
        self.voice = voice
        self.speaker = speaker
        self.length_scale = length_scale
        self.noise_scale = noise_scale
        self.noise_w = noise_w
        
        self.model: Optional[PiperVoice] = None
        self.sample_rate = 22050  # Piper default
        
        if not PIPER_AVAILABLE:
            logger.warning("Piper TTS not available")
        
        logger.info(f"TTS initialized: voice={voice}, speaker={speaker}")
    
    async def initialize(self):
        """Load TTS model"""
        if not PIPER_AVAILABLE:
            logger.warning("Skipping TTS initialization - Piper not available")
            return
        
        try:
            # Construct model path
            model_file = self.model_path / f"{self.voice}.onnx"
            config_file = self.model_path / f"{self.voice}.onnx.json"
            
            if not model_file.exists():
                logger.warning(f"TTS model not found: {model_file}")
                return
            
            logger.info(f"Loading Piper voice from {model_file}")
            
            # Load model in thread pool
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                PiperVoice.load,
                str(model_file),
                str(config_file) if config_file.exists() else None
            )
            
            # Update sample rate from model
            if hasattr(self.model, 'config'):
                self.sample_rate = self.model.config.sample_rate
            
            logger.info(f"Piper voice loaded successfully (sample_rate={self.sample_rate}Hz)")
        
        except Exception as e:
            logger.error(f"Failed to load TTS model: {e}", exc_info=True)
    
    async def synthesize(self, text: str) -> Optional[bytes]:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes (WAV format) or None on error
        """
        if not PIPER_AVAILABLE or self.model is None:
            logger.debug("TTS skipped - not available")
            return None
        
        if not text or not text.strip():
            return None
        
        try:
            # Synthesize in thread pool
            loop = asyncio.get_event_loop()
            audio_bytes = await loop.run_in_executor(
                None,
                self._synthesize_sync,
                text
            )
            
            return audio_bytes
        
        except Exception as e:
            logger.error(f"TTS synthesis error: {e}")
            return None
    
    def _synthesize_sync(self, text: str) -> bytes:
        """
        Synchronous synthesis (runs in thread pool)
        
        Args:
            text: Text to synthesize
        
        Returns:
            Audio bytes in WAV format
        """
        # Synthesize audio - handle different Piper API versions
        audio_samples = []
        
        try:
            # Try newer API (synthesize_stream_raw)
            if hasattr(self.model, 'synthesize_stream_raw'):
                for audio_chunk in self.model.synthesize_stream_raw(
                    text,
                    speaker_id=self.speaker,
                    length_scale=self.length_scale,
                    noise_scale=self.noise_scale,
                    noise_w=self.noise_w
                ):
                    audio_samples.append(audio_chunk)
            
            # Try older API (synthesize)
            elif hasattr(self.model, 'synthesize'):
                result = self.model.synthesize(
                    text,
                    speaker_id=self.speaker,
                    length_scale=self.length_scale,
                    noise_scale=self.noise_scale,
                    noise_w=self.noise_w
                )
                # Result might be tuple (audio, sample_rate) or just audio
                if isinstance(result, tuple):
                    audio_data = result[0]
                else:
                    audio_data = result
                
                # Convert to list if needed
                if isinstance(audio_data, np.ndarray):
                    audio_samples = [audio_data]
                else:
                    audio_samples = [np.array(audio_data)]
            
            # Fallback to __call__ method
            else:
                result = self.model(text)
                if isinstance(result, tuple):
                    audio_data = result[0]
                else:
                    audio_data = result
                audio_samples = [np.array(audio_data)]
        
        except Exception as e:
            logger.error(f"Piper synthesis failed with all methods: {e}")
            raise
        
        # Combine chunks
        if not audio_samples:
            raise ValueError("No audio generated")
        
        audio_data = np.concatenate(audio_samples)
        
        # Convert to bytes (PCM 16-bit)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        
        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_buffer.getvalue()
    
    async def synthesize_streaming(self, text: str):
        """
        Synthesize speech with streaming output
        
        Args:
            text: Text to synthesize
        
        Yields:
            Audio chunks as they are generated
        """
        if not PIPER_AVAILABLE or self.model is None:
            return
        
        try:
            loop = asyncio.get_event_loop()
            
            # Run synthesis in thread pool
            for chunk in await loop.run_in_executor(
                None,
                self._synthesize_streaming_sync,
                text
            ):
                yield chunk
        
        except Exception as e:
            logger.error(f"Streaming TTS error: {e}")
    
    def _synthesize_streaming_sync(self, text: str):
        """
        Synchronous streaming synthesis
        
        Args:
            text: Text to synthesize
        
        Yields:
            Audio chunks
        """
        for audio_chunk in self.model.synthesize_stream_raw(
            text,
            speaker_id=self.speaker,
            length_scale=self.length_scale,
            noise_scale=self.noise_scale,
            noise_w=self.noise_w
        ):
            # Convert to int16
            audio_int16 = (audio_chunk * 32767).astype(np.int16)
            yield audio_int16.tobytes()
    
    def set_voice(self, voice: str):
        """
        Change voice
        
        Args:
            voice: New voice name
        """
        self.voice = voice
        logger.info(f"Voice changed to: {voice}")
        # Will need to reload model
        self.model = None
    
    def set_speed(self, speed: float):
        """
        Adjust speech speed
        
        Args:
            speed: Speed multiplier (1.0 = normal, >1.0 = faster, <1.0 = slower)
        """
        self.length_scale = 1.0 / speed  # Inverse relationship
        logger.info(f"Speech speed set to: {speed}x")
    
    def get_available_voices(self) -> list:
        """
        Get list of available voices
        
        Returns:
            List of voice names
        """
        if not self.model_path.exists():
            return []
        
        # Find all .onnx files
        voices = []
        for model_file in self.model_path.glob("*.onnx"):
            if not model_file.name.endswith(".onnx.json"):
                voice_name = model_file.stem
                voices.append(voice_name)
        
        return voices
    
    async def cleanup(self):
        """Cleanup resources"""
        self.model = None
        logger.info("TTS engine cleaned up")


class MockTTS:
    """Mock TTS for testing"""
    
    async def initialize(self):
        logger.warning("Using Mock TTS - for testing only")
    
    async def synthesize(self, text: str) -> Optional[bytes]:
        await asyncio.sleep(0.1)  # Simulate processing
        
        # Generate simple beep sound
        sample_rate = 16000
        duration = 0.5
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * frequency * t) * 0.3
        audio_int16 = (audio * 32767).astype(np.int16)
        
        # Create WAV
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_buffer.getvalue()
    
    def set_voice(self, voice: str):
        pass
    
    def set_speed(self, speed: float):
        pass
    
    async def cleanup(self):
        pass
