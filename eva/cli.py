"""
Eva — Main CLI Entry Point

Usage:
    python -m eva start          # Start conversation
    python -m eva voice "text"   # Make Eva speak
    python -m eva screenshot     # Capture screen
    python -m eva status         # Check Eva's status
"""

import os
import sys
import subprocess
import platform
from datetime import datetime

import click
from dotenv import load_dotenv

from eva.companion import Eva
from eva.memory.vector_store import get_memory
from eva.voice.tts import get_voice
from eva.vision.screen import get_vision
from eva.vision import detect_game

load_dotenv()


@click.group()
def cli():
    """🐍 Eva — AI Companion for Grisha."""
    pass


@cli.command()
@click.option("--proactive", is_flag=True, help="Enable proactive messages")
@click.option("--voice", is_flag=True, help="Enable voice output")
def start(proactive, voice):
    """Start Eva and begin a conversation."""
    click.echo("🐍 Starting Eva...")
    click.echo(f"   Model: {os.getenv('MODEL', 'claude-opus-4.6')}")
    click.echo(f"   Memory: enabled")
    click.echo(f"   Vision: enabled")
    if proactive:
        click.echo(f"   Proactive: enabled (5 min interval)")
    if voice:
        click.echo(f"   Voice: enabled")
    click.echo("")
    
    # Initialize Eva
    eva = Eva(proactive_interval=300 if proactive else 0)
    
    # Greet
    greeting = eva.greet()
    click.echo(f"Ева: {greeting}")
    click.echo("")
    
    # Start proactive mode if requested
    if proactive:
        eva.start_proactive_mode()
        click.echo("💬 Eva is now in proactive mode. She'll reach out periodically.")
        click.echo("")
    
    # Conversation loop
    while True:
        try:
            user_input = click.prompt("Гриша", type=str)
            
            if user_input.lower() in ["exit", "quit", "пока", "bye"]:
                click.echo("\nЕва: Пока, Гриша! Было классно пообщаться! 👋")
                if proactive:
                    eva.stop_proactive_mode()
                break
            
            if user_input.lower() == "reset":
                eva.reset()
                click.echo("\nЕва: Разговор сброшен. Начинаем с чистого листа! ✨\n")
                continue
            
            if user_input.lower() == "status":
                stats = eva.get_stats()
                click.echo(f"\n📊 Status:")
                click.echo(f"   Conversations: {stats['conversations']}")
                click.echo(f"   Uptime: {stats['uptime']}")
                click.echo(f"   Memories: {stats['memory_count']}")
                click.echo("")
                continue
            
            # Get response
            response = eva.think(user_input)
            click.echo(f"\nЕва: {response}")
            
            # Speak if voice enabled
            if voice:
                click.echo("\n🔊 Speaking...")
                audio_file = eva.speak(response)
                play_audio(audio_file)
            
            click.echo("")
            
        except KeyboardInterrupt:
            click.echo("\n\nЕва: Пока, Гриша! 👋")
            if proactive:
                eva.stop_proactive_mode()
            break
        except Exception as e:
            click.echo(f"\n❌ Error: {e}")


@cli.command()
@click.argument("text")
def voice(text):
    """Make Eva speak the given text."""
    click.echo(f"🔊 Eva says: {text}")
    
    eva_voice = get_voice()
    audio_file = eva_voice.speak(text)
    
    click.echo(f"📁 Saved to: {audio_file}")
    
    # Play audio
    play_audio(audio_file)


@cli.command()
@click.option("--save", is_flag=True, help="Save screenshot")
def screenshot(save):
    """Capture the screen."""
    click.echo("👁️ Capturing screen...")
    
    eva_vision = get_vision()
    
    try:
        filepath = eva_vision.capture_screen()
        click.echo(f"✅ Saved to: {filepath}")
        
        if save:
            click.echo("Screenshot saved.")
        else:
            # Just show the path, don't keep file
            os.remove(filepath)
            click.echo("Screenshot taken (not saved).")
            
    except Exception as e:
        click.echo(f"❌ Failed to capture: {e}")


