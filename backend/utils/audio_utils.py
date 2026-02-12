"""
Audio Utilities
Helper functions for audio processing and conversion
"""
import numpy as np
import wave
import io
from typing import Optional

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class AudioProcessor:
    """Audio processing utilities"""
    
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """
        Initialize audio processor
        
        Args:
            sample_rate: Target sample rate
            channels: Number of channels
        """
        self.sample_rate = sample_rate
        self.channels = channels
    
    def bytes_to_array(self, audio_bytes: bytes) -> Optional[np.ndarray]:
        """
        Convert audio bytes to numpy array
        
        Args:
            audio_bytes: Raw audio bytes (PCM 16-bit)
        
        Returns:
            Numpy array (float32, normalized to [-1, 1])
        """
        try:
            # Convert bytes to int16 array
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)
            
            # Normalize to float32 [-1, 1]
            audio_float = audio_int16.astype(np.float32) / 32768.0
            
            return audio_float
        
        except Exception as e:
            logger.error(f"Failed to convert bytes to array: {e}")
            return None
    
    def array_to_bytes(self, audio_array: np.ndarray) -> bytes:
        """
        Convert numpy array to audio bytes
        
        Args:
            audio_array: Numpy array (float32)
        
        Returns:
            Raw audio bytes (PCM 16-bit)
        """
        # Ensure float32
        if audio_array.dtype != np.float32:
            audio_array = audio_array.astype(np.float32)
        
        # Clip to [-1, 1]
        audio_array = np.clip(audio_array, -1.0, 1.0)
        
        # Convert to int16
        audio_int16 = (audio_array * 32767).astype(np.int16)
        
        return audio_int16.tobytes()
    
    def resample(self, 
                 audio: np.ndarray, 
                 orig_sr: int, 
                 target_sr: int) -> np.ndarray:
        """
        Resample audio (simple linear interpolation)
        
        Args:
            audio: Audio array
            orig_sr: Original sample rate
            target_sr: Target sample rate
        
        Returns:
            Resampled audio
        """
        if orig_sr == target_sr:
            return audio
        
        # Calculate ratio
        ratio = target_sr / orig_sr
        
        # New length
        new_length = int(len(audio) * ratio)
        
        # Create indices for interpolation
        old_indices = np.arange(len(audio))
        new_indices = np.linspace(0, len(audio) - 1, new_length)
        
        # Interpolate
        resampled = np.interp(new_indices, old_indices, audio)
        
        return resampled.astype(audio.dtype)
    
    def normalize(self, audio: np.ndarray, target_level: float = 0.9) -> np.ndarray:
        """
        Normalize audio to target level
        
        Args:
            audio: Audio array
            target_level: Target peak level (0-1)
        
        Returns:
            Normalized audio
        """
        max_val = np.abs(audio).max()
        
        if max_val > 0:
            return audio * (target_level / max_val)
        
        return audio
    
    def apply_gain(self, audio: np.ndarray, gain_db: float) -> np.ndarray:
        """
        Apply gain to audio
        
        Args:
            audio: Audio array
            gain_db: Gain in decibels
        
        Returns:
            Audio with gain applied
        """
        gain_linear = 10 ** (gain_db / 20)
        return audio * gain_linear
    
    def detect_silence(self, 
                      audio: np.ndarray, 
                      threshold: float = 0.01,
                      min_duration_ms: int = 300) -> bool:
        """
        Detect if audio is silence
        
        Args:
            audio: Audio array
            threshold: Silence threshold (RMS)
            min_duration_ms: Minimum duration for silence
        
        Returns:
            True if audio is silence
        """
        # Calculate RMS
        rms = np.sqrt(np.mean(audio ** 2))
        
        # Check threshold
        is_silence = rms < threshold
        
        # Check duration (assuming sample rate is known)
        duration_ms = len(audio) / self.sample_rate * 1000
        
        return is_silence and duration_ms >= min_duration_ms
    
    def remove_dc_offset(self, audio: np.ndarray) -> np.ndarray:
        """
        Remove DC offset from audio
        
        Args:
            audio: Audio array
        
        Returns:
            Audio with DC offset removed
        """
        return audio - np.mean(audio)
    
    def apply_fade(self,
                   audio: np.ndarray,
                   fade_in_ms: int = 10,
                   fade_out_ms: int = 10) -> np.ndarray:
        """
        Apply fade in/out to prevent clicks
        
        Args:
            audio: Audio array
            fade_in_ms: Fade in duration
            fade_out_ms: Fade out duration
        
        Returns:
            Audio with fades applied
        """
        fade_in_samples = int(self.sample_rate * fade_in_ms / 1000)
        fade_out_samples = int(self.sample_rate * fade_out_ms / 1000)
        
        result = audio.copy()
        
        # Fade in
        if fade_in_samples > 0 and len(result) > fade_in_samples:
            fade_in_curve = np.linspace(0, 1, fade_in_samples)
            result[:fade_in_samples] *= fade_in_curve
        
        # Fade out
        if fade_out_samples > 0 and len(result) > fade_out_samples:
            fade_out_curve = np.linspace(1, 0, fade_out_samples)
            result[-fade_out_samples:] *= fade_out_curve
        
        return result
    
    def create_wav_bytes(self, 
                        audio: np.ndarray,
                        sample_rate: Optional[int] = None) -> bytes:
        """
        Create WAV file bytes from audio array
        
        Args:
            audio: Audio array (float32)
            sample_rate: Sample rate (uses default if None)
        
        Returns:
            WAV file bytes
        """
        sr = sample_rate or self.sample_rate
        
        # Convert to int16
        audio_int16 = (np.clip(audio, -1.0, 1.0) * 32767).astype(np.int16)
        
        # Create WAV in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sr)
            wav_file.writeframes(audio_int16.tobytes())
        
        return wav_buffer.getvalue()
    
    def read_wav_bytes(self, wav_bytes: bytes) -> tuple:
        """
        Read WAV file from bytes
        
        Args:
            wav_bytes: WAV file bytes
        
        Returns:
            Tuple of (audio_array, sample_rate)
        """
        wav_buffer = io.BytesIO(wav_bytes)
        
        with wave.open(wav_buffer, 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            frames = wav_file.readframes(wav_file.getnframes())
            
            # Convert to numpy array
            audio_int16 = np.frombuffer(frames, dtype=np.int16)
            
            # Handle stereo
            if channels == 2:
                audio_int16 = audio_int16.reshape(-1, 2).mean(axis=1).astype(np.int16)
            
            # Normalize to float32
            audio_float = audio_int16.astype(np.float32) / 32768.0
            
            return audio_float, sample_rate
    
    def calculate_rms(self, audio: np.ndarray) -> float:
        """
        Calculate RMS energy
        
        Args:
            audio: Audio array
        
        Returns:
            RMS value
        """
        return np.sqrt(np.mean(audio ** 2))
    
    def calculate_peak(self, audio: np.ndarray) -> float:
        """
        Calculate peak level
        
        Args:
            audio: Audio array
        
        Returns:
            Peak value
        """
        return np.abs(audio).max()
