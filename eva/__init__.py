"""
Eva — AI Companion for Grisha

A fully autonomous AI companion with:
- Brain: Claude Opus 4 thinking
- Memory: ChromaDB vector storage + Deep Memory
- Voice: TTS (Edge) + STT (Whisper)
- Vision: Screen capture + Game detection
- Skills: Proactive AI + System monitoring
- Gaming: Real-time gaming advice mode

Usage:
    python -m eva start              # Start conversation
    python -m eva voice "text"       # Make Eva speak
    python -m eva screenshot         # Capture screen
    python -m eva status             # Check Eva's status
    python -m eva recall "query"     # Search memory
    python -m eva stt                # Voice input test
"""

from eva.companion import Eva
from eva.memory.vector_store import get_memory
from eva.memory.deep_memory import DeepMemory, get_deep_memory
from eva.voice.stt import EvaSTT
from eva.voice.tts import get_voice

__version__ = "1.0.0"
__all__ = [
    "Eva",
    "get_memory",
    "get_deep_memory",
    "DeepMemory",
    "EvaSTT",
    "get_voice",
]
