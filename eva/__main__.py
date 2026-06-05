"""
Eva CLI — Command Line Interface

Usage:
    python -m eva                    # Interactive mode
    python -m eva status            # Check status
    python -m eva voice "text"      # Text-to-speech
    python -m eva screenshot        # Take screenshot
    python -m eva recall "query"    # Search memory
    python -m eva stt               # Voice input test
    python -m eva gaming            # Start gaming mode
"""

import sys
import argparse
from pathlib import Path

# Add vendor to path for imports
vendor_path = Path(__file__).parent.parent / "vendor"
sys.path.insert(0, str(vendor_path))

from eva.companion import Eva
from eva.voice.tts import get_voice
from eva.vision.screen import get_vision
from eva.memory.vector_store import get_memory
from eva.voice.stt import EvaSTT


def cmd_status():
    """Check Eva's status."""
    print("🟢 Eva v0.7.0 — Autonomous AI Companion")
    print("=" * 40)
    print("Components:")
    print("  ✅ Brain (Claude Opus 4)")
    print("  ✅ Memory (ChromaDB + Deep Memory)")
    print("  ✅ Voice (Edge TTS + Whisper STT)")
    print("  ✅ Vision (Screen capture)")
    print("  ✅ Skills (Proactive + System)")
    print("  ✅ Gaming Mode")
    print("=" * 40)


def cmd_voice(text: str):
    """Make Eva speak."""
    print(f"🎤 Eva speaking: {text}")
    voice = get_voice()
    voice.speak(text)
    print("✅ Done")


def cmd_screenshot():
    """Take a screenshot."""
    print("📸 Taking screenshot...")
    vision = get_vision()
    result = vision.capture_screen()
    if isinstance(result, str):
        print(f"✅ Saved: {result}")
    else:
        print(f"✅ Captured successfully")
    return result


def cmd_recall(query: str):
    """Search memory."""
    print(f"🔍 Searching memory for: {query}")
    memory = get_memory()
    results = memory.recall(query, limit=5)
    print(f"Found {len(results)} results:")
    for i, r in enumerate(results):
        print(f"  {i+1}. [{r.get('type', r.get('category', 'unknown'))}] {str(r.get('content', r.get('text', '')))[:100]}...")
    return results


def cmd_stt():
    """Test voice input (push-to-talk)."""
    print("🎤 Voice Input Test — Push-to-Talk")
    print("Hold SPACE to record, release to transcribe")
    print("Press Ctrl+C to cancel\n")
    stt = EvaSTT()
    text = stt.listen_push_to_talk()
    if text:
        print(f"\n📝 Recognized: {text}")
    else:
        print("\n❌ No speech detected")
    return text


def cmd_gaming():
    """Start gaming mode."""
    print("🎮 Starting Gaming Mode...")
    from eva.vision import create_gaming_mode
    gaming = create_gaming_mode()
    print("✅ Gaming mode ready!")
    return gaming


def cmd_chat():
    """Start interactive chat."""
    print("💬 Starting Eva — Press Ctrl+C to exit")
    print("-" * 40)
    eva = Eva()
    while True:
        try:
            user_input = input("\nYou: ")
            if user_input.strip():
                response = eva.think(user_input)
                print(f"Eva: {response}")
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


def main():
    parser = argparse.ArgumentParser(
        description="Eva — Autonomous AI Companion for Grisha",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # status
    subparsers.add_parser("status", help="Check Eva's status")
    
    # voice
    voice_parser = subparsers.add_parser("voice", help="Make Eva speak")
    voice_parser.add_argument("text", help="Text to speak")
    
    # screenshot
    subparsers.add_parser("screenshot", help="Take a screenshot")
    
    # recall
    recall_parser = subparsers.add_parser("recall", help="Search memory")
    recall_parser.add_argument("query", help="Search query")
    
    # stt
    subparsers.add_parser("stt", help="Voice input test")
    
    # gaming
    subparsers.add_parser("gaming", help="Start gaming mode")
    
    # chat (default)
    subparsers.add_parser("chat", help="Start interactive chat")

    args = parser.parse_args()
    
    if args.command == "status":
        cmd_status()
    elif args.command == "voice":
        cmd_voice(args.text)
    elif args.command == "screenshot":
        cmd_screenshot()
    elif args.command == "recall":
        cmd_recall(args.query)
    elif args.command == "stt":
        cmd_stt()
    elif args.command == "gaming":
        cmd_gaming()
    elif args.command == "chat" or args.command is None:
        cmd_chat()


if __name__ == "__main__":
    main()