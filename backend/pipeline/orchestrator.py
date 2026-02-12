"""
Pipeline Orchestrator
Coordinates all pipeline components for end-to-end processing
"""
import asyncio
import time
from typing import Optional, Dict
import numpy as np

from backend.config import Config
from backend.pipeline.vad import VoiceActivityDetector, PassthroughVAD
from backend.pipeline.asr import ASREngine, MockASR
from backend.pipeline.translator import Translator, MockTranslator
from backend.pipeline.tts import TTSEngine, MockTTS
from backend.pipeline.stabilizer import TextStabilizer, PhraseBuffer
from backend.utils.audio_utils import AudioProcessor
from backend.utils.metrics import MetricsCollector
from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class PipelineOrchestrator:
    """
    Orchestrates the complete audio processing pipeline:
    Audio → VAD → ASR → Translation → TTS
    """
    
    def __init__(self, config: Config):
        """
        Initialize pipeline orchestrator
        
        Args:
            config: Application configuration
        """
        self.config = config
        
        # Pipeline components
        self.vad: Optional[VoiceActivityDetector] = None
        self.asr: Optional[ASREngine] = None
        self.translator: Optional[Translator] = None
        self.tts: Optional[TTSEngine] = None
        
        # Utilities
        self.audio_processor = AudioProcessor(config.SAMPLE_RATE)
        self.stabilizer = TextStabilizer()
        self.phrase_buffer = PhraseBuffer()
        self.metrics = MetricsCollector()
        
        # State
        self.is_ready = False
        self.processing_lock = asyncio.Lock()
        self.audio_buffer = []
        
        logger.info("Pipeline orchestrator created")
    
    async def initialize(self):
        """Initialize all pipeline components"""
        logger.info("Initializing pipeline components...")
        
        try:
            # Initialize VAD
            if self.config.VAD_ENABLED:
                self.vad = VoiceActivityDetector(
                    sample_rate=self.config.SAMPLE_RATE,
                    threshold=self.config.VAD_THRESHOLD,
                    min_speech_duration_ms=self.config.VAD_MIN_SPEECH_DURATION_MS,
                    min_silence_duration_ms=self.config.VAD_MIN_SILENCE_DURATION_MS,
                    speech_pad_ms=self.config.VAD_SPEECH_PAD_MS
                )
            else:
                self.vad = PassthroughVAD(
                    sample_rate=self.config.SAMPLE_RATE,
                    target_duration_ms=self.config.CHUNK_DURATION_MS
                )
            
            await self.vad.initialize()
            logger.info("✓ VAD initialized")
            
            # Initialize ASR
            logger.info("Loading Whisper ASR model...")
            self.asr = ASREngine(
                model_path=self.config.WHISPER_MODEL_PATH,
                model_size=self.config.WHISPER_MODEL_SIZE,
                compute_type=self.config.WHISPER_COMPUTE_TYPE,
                device=self.config.WHISPER_DEVICE,
                language=self.config.SOURCE_LANGUAGE,
                beam_size=self.config.WHISPER_BEAM_SIZE,
                num_workers=self.config.WHISPER_NUM_WORKERS
            )
            
            try:
                await self.asr.initialize()
                logger.info("✓ ASR (Whisper) initialized successfully")
            except Exception as e:
                logger.error(f"ASR initialization failed: {e}", exc_info=True)
                logger.error("=" * 60)
                logger.error("CRITICAL: Whisper model failed to load!")
                logger.error("The application will use mock transcription (placeholder text)")
                logger.error("")
                logger.error("To fix this:")
                logger.error("1. Whisper models download automatically on first use")
                logger.error("2. Ensure internet connection is available")
                logger.error("3. Check disk space (~500MB needed for 'small' model)")
                logger.error("4. Wait for model download to complete")
                logger.error("")
                logger.error("Using Mock ASR for testing only...")
                logger.error("=" * 60)
                
                self.asr = MockASR()
                await self.asr.initialize()
                logger.warning("⚠ Mock ASR initialized (NOT PRODUCTION READY)")
            
            # Initialize Translator
            logger.info("Loading Argos Translate model...")
            self.translator = Translator(
                model_path=self.config.ARGOS_MODEL_PATH,
                source_lang=self.config.SOURCE_LANGUAGE,
                target_lang=self.config.TARGET_LANGUAGE
            )
            
            try:
                await self.translator.initialize()
                logger.info("✓ Translator (Argos) initialized successfully")
            except Exception as e:
                logger.error(f"Translation initialization failed: {e}", exc_info=True)
                logger.warning("⚠ Using Mock Translator (will return placeholder translations)")
                logger.warning("Translation packages download automatically when languages selected")
                
                self.translator = MockTranslator(
                    source_lang=self.config.SOURCE_LANGUAGE,
                    target_lang=self.config.TARGET_LANGUAGE
                )
                await self.translator.initialize()
            
            # Initialize TTS
            logger.info("Loading Piper TTS model...")
            self.tts = TTSEngine(
                model_path=self.config.PIPER_MODEL_PATH,
                voice=self.config.PIPER_VOICE,
                speaker=self.config.PIPER_SPEAKER,
                length_scale=self.config.PIPER_LENGTH_SCALE,
                noise_scale=self.config.PIPER_NOISE_SCALE,
                noise_w=self.config.PIPER_NOISE_W
            )
            
            try:
                await self.tts.initialize()
                logger.info("✓ TTS (Piper) initialized successfully")
            except Exception as e:
                logger.error(f"TTS initialization failed: {e}", exc_info=True)
                logger.error("=" * 60)
                logger.error("CRITICAL: Piper TTS voice not found!")
                logger.error("")
                logger.error("To fix this:")
                logger.error("1. Run: python download_models.py")
                logger.error("2. Or manually download voice files from:")
                logger.error("   https://huggingface.co/rhasspy/piper-voices")
                logger.error("3. Place .onnx and .onnx.json files in models/piper/")
                logger.error("")
                logger.error("Using Mock TTS (will generate placeholder audio)...")
                logger.error("=" * 60)
                
                self.tts = MockTTS()
                await self.tts.initialize()
                logger.warning("⚠ Mock TTS initialized (NOT PRODUCTION READY)")
            
            self.is_ready = True
            logger.info("✅ Pipeline initialization complete")
        
        except Exception as e:
            logger.error(f"Pipeline initialization failed: {e}", exc_info=True)
            raise
    
    async def process_audio(self, audio_bytes: bytes) -> Optional[Dict]:
        """
        Process audio through the complete pipeline
        
        Args:
            audio_bytes: Raw audio bytes from WebSocket
        
        Returns:
            Dictionary with processing results or None
        """
        if not self.is_ready:
            logger.warning("Pipeline not ready")
            return None
        
        start_time = time.time()
        
        try:
            # Convert bytes to numpy array
            audio_array = self.audio_processor.bytes_to_array(audio_bytes)
            
            if audio_array is None or len(audio_array) == 0:
                return None
            
            # Stage 1: VAD
            vad_start = time.time()
            is_speech, speech_segment = await self.vad.process(audio_array)
            vad_latency = (time.time() - vad_start) * 1000
            
            # No complete speech segment yet
            if speech_segment is None:
                return {
                    'type': 'vad_status',
                    'is_speech': is_speech,
                    'metrics': {'vad_latency_ms': vad_latency}
                }
            
            logger.debug(f"Speech segment detected: {len(speech_segment)} samples")
            
            # Stage 2: ASR
            asr_start = time.time()
            transcription_result = await self.asr.transcribe(
                speech_segment,
                language=self.config.SOURCE_LANGUAGE
            )
            asr_latency = (time.time() - asr_start) * 1000
            
            transcription_text = transcription_result.get('text', '')
            
            if not transcription_text:
                logger.debug("No transcription produced")
                return None
            
            logger.info(f"Transcription: {transcription_text}")
            
            # Stage 3: Text Stabilization
            stabilizer_result = self.stabilizer.process(
                transcription_text,
                is_final=True
            )
            
            stable_text = stabilizer_result['stable_text']
            
            # Stage 4: Translation
            translation_start = time.time()
            translated_text = await self.translator.translate(stable_text)
            translation_latency = (time.time() - translation_start) * 1000
            
            logger.info(f"Translation: {translated_text}")
            
            # Stage 5: TTS
            tts_start = time.time()
            audio_bytes = await self.tts.synthesize(translated_text)
            tts_latency = (time.time() - tts_start) * 1000
            
            # Calculate total latency
            total_latency = (time.time() - start_time) * 1000
            
            # Collect metrics
            metrics = {
                'vad_latency_ms': vad_latency,
                'asr_latency_ms': asr_latency,
                'translation_latency_ms': translation_latency,
                'tts_latency_ms': tts_latency,
                'total_latency_ms': total_latency,
                'audio_duration_ms': len(speech_segment) / self.config.SAMPLE_RATE * 1000,
                'transcription_confidence': transcription_result.get('confidence', 0.0)
            }
            
            self.metrics.record('pipeline_latency', total_latency)
            self.metrics.record('asr_latency', asr_latency)
            self.metrics.record('translation_latency', translation_latency)
            self.metrics.record('tts_latency', tts_latency)
            
            logger.info(f"Pipeline latency: {total_latency:.1f}ms")
            
            # Return results
            return {
                'transcription': stable_text,
                'translation': translated_text,
                'audio_bytes': audio_bytes,
                'source_language': self.config.SOURCE_LANGUAGE,
                'target_language': self.config.TARGET_LANGUAGE,
                'metrics': metrics,
                'is_final': True
            }
        
        except Exception as e:
            logger.error(f"Pipeline processing error: {e}", exc_info=True)
            return {
                'error': str(e),
                'type': 'processing_error'
            }
    
    async def reset(self):
        """Reset pipeline state"""
        logger.info("Resetting pipeline state...")
        
        if self.vad:
            self.vad.reset()
        
        self.stabilizer.reset()
        self.phrase_buffer.reset()
        self.audio_buffer = []
        
        logger.info("Pipeline state reset")
    
    async def cleanup(self):
        """Cleanup pipeline resources"""
        logger.info("Cleaning up pipeline...")
        
        if self.asr:
            await self.asr.cleanup()
        
        if self.translator:
            await self.translator.cleanup()
        
        if self.tts:
            await self.tts.cleanup()
        
        self.is_ready = False
        logger.info("Pipeline cleanup complete")
    
    def get_status(self) -> dict:
        """Get pipeline status"""
        return {
            'ready': self.is_ready,
            'vad_state': self.vad.get_state() if self.vad else {},
            'stabilizer_state': self.stabilizer.get_state(),
            'metrics': self.metrics.get_summary()
        }
    
    async def update_languages(self, source_lang: str, target_lang: str):
        """
        Update language settings
        
        Args:
            source_lang: New source language
            target_lang: New target language
        """
        logger.info(f"Updating languages: {source_lang} → {target_lang}")
        
        self.config.SOURCE_LANGUAGE = source_lang
        self.config.TARGET_LANGUAGE = target_lang
        
        if self.asr:
            self.asr.set_language(source_lang)
        
        if self.translator:
            self.translator.set_language_pair(source_lang, target_lang)
        
        # Reset state for new language pair
        await self.reset()
