"""
Eva's Memory System

This module handles Eva's long-term memory using ChromaDB.
Think of it as Eva's "brain cells" — she remembers everything.
"""

import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import chromadb
from chromadb.config import Settings

# Path to memory storage
MEMORY_PATH = "./data/memory"


class EvaMemory:
    """
    Eva's memory — stores and retrieves experiences.
    
    Uses ChromaDB for vector storage. When Eva learns something,
    it gets embedded and stored here. When she needs to remember,
    she searches this memory.
    """
    
    def __init__(self, path: str = MEMORY_PATH):
        """
        Initialize Eva's memory.
        
        Args:
            path: Where to store memory files
        """
        # Ensure directory exists
        os.makedirs(path, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=path)
        
        # Create collection for memories
        self.collection = self.client.get_or_create_collection(
            name="eva_memories",
            metadata={"description": "Eva's long-term memories"}
        )
        
        # Create collection for facts about Grisha
        self.facts_collection = self.client.get_or_create_collection(
            name="grisha_facts",
            metadata={"description": "Facts about Grisha"}
        )
        
        # Counter for IDs
        self._memory_id = 0
    
    def remember(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Store a memory.
        
        Args:
            content: What to remember
            metadata: Optional metadata (time, context, importance)
        
        Returns:
            Memory ID
        """
        # Generate ID
        self._memory_id += 1
        memory_id = f"memory_{self._memory_id}"
        
        # Add timestamp if not present
        if metadata is None:
            metadata = {}
        if "timestamp" not in metadata:
            metadata["timestamp"] = datetime.now().isoformat()
        
        # Store in vector DB
        self.collection.add(
            documents=[content],
            ids=[memory_id],
            metadatas=[metadata]
        )
        
        return memory_id
    
    def recall(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Search memories by query.
        
        Args:
            query: What to search for
            limit: How many results to return
        
        Returns:
            List of memories (content + metadata)
        """
        results = self.collection.query(
            query_texts=[query],
            n_results=limit
        )
        
        # Format results
        memories = []
        if results["documents"]:
            for i, doc in enumerate(results["documents"][0]):
                memories.append({
                    "content": doc,
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i]
                })
        
        return memories
    
    def store_fact(self, fact: str, category: str = "general") -> str:
        """
        Store a fact about Grisha.
        
        Args:
            fact: The fact
            category: Category (work, personal, projects, etc.)
        
        Returns:
            Fact ID
        """
        fact_id = f"fact_{category}_{self._memory_id}"
        self._memory_id += 1
        
        self.facts_collection.add(
            documents=[fact],
            ids=[fact_id],
            metadatas=[{"category": category, "timestamp": datetime.now().isoformat()}]
        )
        
        return fact_id
    
    def get_facts(self, category: Optional[str] = None, limit: int = 50) -> List[str]:
        """
        Get facts about Grisha.
        
        Args:
            category: Filter by category (or None for all)
            limit: Max results
        
        Returns:
            List of facts
        """
        if category:
            results = self.facts_collection.query(
                query_texts=[category],
                where={"category": category},
                n_results=limit
            )
        else:
            results = self.facts_collection.query(
                query_texts=["*"],
                n_results=limit
            )
        
        if results["documents"]:
            return results["documents"][0]
        
        return []
    
    def get_context(self, query: str, limit: int = 10) -> str:
        """
        Get memory context for AI.
        
        This creates a formatted string of relevant memories
        that can be added to the conversation context.
        
        Args:
            query: What to recall
            limit: How many memories
        
        Returns:
            Formatted memory context
        """
        memories = self.recall(query, limit)
        
        if not memories:
            return ""
        
        parts = ["[Recent memories]"]
        for m in memories:
            ts = m["metadata"].get("timestamp", "unknown")
            parts.append(f"- {m['content']} (at {ts})")
        
        return "\n".join(parts)
    
    def get_memory_summary(self) -> str:
        """
        Get a summary of all memories.
        
        Returns:
            Summary string for AI context
        """
        # Get recent memories
        results = self.collection.query(
            query_texts=["life, work, projects, personal"],
            n_results=20
        )
        
        if not results["documents"]:
            return "No memories yet."
        
        # Format as summary
        docs = results["documents"][0]
        return f"Eva has {len(docs)} memories. Recent ones:\n" + "\n".join(f"- {d[:100]}..." for d in docs[:5])


# Global memory instance
_memory: Optional[EvaMemory] = None


def get_memory() -> EvaMemory:
    """Get or create the global memory instance."""
    global _memory
    if _memory is None:
        _memory = EvaMemory()
    return _memory