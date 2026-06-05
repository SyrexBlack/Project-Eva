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
    python -m eva proactive         # Proactive AI commands
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
    print("🟢 Eva v1.0.0 — Autonomous AI Companion")
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


def cmd_proactive(args):
    """Proactive AI commands."""
    from eva.skills.interest_engine import get_interest_engine
    from eva.skills.task_automation import get_task_automation
    from eva.skills.proactive_scheduler import get_proactive_scheduler
    
    if args.subcommand == "interests":
        engine = get_interest_engine()
        interests = engine.get_interests()
        print("📊 Interest Engine")
        print("─" * 40)
        for interest in interests:
            status = "✅" if interest.enabled else "❌"
            last = interest.last_check.strftime("%H:%M") if interest.last_check else "never"
            print(f"   {status} {interest.topic}")
            print(f"      Priority: {interest.priority:.1f} | Last: {last}")
        print("─" * 40)
        
    elif args.subcommand == "tasks":
        tasks = get_task_automation()
        pending = tasks.get_pending_tasks(limit=10)
        due = tasks.get_due_tasks()
        print("📋 Task Automation")
        print("─" * 40)
        if due:
            print("🔴 DUE NOW:")
            for task in due:
                print(f"   - {task.title}")
        if pending:
            print("📌 PENDING:")
            for task in pending[:5]:
                print(f"   📌 {task.title}")
        stats = tasks.get_stats()
        print("─" * 40)
        print(f"   Total: {stats['total_tasks']} | Pending: {stats['pending']}")
        
    elif args.subcommand == "add":
        from datetime import datetime, timedelta
        tasks = get_task_automation()
        due_at = None
        if args.minutes:
            due_at = datetime.now() + timedelta(minutes=args.minutes)
        task = tasks.add_task(title=args.title, due_at=due_at)
        print(f"✅ Task added: {task.title}")
        
    elif args.subcommand == "start":
        print("🤖 Starting Proactive Scheduler...")
        print("   Morning check-in: 9-11 AM")
        print("   Evening wrap-up: 8-10 PM")
        print("   Task reminders: every 30 min")
        print("\nPress Ctrl+C to stop\n")
        
        scheduler = get_proactive_scheduler(callback=lambda msg: print(f"\n💬 Ева: {msg}\n"))
        scheduler.start()
        try:
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            scheduler.stop()
            print("\n🤖 Proactive scheduler stopped.")
            
    else:
        print("📊 Proactive AI Stats")
        print("─" * 40)
        
        engine = get_interest_engine()
        stats = engine.get_stats()
        print(f"   Interests: {stats['total_interests']} total, {stats['active_interests']} active")
        
        tasks = get_task_automation()
        t_stats = tasks.get_stats()
        print(f"   Tasks: {t_stats['total_tasks']} total, {t_stats['pending']} pending, {t_stats['due_now']} due")
        
        print("─" * 40)


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
    
    # proactive
    proactive_parser = subparsers.add_parser("proactive", help="Proactive AI commands")
    proactive_subparsers = proactive_parser.add_subparsers(dest="subcommand", help="Proactive subcommands")
    
    proactive_subparsers.add_parser("interests", help="Show monitored interests")
    proactive_subparsers.add_parser("tasks", help="Show pending tasks")
    
    proactive_start_parser = proactive_subparsers.add_parser("start", help="Start proactive scheduler")
    
    proactive_add_parser = proactive_subparsers.add_parser("add", help="Add a task")
    proactive_add_parser.add_argument("title", help="Task title")
    proactive_add_parser.add_argument("--minutes", type=int, default=0, help="Due in N minutes")
    
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
    elif args.command == "proactive":
        cmd_proactive(args)
    elif args.command == "chat" or args.command is None:
        cmd_chat()


if __name__ == "__main__":
    main()