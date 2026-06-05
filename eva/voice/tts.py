"""
Eva's Voice Module

Handles speech-to-text (STT) and text-to-speech (TTS).
Eva can listen and speak naturally.
"""

import os
import asyncio
from typing import Optional
import edge_tts
from dotenv import load_dotenv

load_dotenv()

# Default voice settings
DEFAULT_VOICE = "en-US-AriaNeural"
VOICE_CACHE = "./data/voice_cache"


class EvaVoice:
    """
    Eva's voice — speaks and listens.
    
    Uses Edge TTS for high-quality speech synthesis.
    Can be extended with Whisper for speech recognition.
    """
    
    def __init__(self, voice: str = DEFAULT_VOICE):
        """
        Initialize Eva's voice.
        
        Args:
            voice: Edge TTS voice name
        """
        self.voice = voice
        os.makedirs(VOICE_CACHE, exist_ok=True)
    
    async def speak_async(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Convert text to speech asynchronously.
        
        Args:
            text: Text to speak
            output_file: Optional output file path
        
        Returns:
            Path to audio file
        """
        if output_file is None:
            output_file = f"{VOICE_CACHE}/eva_response_{len(text)}.mp3"
        
        # Generate speech
        communicate = edge_tts.Communicate(text, self.voice)
        await communicate.save(output_file)
        
        return output_file
    
    def speak(self, text: str, output_file: Optional[str] = None) -> str:
        """
        Convert text to speech (synchronous version).
        
        Args:
            text: Text to speak
            output_file: Optional output file path
        
        Returns:
            Path to audio file
        """
        return asyncio.run(self.speak_async(text, output_file))
    
    async def list_voices_async(self, language: str = "en") -> list:
        """
        List available voices.
        
        Args:
            language: Language code (en, ru, etc.)
        
        Returns:
            List of available voices
        """
        voices = await edge_tts.list_voices()
        return [v for v in voices if v["Locale"].startswith(language)]
    
    def list_voices(self, language: str = "en") -> list:
        """List available voices (sync)."""
        return asyncio.run(self.list_voices_async(language))


# Global instance
_voice: Optional[EvaVoice] = None


def get_voice() -> EvaVoice:
    """Get or create global voice instance."""
    global _voice
    if _voice is None:
        _voice = EvaVoice()
    return _voice
