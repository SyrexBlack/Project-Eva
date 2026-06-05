"""
Eva's Brain — Core AI Module

This module connects to Opus 4.6 and handles all AI interactions.
Think of it as Eva's "thinking" center.
"""

import os
import json
import requests
from typing import Optional, List, Dict, Any, Union
from dotenv import load_dotenv

from eva.core.personality import EVA_SYSTEM_PROMPT, EVA_GREETING

load_dotenv()


class EvaBrain:
    """
    Eva's brain — handles all AI interactions.
    
    Connects to Grisha's Opus 4.6 proxy and manages conversations.
    """
    
    def __init__(self, base_url: str, api_key: str, model: str = "claude-opus-4.6", system_prompt: Optional[str] = None):
        """
        Initialize Eva's brain.
        
        Args:
            base_url: URL of the API proxy (e.g., http://89.167.8.202:8000)
            api_key: API key for authentication
            model: Model name to use
            system_prompt: Custom system prompt (optional)
        """
        self.base_url = base_url.rstrip('/').rstrip('/v1')
        self.model = model
        self.api_key = api_key
        self._custom_system = system_prompt or EVA_SYSTEM_PROMPT
        
        # Conversation history (Anthropic format)
        self.messages: List[Dict[str, str]] = []
        
        # Initialize with system prompt
        self._init_system()
    
    @property
    def system_prompt(self) -> str:
        return self._custom_system
    
    @system_prompt.setter
    def system_prompt(self, value: str):
        self._custom_system = value
        self._init_system()
    
    def _init_system(self):
        """Set up the system prompt with Eva's personality."""
        # For Anthropic API, system is a separate parameter
        pass  # System is stored in _custom_system
    
    def think(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Make Eva think and respond.
        
        Args:
            user_input: What Grisha said
            context: Optional context (screen state, memory, etc.)
        
        Returns:
            Eva's response
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": user_input})
        
        # Build context string if provided
        context_str = ""
        if context:
            context_str = self._format_context(context)
        
        # Prepare messages for API (exclude system, we'll use 'system' param)
        api_messages = self.messages.copy()
        if context_str:
            api_messages.append({"role": "user", "content": f"[Context]\n{context_str}"})
        
        # Use Anthropic Messages API (properly handles system prompt)
        try:
            response = requests.post(
                f"{self.base_url}/v1/messages",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "anthropic-version": "2023-06-01"
                },
                json={
                    "model": self.model,
                    "system": self._custom_system,
                    "messages": api_messages,
                    "max_tokens": 2048,
                    "temperature": 0.7,
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code} - {response.text}")
            
            result = response.json()
            
            # Extract response text
            response_text = ""
            for content in result.get('content', []):
                if content.get('type') == 'text':
                    response_text = content.get('text', '')
                    break
            
            # Add assistant response to history
            self.messages.append({"role": "assistant", "content": response_text})
            
            return response_text
            
        except Exception as e:
            # Fallback: try chat completions if messages endpoint fails
            return self._think_chat_completions(user_input, context)
    
    def _think_chat_completions(self, user_input: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Fallback using OpenAI chat completions."""
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self._custom_system},
                        {"role": "user", "content": user_input}
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.7,
                },
                timeout=120
            )
            
            if response.status_code != 200:
                raise Exception(f"API Error: {response.status_code}")
            
            result = response.json()
            response_text = result['choices'][0]['message']['content']
            
            return response_text
            
        except Exception as e:
            return f"Извини, произошла ошибка: {str(e)}"
    
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
        return self.think("Привет! Начни разговор от имени Евы.")
    
    def reset(self):
        """Reset conversation (keep system prompt)."""
        self.messages = []
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.messages
    
    def add_memory_context(self, memory_summary: str):
        """Add memory context to the conversation."""
        # For Anthropic API, we prepend to the first user message
        if self.messages:
            self.messages[0]["content"] = f"[Long-term memory]\n{memory_summary}\n\n" + self.messages[0]["content"]