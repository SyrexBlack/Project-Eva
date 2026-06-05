"""
Eva Voice Module

Exports:
- get_voice: Get TTS instance
- get_stt: Get STT instance
- EvaVoice: Text-to-speech (Edge TTS)
- EvaSTT: Speech-to-text (Whisper)
"""

from eva.voice.tts import get_voice, EvaVoice
from eva.voice.stt import get_stt, EvaSTT, STTConfig, SimpleSTT

__all__ = [
    # TTS
    "get_voice",
    "EvaVoice",
    
    # STT
    "get_stt",
    "EvaSTT",
    "STTConfig",
    "SimpleSTT",
]