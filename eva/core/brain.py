"""
Eva's Brain — Core AI Module

This module connects to Opus 4.6 and handles all AI interactions.
Think of it as Eva's "thinking" center.
"""

import os
import json
from typing import Optional, List, Dict, Any, Union
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam
from dotenv import load_dotenv

from eva.core.personality import EVA_SYSTEM_PROMPT, EVA_GREETING

load_dotenv()


class EvaBrain:
    """
    Eva's brain — handles all AI interactions.
    
    Connects to Grisha's Opus 4.6 proxy and manages conversations.
    """
    
    def __init__(self, base_url: str, api_key: str, model: str = "claude-opus-4.6"):
        """
        Initialize Eva's brain.
        
        Args:
            base_url: URL of the API proxy (e.g., http://89.167.8.202:8000/v1)
            api_key: API key for authentication
            model: Model name to use
        """
        self.base_url = base_url
        self.model = model
        
        # Create OpenAI-compatible client
        self.client = OpenAI(
            base_url=base_url,
            api_key=api_key,
        )
        
        # Conversation history
        self.messages: List[ChatCompletionMessageParam] = []
        
        # Initialize with system prompt
        self._init_system()
    
    def _init_system(self):
        """Set up the system prompt with Eva's personality."""
        self.messages = [
            {"role": "system", "content": EVA_SYSTEM_PROMPT}
        ]
    
    def think(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Make Eva think and respond.
        
        Args:
            user_input: What Grisha said
            context: Optional context (screen state, memory, etc.)
        
        Returns:
            Eva's response
        """
        # Add user message
        self.messages.append({"role": "user", "content": user_input})
        
        # Add context if provided
        if context:
            context_str = self._format_context(context)
            if context_str:
                self.messages.append({
                    "role": "system", 
                    "content": context_str
                })
        
        # Get response from AI
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.messages,
            temperature=0.7,
            max_tokens=2048,
        )
        
        # Extract response text
        response_text = response.choices[0].message.content or ""
        
        # Add to history
        self.messages.append({"role": "assistant", "content": response_text})
        
        return response_text
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context into a readable string."""
        parts = []
        
        if "screen" in context:
            parts.append(f"[Screen capture]\n{context['screen']}")
        
        if "memory" in context:
            parts.append(f"[Recent memories]\n{context['memory']}")
        
        if "time" in context:
            parts.append(f"[Time]\n{context['time']}")
        
        return "\n\n".join(parts)
    
    def greet(self) -> str:
        """Get Eva's greeting."""
        return self.think(EVA_GREETING)
    
    def reset(self):
        """Reset conversation (keep system prompt)."""
        self._init_system()
    
    def get_history(self) -> List[ChatCompletionMessageParam]:
        """Get conversation history."""
        return self.messages[1:]  # Exclude system prompt
    
    def add_memory_context(self, memory_summary: str):
        """Add memory context to the conversation."""
        self.messages.append({
            "role": "system",
            "content": f"[Long-term memory]\n{memory_summary}"
        })
