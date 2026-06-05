"""
Eva Memory Module

Exports:
- get_memory: Get ChromaDB memory instance
- get_deep_memory: Get deep memory (multi-level)
- ShortTermMemory: Session buffer
- LongTermMemory: ChromaDB with summarization
- KnowledgeGraph: Entity relationships
- DeepMemory: Unified memory interface
"""

from eva.memory.vector_store import get_memory
from eva.memory.deep_memory import (
    get_deep_memory,
    DeepMemory,
    ShortTermMemory,
    LongTermMemory,
    KnowledgeGraph,
    MemoryType,
    MemoryEntry
)

__all__ = [
    # Legacy
    "get_memory",
    
    # Deep Memory
    "get_deep_memory",
    "DeepMemory",
    "ShortTermMemory",
    "LongTermMemory",
    "KnowledgeGraph",
    "MemoryType",
    "MemoryEntry",
]