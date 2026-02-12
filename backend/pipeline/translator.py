"""
Translation Module
Uses Argos Translate for offline neural translation
"""
import asyncio
from typing import Optional, List, Tuple
from pathlib import Path

try:
    import argostranslate.package
    import argostranslate.translate
    ARGOS_AVAILABLE = True
except ImportError:
    ARGOS_AVAILABLE = False

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class Translator:
    """
    Neural translation using Argos Translate
    Offline, privacy-focused translation
    """
    
    def __init__(self,
                 model_path: Path,
                 source_lang: str = "en",
                 target_lang: str = "es"):
        """
        Initialize translator
        
        Args:
            model_path: Path to Argos models
            source_lang: Source language code
            target_lang: Target language code
        """
        self.model_path = model_path
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.translator = None
        
        if not ARGOS_AVAILABLE:
            logger.warning("Argos Translate not available, translation will be disabled")
        
        logger.info(f"Translator initialized: {source_lang} → {target_lang}")
    
    async def initialize(self):
        """Load translation model"""
        if not ARGOS_AVAILABLE:
            logger.warning("Skipping translation initialization - Argos not available")
            return
        
        try:
            # Set package directory
            if self.model_path.exists():
                argostranslate.package.package_dir = str(self.model_path)
            
            # Update package index
            logger.info("Updating Argos package index...")
            await asyncio.get_event_loop().run_in_executor(
                None,
                argostranslate.package.update_package_index
            )
            
            # Get available packages
            available_packages = argostranslate.package.get_available_packages()
            
            # Find required package
            required_package = None
            for package in available_packages:
                if (package.from_code == self.source_lang and 
                    package.to_code == self.target_lang):
                    required_package = package
                    break
            
            if required_package:
                # Check if already installed
                installed_packages = argostranslate.package.get_installed_packages()
                is_installed = any(
                    p.from_code == self.source_lang and p.to_code == self.target_lang
                    for p in installed_packages
                )
                
                if not is_installed:
                    logger.info(f"Installing translation package: {self.source_lang} → {self.target_lang}")
                    await asyncio.get_event_loop().run_in_executor(
                        None,
                        argostranslate.package.install_from_path,
                        required_package.download()
                    )
                
                logger.info("Translation model loaded successfully")
            else:
                logger.warning(
                    f"Translation package not found: {self.source_lang} → {self.target_lang}"
                )
        
        except Exception as e:
            logger.error(f"Failed to initialize translation: {e}", exc_info=True)
    
    async def translate(self, text: str) -> str:
        """
        Translate text
        
        Args:
            text: Source text
        
        Returns:
            Translated text
        """
        if not ARGOS_AVAILABLE:
            logger.debug("Translation skipped - Argos not available")
            return text
        
        if not text or not text.strip():
            return text
        
        try:
            # Get translation
            loop = asyncio.get_event_loop()
            translated = await loop.run_in_executor(
                None,
                self._translate_sync,
                text
            )
            
            return translated
        
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return text  # Return original on error
    
    def _translate_sync(self, text: str) -> str:
        """
        Synchronous translation (runs in thread pool)
        
        Args:
            text: Source text
        
        Returns:
            Translated text
        """
        try:
            translated = argostranslate.translate.translate(
                text,
                self.source_lang,
                self.target_lang
            )
            return translated
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return text
    
    async def translate_batch(self, texts: List[str]) -> List[str]:
        """
        Translate multiple texts
        
        Args:
            texts: List of source texts
        
        Returns:
            List of translated texts
        """
        if not ARGOS_AVAILABLE:
            return texts
        
        results = []
        for text in texts:
            translated = await self.translate(text)
            results.append(translated)
        
        return results
    
    def set_language_pair(self, source_lang: str, target_lang: str):
        """
        Update language pair
        
        Args:
            source_lang: New source language
            target_lang: New target language
        """
        self.source_lang = source_lang
        self.target_lang = target_lang
        logger.info(f"Language pair updated: {source_lang} → {target_lang}")
        
        # Will need to reload model on next translate
        self.translator = None
    
    def get_supported_languages(self) -> List[Tuple[str, str]]:
        """
        Get list of supported language pairs
        
        Returns:
            List of (source_code, target_code) tuples
        """
        if not ARGOS_AVAILABLE:
            return []
        
        try:
            installed = argostranslate.package.get_installed_packages()
            return [(p.from_code, p.to_code) for p in installed]
        except:
            return []
    
    def get_available_languages(self) -> List[str]:
        """
        Get list of available language codes
        
        Returns:
            List of language codes
        """
        if not ARGOS_AVAILABLE:
            return ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh', 'ar']
        
        try:
            available = argostranslate.package.get_available_packages()
            languages = set()
            for package in available:
                languages.add(package.from_code)
                languages.add(package.to_code)
            return sorted(list(languages))
        except:
            return ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh', 'ar']
    
    async def cleanup(self):
        """Cleanup resources"""
        self.translator = None
        logger.info("Translator cleaned up")


class MockTranslator:
    """Mock translator for testing"""
    
    def __init__(self, source_lang: str = "en", target_lang: str = "es"):
        self.source_lang = source_lang
        self.target_lang = target_lang
        logger.warning("Using Mock Translator - for testing only")
    
    async def initialize(self):
        pass
    
    async def translate(self, text: str) -> str:
        await asyncio.sleep(0.05)  # Simulate processing
        return f"[{self.target_lang.upper()}] {text}"
    
    def set_language_pair(self, source_lang: str, target_lang: str):
        self.source_lang = source_lang
        self.target_lang = target_lang
    
    def get_available_languages(self) -> List[str]:
        return ['en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'zh', 'ar']
    
    async def cleanup(self):
        pass