@cli.command()
def status():
    """Check Eva's status and statistics."""
    memory = get_memory()
    
    click.echo("🐍 Eva Status")
    click.echo("─" * 30)
    click.echo(f"   Brain: Connected to {os.getenv('MODEL', 'claude-opus-4.6')}")
    click.echo(f"   Memory: {memory.collection.count()} memories stored")
    click.echo(f"   Voice: Edge TTS ready")
    click.echo(f"   Vision: MSS ready")
    click.echo(f"   Platform: {platform.system()}")
    click.echo(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    click.echo("─" * 30)


@cli.command()
@click.argument("query")
def recall(query):
    """Search Eva's memory."""
    memory = get_memory()
    memories = memory.recall(query)
    
    if not memories:
        click.echo("Ничего не найдено в памяти.")
        return
    
    click.echo(f"📖 Найдено {len(memories)} воспоминаний:\n")
    for i, m in enumerate(memories, 1):
        click.echo(f"  {i}. {m['content'][:150]}...")
        click.echo(f"     [{m['metadata'].get('timestamp', 'unknown')}]")
        click.echo("")


@cli.command()
def memory_clear():
    """Clear all Eva's memories. ⚠️ Destructive!"""
    if not click.confirm("Вы уверены? Все воспоминания Евы будут удалены!"):
        click.echo("Отменено.")
        return
    
    memory = get_memory()
    
    # Delete all items
    try:
        memory.client.delete_collection("eva_memories")
        memory.client.delete_collection("grisha_facts")
        click.echo("✅ Память очищена.")
    except Exception as e:
        click.echo(f"❌ Error: {e}")


@cli.group()
def gaming():
    """🎮 Gaming mode — Eva watches your screen during games."""
    pass


@gaming.command(name="start")
@click.option("--voice", is_flag=True, help="Speak advice aloud")
def gaming_start(voice):
    """Start gaming mode — Eva watches and advises."""
    click.echo("🎮 Starting Gaming Mode...")
    
    # Check if game is running
    game = detect_game()
    if game:
        click.echo(f"✅ Game detected: {game.name}")
    else:
        click.echo("⚠️ No game detected. Will activate when game starts.")
    
    click.echo("   Analyzing screen every 5 seconds...")
    click.echo("   Press Ctrl+C to stop")
    click.echo("")
    
    # Initialize Eva with gaming
    eva = Eva()
    
    def on_advice(advice):
        click.echo(f"\n🎯 Ева: {advice}\n")
        if voice:
            audio_file = eva.speak(advice)
            play_audio(audio_file)
    
    eva.start_gaming_mode(on_advice=on_advice)
    
    try:
        # Keep running
        while eva.gaming_active:
            import time
            time.sleep(1)
    except KeyboardInterrupt:
        eva.stop_gaming_mode()
        click.echo("\n\n🎮 Gaming mode stopped.")


@gaming.command(name="check")
def gaming_check():
    """Check if a game is currently running."""
    game = detect_game()
    
    if game:
        click.echo(f"✅ Game detected: {game.name}")
        click.echo(f"   Type: {game.type.value}")
        click.echo(f"   Process: {game.process_name}")
    else:
        click.echo("❌ No game detected.")


@gaming.command(name="analyze")
@click.option("--voice", is_flag=True, help="Speak advice aloud")
def gaming_analyze(voice):
    """Manually analyze current screen."""
    click.echo("👁️ Analyzing screen...")
    
    game = detect_game()
    if not game:
        click.echo("❌ No game detected.")
        return
    
    click.echo(f"✅ Game: {game.name}")
    
    # Analyze
    eva = Eva()
    advice = eva.analyze_screen()
    
    if advice:
        click.echo(f"\n🎯 Ева: {advice}")
        
        if voice:
            audio_file = eva.speak(advice)
            play_audio(audio_file)
    else:
        click.echo("❌ Could not analyze screen.")


@gaming.command(name="stats")
def gaming_stats():
    """Show gaming session statistics."""
    eva = Eva()
    stats = eva.get_gaming_stats()
    
    if not stats:
        click.echo("❌ No gaming session active.")
        return
    
    click.echo("🎮 Gaming Stats")
    click.echo("─" * 30)
    for key, value in stats.items():
        click.echo(f"   {key}: {value}")
    click.echo("─" * 30)


def play_audio(filepath: str):
    """Play audio file using system default player."""
    system = platform.system()
    
    try:
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Darwin":  # macOS
            subprocess.run(["open", filepath])
        else:  # Linux
            subprocess.run(["xdg-open", filepath])
    except Exception as e:
        click.echo(f"⚠️ Could not play audio: {e}")
        click.echo(f"   File saved at: {filepath}")


if __name__ == "__main__":
    cli()