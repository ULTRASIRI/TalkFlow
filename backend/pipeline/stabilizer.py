"""
Text Stabilizer
Prevents flickering and ensures smooth progressive output
"""
import asyncio
from typing import Optional
from difflib import SequenceMatcher

from backend.utils.logger import setup_logger

logger = setup_logger(__name__)


class TextStabilizer:
    """
    Stabilizes transcription output to prevent flickering
    Uses longest common subsequence to determine stable prefix
    """
    
    def __init__(self,
                 similarity_threshold: float = 0.85,
                 min_stable_length: int = 10):
        """
        Initialize text stabilizer
        
        Args:
            similarity_threshold: Minimum similarity ratio for stability
            min_stable_length: Minimum characters to consider stable
        """
        self.similarity_threshold = similarity_threshold
        self.min_stable_length = min_stable_length
        
        self.previous_text = ""
        self.stable_text = ""
        self.consecutive_stable_count = 0
        
        logger.info(
            f"Text stabilizer initialized: threshold={similarity_threshold}, "
            f"min_length={min_stable_length}"
        )
    
    def process(self, new_text: str, is_final: bool = False) -> dict:
        """
        Process new transcription text
        
        Args:
            new_text: New transcription text
            is_final: Whether this is a final transcription
        
        Returns:
            Dictionary with:
            - stable_text: Text confirmed as stable
            - incremental_text: New text to display
            - confidence: Confidence in stability
        """
        if not new_text:
            return {
                'stable_text': self.stable_text,
                'incremental_text': '',
                'confidence': 1.0,
                'is_stable': True
            }
        
        # If final, return as-is
        if is_final:
            self.stable_text = new_text
            self.previous_text = new_text
            self.consecutive_stable_count = 0
            
            return {
                'stable_text': new_text,
                'incremental_text': new_text[len(self.stable_text):] if len(new_text) > len(self.stable_text) else '',
                'confidence': 1.0,
                'is_stable': True
            }
        
        # Calculate similarity with previous text
        similarity = self._calculate_similarity(self.previous_text, new_text)
        
        # Find stable prefix
        stable_prefix = self._find_stable_prefix(self.previous_text, new_text)
        
        # Determine if text is stable
        is_stable = (
            similarity >= self.similarity_threshold and
            len(stable_prefix) >= self.min_stable_length
        )
        
        if is_stable:
            self.consecutive_stable_count += 1
        else:
            self.consecutive_stable_count = 0
        
        # Update stable text if confidence is high
        if self.consecutive_stable_count >= 2 or len(stable_prefix) > len(self.stable_text):
            new_stable = stable_prefix
            incremental = new_stable[len(self.stable_text):]
            self.stable_text = new_stable
        else:
            incremental = ''
        
        # Update previous text
        self.previous_text = new_text
        
        return {
            'stable_text': self.stable_text,
            'incremental_text': incremental,
            'confidence': similarity,
            'is_stable': is_stable,
            'full_text': new_text
        }
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two texts
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Similarity ratio (0-1)
        """
        if not text1 and not text2:
            return 1.0
        if not text1 or not text2:
            return 0.0
        
        matcher = SequenceMatcher(None, text1, text2)
        return matcher.ratio()
    
    def _find_stable_prefix(self, text1: str, text2: str) -> str:
        """
        Find longest common prefix between two texts
        
        Args:
            text1: First text
            text2: Second text
        
        Returns:
            Stable prefix
        """
        if not text1 or not text2:
            return ""
        
        # Use sequence matcher to find matching blocks
        matcher = SequenceMatcher(None, text1, text2)
        matching_blocks = matcher.get_matching_blocks()
        
        # Find longest matching prefix
        if matching_blocks:
            first_block = matching_blocks[0]
            if first_block.a == 0 and first_block.b == 0:
                return text2[:first_block.size]
        
        return ""
    
    def reset(self):
        """Reset stabilizer state"""
        self.previous_text = ""
        self.stable_text = ""
        self.consecutive_stable_count = 0
        logger.debug("Text stabilizer reset")
    
    def get_state(self) -> dict:
        """Get current stabilizer state"""
        return {
            'stable_text_length': len(self.stable_text),
            'previous_text_length': len(self.previous_text),
            'consecutive_stable': self.consecutive_stable_count
        }


class PhraseBuffer:
    """
    Buffers text until complete phrases are detected
    Prevents cutting mid-sentence
    """
    
    def __init__(self,
                 min_phrase_length: int = 20,
                 phrase_delimiters: str = ".!?,;:\n"):
        """
        Initialize phrase buffer
        
        Args:
            min_phrase_length: Minimum characters for a phrase
            phrase_delimiters: Characters that end a phrase
        """
        self.min_phrase_length = min_phrase_length
        self.phrase_delimiters = phrase_delimiters
        
        self.buffer = ""
        
        logger.info(f"Phrase buffer initialized: min_length={min_phrase_length}")
    
    def add(self, text: str) -> Optional[str]:
        """
        Add text to buffer
        
        Args:
            text: New text to add
        
        Returns:
            Complete phrase if available, None otherwise
        """
        self.buffer += text
        
        # Check if we have a complete phrase
        if len(self.buffer) >= self.min_phrase_length:
            # Find last phrase delimiter
            last_delimiter_pos = -1
            for delimiter in self.phrase_delimiters:
                pos = self.buffer.rfind(delimiter)
                if pos > last_delimiter_pos:
                    last_delimiter_pos = pos
            
            if last_delimiter_pos >= self.min_phrase_length:
                # Extract complete phrase
                phrase = self.buffer[:last_delimiter_pos + 1].strip()
                self.buffer = self.buffer[last_delimiter_pos + 1:].strip()
                return phrase
        
        return None
    
    def flush(self) -> str:
        """
        Flush remaining buffer
        
        Returns:
            Buffered text
        """
        text = self.buffer
        self.buffer = ""
        return text
    
    def reset(self):
        """Reset buffer"""
        self.buffer = ""
    
    def get_buffered(self) -> str:
        """Get current buffer content"""
        return self.buffer
