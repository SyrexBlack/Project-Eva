"""
Eva — Main Entry Point

This is the main module that brings Eva to life.
Run this to start Eva as a CLI assistant.
"""

import os
import sys
from datetime import datetime
from typing import Optional

import click
from dotenv import load_dotenv

from eva.core.brain import EvaBrain
from eva.core.personality import EVA_GREETING
from eva.memory.vector_store import get_memory

# Load environment
load_dotenv()


class Eva:
    """
    Eva — AI Companion for Grisha.
    
    This is the main class that orchestrates all of Eva's components:
    - Brain (AI thinking)
    - Memory (long-term storage)
    - Voice (future)
    - Vision (future)
    """
    
    def __init__(self):
        """Initialize Eva."""
        # Get config from environment
        self.base_url = os.getenv("BASE_URL", "http://89.167.8.202:8000/v1")
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("MODEL", "claude-opus-4.6")
        
        # Initialize brain
        self.brain = EvaBrain(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model
        )
        
        # Initialize memory
        self.memory = get_memory()
        
        # State
        self.name = "Ева"
        self.started_at = datetime.now()
    
    def think(self, user_input: str, use_memory: bool = True) -> str:
        """
        Make Eva think and respond.
        
        Args:
            user_input: What Grisha said
            use_memory: Whether to include memory context
        
        Returns:
            Eva's response
        """
        # Build context
        context = {}
        
        if use_memory:
            # Get relevant memories
            memory_context = self.memory.get_context(user_input)
            if memory_context:
                context["memory"] = memory_context
        
        # Add time context
        context["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Get response
        response = self.brain.think(user_input, context)
        
        # Store this interaction in memory
        self.memory.remember(
            content=f"Grisha said: {user_input}\nEva responded: {response}",
            metadata={
                "type": "conversation",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        return response
    
    def greet(self) -> str:
        """Get Eva's greeting."""
        return self.brain.greet()
    
    def reset(self):
        """Reset Eva's brain (new conversation)."""
        self.brain.reset()


# CLI Interface
@click.group()
def cli():
    """Eva — AI Companion for Grisha."""
    pass


@cli.command()
def start():
    """Start Eva and begin a conversation."""
    eva = Eva()
    
    click.echo("🐍 Starting Eva...")
    click.echo(f"   Model: {eva.model}")
    click.echo(f"   Memory: {'enabled' if eva.memory else 'disabled'}")
    click.echo("")
    
    # Greet
    greeting = eva.greet()
    click.echo(f"Ева: {greeting}")
    click.echo("")
    
    # Conversation loop
    while True:
        try:
            user_input = click.prompt("Гриша", type=str)
            
            if user_input.lower() in ["exit", "quit", "пока", "bye"]:
                click.echo("Ева: Пока, Гриша! Было классно пообщаться! 👋")
                break
            
            if user_input.lower() == "reset":
                eva.reset()
                click.echo("Ева: Разговор сброшен. Начинаем с чистого листа! ✨")
                continue
            
            response = eva.think(user_input)
            click.echo(f"Ева: {response}")
            click.echo("")
            
        except KeyboardInterrupt:
            click.echo("\nЕва: Пока, Гриша! 👋")
            break
        except Exception as e:
            click.echo(f"❌ Error: {e}")


@cli.command()
def memory_check():
    """Check Eva's memory status."""
    eva = Eva()
    summary = eva.memory.get_memory_summary()
    click.echo(f"📚 Eva's Memory:\n{summary}")


@cli.command()
@click.argument("query")
def recall(query):
    """Search Eva's memory."""
    eva = Eva()
    memories = eva.memory.recall(query)
    
    if not memories:
        click.echo("Ничего не найдено в памяти.")
        return
    
    click.echo(f"📖 Найдено {len(memories)} воспоминаний:\n")
    for m in memories:
        click.echo(f"  • {m['content'][:100]}...")
        click.echo(f"    ({m['metadata'].get('timestamp', 'unknown')})\n")


if __name__ == "__main__":
    cli()
