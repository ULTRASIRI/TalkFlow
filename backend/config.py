"""
TalkFlow Configuration
Centralized configuration for all pipeline components
"""
import os
from pathlib import Path
from typing import Optional


class Config:
    """Application configuration"""
    
    def __init__(self):
        # Base paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.MODELS_DIR = self.BASE_DIR / "models"
        
        # Model paths
        self.WHISPER_MODEL_PATH = self._get_model_path("whisper", "WHISPER_MODEL_PATH")
        self.ARGOS_MODEL_PATH = self._get_model_path("argos", "ARGOS_MODEL_PATH")
        self.PIPER_MODEL_PATH = self._get_model_path("piper", "PIPER_MODEL_PATH")
        
        # Audio settings
        self.SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
        self.CHANNELS = int(os.getenv("CHANNELS", "1"))
        # Reduced chunk duration for better VAD alignment (2048 samples = 128ms at 16kHz)
        self.CHUNK_DURATION_MS = int(os.getenv("CHUNK_DURATION_MS", "128"))
        self.CHUNK_SIZE = int(self.SAMPLE_RATE * self.CHUNK_DURATION_MS / 1000)
        
        # VAD settings
        self.VAD_ENABLED = os.getenv("VAD_ENABLED", "true").lower() == "true"
        self.VAD_THRESHOLD = float(os.getenv("VAD_THRESHOLD", "0.5"))
        self.VAD_MIN_SPEECH_DURATION_MS = int(os.getenv("VAD_MIN_SPEECH_DURATION_MS", "250"))
        self.VAD_MIN_SILENCE_DURATION_MS = int(os.getenv("VAD_MIN_SILENCE_DURATION_MS", "300"))
        self.VAD_SPEECH_PAD_MS = int(os.getenv("VAD_SPEECH_PAD_MS", "100"))
        
        # ASR settings (faster-whisper)
        self.WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
        self.WHISPER_COMPUTE_TYPE = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self.WHISPER_DEVICE = os.getenv("WHISPER_DEVICE", "cpu")
        self.WHISPER_NUM_WORKERS = int(os.getenv("WHISPER_NUM_WORKERS", "1"))
        self.WHISPER_BEAM_SIZE = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
        
        # Language settings
        self.SOURCE_LANGUAGE = os.getenv("SOURCE_LANGUAGE", "en")
        self.TARGET_LANGUAGE = os.getenv("TARGET_LANGUAGE", "es")
        
        # Translation settings (Argos)
        self.ARGOS_DEVICE = os.getenv("ARGOS_DEVICE", "cpu")
        
        # TTS settings (Piper)
        self.PIPER_VOICE = os.getenv("PIPER_VOICE", "en_US-lessac-medium")
        self.PIPER_SPEAKER = int(os.getenv("PIPER_SPEAKER", "0"))
        self.PIPER_LENGTH_SCALE = float(os.getenv("PIPER_LENGTH_SCALE", "1.0"))
        self.PIPER_NOISE_SCALE = float(os.getenv("PIPER_NOISE_SCALE", "0.667"))
        self.PIPER_NOISE_W = float(os.getenv("PIPER_NOISE_W", "0.8"))
        
        # Buffer settings
        self.MIN_BUFFER_DURATION_MS = int(os.getenv("MIN_BUFFER_DURATION_MS", "800"))
        self.MAX_BUFFER_DURATION_MS = int(os.getenv("MAX_BUFFER_DURATION_MS", "1200"))
        self.BUFFER_OVERLAP_MS = int(os.getenv("BUFFER_OVERLAP_MS", "100"))
        
        # Performance settings
        self.MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "3"))
        self.PROCESSING_TIMEOUT_SECONDS = int(os.getenv("PROCESSING_TIMEOUT_SECONDS", "10"))
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_DIR = self.BASE_DIR / "logs"
        self.LOG_DIR.mkdir(exist_ok=True)
        
        # Metrics
        self.ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.METRICS_WINDOW_SIZE = int(os.getenv("METRICS_WINDOW_SIZE", "100"))
    
    def _get_model_path(self, model_type: str, env_var: str) -> Path:
        """Get model path from environment or use default"""
        env_path = os.getenv(env_var)
        if env_path:
            return Path(env_path)
        return self.MODELS_DIR / model_type
    
    def get_language_pair(self) -> tuple[str, str]:
        """Get current language pair"""
        return self.SOURCE_LANGUAGE, self.TARGET_LANGUAGE
    
    def validate(self) -> bool:
        """Validate configuration"""
        errors = []
        
        # Check model directories exist
        if not self.MODELS_DIR.exists():
            errors.append(f"Models directory not found: {self.MODELS_DIR}")
        
        # Validate audio settings
        if self.SAMPLE_RATE not in [8000, 16000, 22050, 44100, 48000]:
            errors.append(f"Invalid sample rate: {self.SAMPLE_RATE}")
        
        if self.CHANNELS not in [1, 2]:
            errors.append(f"Invalid channel count: {self.CHANNELS}")
        
        # Validate VAD settings
        if not 0 <= self.VAD_THRESHOLD <= 1:
            errors.append(f"Invalid VAD threshold: {self.VAD_THRESHOLD}")
        
        # Validate buffer settings
        if self.MIN_BUFFER_DURATION_MS > self.MAX_BUFFER_DURATION_MS:
            errors.append("MIN_BUFFER_DURATION_MS cannot exceed MAX_BUFFER_DURATION_MS")
        
        if errors:
            for error in errors:
                print(f"Configuration error: {error}")
            return False
        
        return True
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"TalkFlowConfig(\n"
            f"  Sample Rate: {self.SAMPLE_RATE}Hz\n"
            f"  Languages: {self.SOURCE_LANGUAGE} → {self.TARGET_LANGUAGE}\n"
            f"  VAD: {'Enabled' if self.VAD_ENABLED else 'Disabled'}\n"
            f"  Whisper: {self.WHISPER_MODEL_SIZE}/{self.WHISPER_COMPUTE_TYPE}\n"
            f")"
        )


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """Get singleton config instance"""
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
