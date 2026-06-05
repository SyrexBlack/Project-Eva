"""
Eva — AI Companion for Grisha

Usage:
    python -m eva start          # Start conversation
    python -m eva voice "text"   # Make Eva speak
    python -m eva screenshot     # Capture screen
    python -m eva status         # Check Eva's status
    python -m eva recall "query" # Search memory
"""

from eva.companion import Eva
from eva.memory.vector_store import get_memory

__version__ = "0.2.0"
__all__ = ["Eva", "get_memory"]
