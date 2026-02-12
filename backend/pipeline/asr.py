"""
Automatic Speech Recognition (ASR)
Uses faster-whisper for efficient transcription
"""
import asyncio
import numpy as np
from typing import Optional, Dict, List
from pathlib import Path

from faster_whisper import WhisperModel

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class ASREngine:
    """
    ASR Engine using faster-whisper
    Optimized for low-latency transcription with int8 quantization
    """
    
    def __init__(self,
                 model_path: Path,
                 model_size: str = "small",
                 compute_type: str = "int8",
                 device: str = "cpu",
                 language: str = "en",
                 beam_size: int = 5,
                 num_workers: int = 1):
        """
        Initialize ASR engine
        
        Args:
            model_path: Path to Whisper model
            model_size: Model size (tiny, base, small, medium, large)
            compute_type: Compute type (int8, float16, float32)
            device: Device to run on (cpu, cuda)
            language: Source language code
            beam_size: Beam size for decoding
            num_workers: Number of CPU workers
        """
        self.model_path = model_path
        self.model_size = model_size
        self.compute_type = compute_type
        self.device = device
        self.language = language
        self.beam_size = beam_size
        self.num_workers = num_workers
        
        self.model: Optional[WhisperModel] = None
        
        logger.info(
            f"ASR initialized: model={model_size}, compute={compute_type}, "
            f"device={device}, language={language}"
        )
    
    async def initialize(self):
        """Load Whisper model"""
        try:
            logger.info(f"Loading Whisper model from {self.model_path}")
            
            # Initialize model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None,
                self._load_model
            )
            
            logger.info("Whisper model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}", exc_info=True)
            raise
    
    def _load_model(self) -> WhisperModel:
        """Load model (blocking operation)"""
        # Check if model exists locally
        model_path_str = None
        
        if self.model_path.exists():
            # Check for model files in directory
            model_files = list(self.model_path.glob("*.bin")) + list(self.model_path.glob("model.bin"))
            
            if model_files:
                model_path_str = str(self.model_path)
                logger.info(f"Using local Whisper model from {model_path_str}")
            else:
                logger.warning(f"No model files found in {self.model_path}, will download")
                model_path_str = self.model_size
        else:
            # Download model
            logger.info(f"Model directory not found, downloading {self.model_size}")
            model_path_str = self.model_size
        
        try:
            return WhisperModel(
                model_path_str,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.num_workers,
                num_workers=self.num_workers,
                download_root=str(self.model_path.parent) if self.model_path.exists() else None
            )
        except Exception as e:
            logger.error(f"Failed to load Whisper model: {e}")
            # Try downloading without custom path
            logger.info(f"Attempting to download model {self.model_size} to default cache")
            return WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
                cpu_threads=self.num_workers,
                num_workers=self.num_workers
            )
    
    async def transcribe(self, 
                        audio: np.ndarray,
                        language: Optional[str] = None) -> Dict[str, any]:
        """
        Transcribe audio to text
        
        Args:
            audio: Audio data (numpy array, float32, mono, 16kHz)
            language: Override source language
        
        Returns:
            Dictionary with transcription results:
            {
                'text': str,
                'language': str,
                'segments': list,
                'confidence': float
            }
        """
        if self.model is None:
            raise RuntimeError("Model not initialized")
        
        # Use specified language or default
        lang = language or self.language
        
        try:
            # Run transcription in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._transcribe_sync,
                audio,
                lang
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Transcription error: {e}", exc_info=True)
            return {
                'text': '',
                'language': lang,
                'segments': [],
                'confidence': 0.0,
                'error': str(e)
            }
    
    def _transcribe_sync(self, audio: np.ndarray, language: str) -> Dict[str, any]:
        """
        Synchronous transcription (runs in thread pool)
        
        Args:
            audio: Audio data
            language: Language code
        
        Returns:
            Transcription result
        """
        # Ensure audio is float32
        if audio.dtype != np.float32:
            audio = audio.astype(np.float32)
        
        # Normalize audio to [-1, 1] if needed
        max_val = np.abs(audio).max()
        if max_val > 1.0:
            audio = audio / max_val
        
        # Transcribe
        segments, info = self.model.transcribe(
            audio,
            language=language,
            beam_size=self.beam_size,
            vad_filter=False,  # We handle VAD separately
            word_timestamps=False  # Disable for speed
        )
        
        # Collect segments
        segment_list = []
        full_text = []
        total_confidence = 0.0
        segment_count = 0
        
        for segment in segments:
            segment_dict = {
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'confidence': segment.avg_logprob
            }
            segment_list.append(segment_dict)
            full_text.append(segment.text.strip())
            total_confidence += segment.avg_logprob
            segment_count += 1
        
        # Calculate average confidence
        avg_confidence = total_confidence / segment_count if segment_count > 0 else 0.0
        
        # Combine text
        text = ' '.join(full_text).strip()
        
        return {
            'text': text,
            'language': info.language,
            'segments': segment_list,
            'confidence': avg_confidence,
            'duration': info.duration
        }
    
    async def transcribe_streaming(self,
                                   audio_iterator,
                                   language: Optional[str] = None):
        """
        Transcribe audio stream (generator)
        
        Args:
            audio_iterator: Async iterator yielding audio chunks
            language: Override source language
        
        Yields:
            Transcription results as they become available
        """
        async for audio_chunk in audio_iterator:
            result = await self.transcribe(audio_chunk, language)
            if result.get('text'):
                yield result
    
    def set_language(self, language: str):
        """Update source language"""
        self.language = language
        logger.info(f"ASR language set to: {language}")
    
    def get_supported_languages(self) -> List[str]:
        """Get list of supported languages"""
        # Whisper supports 99 languages
        return [
            'en', 'zh', 'de', 'es', 'ru', 'ko', 'fr', 'ja', 'pt', 'tr',
            'pl', 'ca', 'nl', 'ar', 'sv', 'it', 'id', 'hi', 'fi', 'vi',
            'he', 'uk', 'el', 'ms', 'cs', 'ro', 'da', 'hu', 'ta', 'no',
            'th', 'ur', 'hr', 'bg', 'lt', 'la', 'mi', 'ml', 'cy', 'sk',
            'te', 'fa', 'lv', 'bn', 'sr', 'az', 'sl', 'kn', 'et', 'mk',
            'br', 'eu', 'is', 'hy', 'ne', 'mn', 'bs', 'kk', 'sq', 'sw',
            'gl', 'mr', 'pa', 'si', 'km', 'sn', 'yo', 'so', 'af', 'oc',
            'ka', 'be', 'tg', 'sd', 'gu', 'am', 'yi', 'lo', 'uz', 'fo',
            'ht', 'ps', 'tk', 'nn', 'mt', 'sa', 'lb', 'my', 'bo', 'tl',
            'mg', 'as', 'tt', 'haw', 'ln', 'ha', 'ba', 'jw', 'su'
        ]
    
    async def cleanup(self):
        """Cleanup resources"""
        self.model = None
        logger.info("ASR engine cleaned up")


class MockASR:
    """Mock ASR for testing without model"""
    
    async def initialize(self):
        logger.warning("Using Mock ASR - for testing only")
    
    async def transcribe(self, audio: np.ndarray, language: Optional[str] = None) -> Dict:
        await asyncio.sleep(0.1)  # Simulate processing
        return {
            'text': '[Mock transcription]',
            'language': language or 'en',
            'segments': [],
            'confidence': 1.0
        }
    
    def set_language(self, language: str):
        pass
    
    async def cleanup(self):
        pass
