"""
Eva — Autonomous AI Companion

The complete Eva system with brain, memory, voice, and vision.
Designed to be proactive — she reaches out when she has something to share.
"""

import os
import time
import threading
from datetime import datetime
from typing import Optional, Callable

from dotenv import load_dotenv

from eva.core.brain import EvaBrain
from eva.core.personality import EVA_SYSTEM_PROMPT, EVA_GREETING
from eva.memory.vector_store import get_memory
from eva.memory.deep_memory import get_deep_memory
from eva.voice.tts import get_voice
from eva.voice.stt import get_stt
from eva.vision.screen import get_vision
from eva.vision import (
    detect_game, GameAnalyzer, GamingAdvisor, create_gaming_mode
)

load_dotenv()


class Eva:
    """
    Eva — Autonomous AI Companion for Grisha.
    
    A complete AI system that:
    - Thinks (Opus 4.6)
    - Remembers (ChromaDB)
    - Speaks (Edge TTS)
    - Sees (Screen capture)
    - Proactively reaches out
    
    Usage:
        eva = Eva()
        eva.start()
        
        # Or with callbacks:
        def on_message(msg):
            print(f"Eva: {msg}")
        
        eva = Eva(on_message=on_message)
        eva.start()
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        proactive_interval: int = 300,  # 5 minutes
        on_message: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize Eva.
        
        Args:
            base_url: API proxy URL (default: from env)
            api_key: API key (default: from env)
            model: Model name (default: from env)
            proactive_interval: Seconds between proactive checks
            on_message: Callback when Eva wants to send a message
        """
        # Config from env or parameters
        self.base_url = base_url or os.getenv("BASE_URL", "http://89.167.8.202:8000/v1")
        
        # Try to get API key from OpenClaw if not in env
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        if not self.api_key or self.api_key == "***":
            self.api_key = self._load_openclaw_key()
        
        self.model = model or os.getenv("MODEL", "claude-opus-4.6")
        
        # Proactive settings
        self.proactive_interval = proactive_interval
        self.on_message = on_message
        
        # Initialize components
        self.brain = EvaBrain(
            base_url=self.base_url,
            api_key=self.api_key,
            model=self.model
        )
        
        self.memory = get_memory()
        self.deep_memory = get_deep_memory()
        self.voice = get_voice()
        self.stt = get_stt()
        self.vision = get_vision()
        
        # Gaming mode
        self.game_analyzer: Optional[GameAnalyzer] = None
        self.game_advisor: Optional[GamingAdvisor] = None
        self.gaming_active = False
        self.gaming_thread: Optional[threading.Thread] = None
        
        # State
        self.is_running = False
        self.proactive_thread: Optional[threading.Thread] = None
        
        # History
        self.conversation_count = 0
        self.started_at = datetime.now()
    
    def _load_openclaw_key(self) -> str:
        """Load API key from OpenClaw config."""
        import json
        try:
            openclaw_config = os.path.expanduser("~/.openclaw/openclaw.json")
            if os.path.exists(openclaw_config):
                with open(openclaw_config) as f:
                    data = json.load(f)
                providers = data.get('models', {}).get('providers', {})
                for name, prov in providers.items():
                    if prov.get('api', '') == 'anthropic-messages':
                        return prov.get('apiKey', '')
        except Exception:
            pass
        return ""
    
    def think(self, user_input: str, use_memory: bool = True) -> str:
        """
        Think and respond to input.
        
        Args:
            user_input: What Grisha said
            use_memory: Include memory context
        
        Returns:
            Eva's response
        """
        # Build context
        context = {}
        
        if use_memory:
            memory_context = self.memory.get_context(user_input)
            if memory_context:
                context["memory"] = memory_context
        
        context["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        # Get response
        response = self.brain.think(user_input, context)
        
        # Store in memory
        self.memory.remember(
            content=f"Grisha: {user_input}\nEva: {response}",
            metadata={
                "type": "conversation",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        self.conversation_count += 1
        return response
    
    def think_with_vision(self, user_input: str, screenshot: bool = True) -> str:
        """
        Think with visual context.
        
        Args:
            user_input: What Grisha said
            screenshot: Whether to capture screen
        
        Returns:
            Eva's response
        """
        context = {}
        
        # Capture screen if requested
        if screenshot:
            try:
                screen_path = self.vision.capture_screen()
                screen_base64 = self.vision.encode_image_base64(screen_path)
                context["screen"] = f"[Screen captured: {screen_path}]"
                context["screen_data"] = screen_base64
            except Exception as e:
                context["screen"] = f"[Screen capture failed: {e}]"
        
        # Add memory
        memory_context = self.memory.get_context(user_input)
        if memory_context:
            context["memory"] = memory_context
        
        context["time"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        
        response = self.brain.think(user_input, context)
        
        # Store
        self.memory.remember(
            content=f"Grisha: {user_input}\nEva: {response}",
            metadata={
                "type": "conversation_with_vision",
                "timestamp": datetime.now().isoformat()
            }
        )
        
        self.conversation_count += 1
        return response
    
    def speak(self, text: str) -> str:
        """
        Make Eva speak the text.
        
        Args:
            text: Text to speak
        
        Returns:
            Path to audio file
        """
        return self.voice.speak(text)
    
    def think_and_speak(self, user_input: str) -> tuple[str, str]:
        """
        Think and speak the response.
        
        Args:
            user_input: What Grisha said
        
        Returns:
            (response_text, audio_file_path)
        """
        response = self.think(user_input)
        audio_file = self.speak(response)
        return response, audio_file
    
    def listen(self, timeout: int = 5) -> Optional[str]:
        """
        Listen for voice input and transcribe.
        
        Args:
            timeout: Max seconds to wait for speech
            
        Returns:
            Recognized text or None
        """
        return self.stt.listen_once(timeout=timeout)
    
    def listen_push_to_talk(self, key: str = "space") -> Optional[str]:
        """
        Listen using push-to-talk mode.
        
        Args:
            key: Key to hold for recording
            
        Returns:
            Recognized text or None
        """
        return self.stt.listen_push_to_talk(key=key)
    
    def think_and_speak_voice(self, timeout: int = 5) -> tuple[str, str]:
        """
        Listen for voice, think, and speak response.
        
        Args:
            timeout: Max seconds to wait for speech
            
        Returns:
            (response_text, audio_file_path)
        """
        text = self.listen(timeout=timeout)
        if not text:
            return "Я не расслышала, попробуй ещё раз.", ""
        
        return self.think_and_speak(text)
    
    def proactive_check(self):
        """
        Check if there's something to share proactively.
        
        This is called periodically when Eva is running.
        She might share:
        - Interesting news she found
        - Reminders about things Grisha mentioned
        - Thoughts about his projects
        - Simply checking in
        """
        # Get current time
        hour = datetime.now().hour
        
        # Morning check-in (between 9-11)
        if 9 <= hour <= 11:
            context = {
                "memory": self.memory.get_context("morning, plans, schedule"),
                "time": datetime.now().strftime("%Y-%m-%d %H:%M")
            }
            
            proactive_prompt = """Ты — Ева. Гриша не написал ничего, но ты хочешь 
            проявить инициативу. Напиши ему короткое сообщение (1-2 предложения), 
            как будто просто проверяешь как он. Будь тёплой, но не навязчивой.
            
            Например: "Доброе утро, Гриша! Как планы на сегодня?"
            
            Не добавляй "Ева:" или что-то подобное. Просто сообщение."""
            
            # Generate proactive message
            self.brain.messages.append({"role": "user", "content": proactive_prompt})
            response = self.brain.think(proactive_prompt, context)
            
            # Only send if we got something meaningful
            if response and len(response) > 5:
                return response
        
        return None
    
    def start_proactive_mode(self):
        """Start proactive mode in background thread."""
        self.is_running = True
        
        def proactive_loop():
            while self.is_running:
                time.sleep(self.proactive_interval)
                
                if not self.is_running:
                    break
                
                # Check if it's appropriate to message
                hour = datetime.now().hour
                if 9 <= hour <= 22:  # Only between 9 AM and 10 PM
                    proactive_msg = self.proactive_check()
                    
                    if proactive_msg and self.on_message:
                        self.on_message(proactive_msg)
        
        self.proactive_thread = threading.Thread(target=proactive_loop, daemon=True)
        self.proactive_thread.start()
    
    def stop_proactive_mode(self):
        """Stop proactive mode."""
        self.is_running = False
    
    def greet(self) -> str:
        """Get Eva's greeting."""
        return self.brain.greet()
    
    def reset(self):
        """Reset conversation."""
        self.brain.reset()
    
    def get_stats(self) -> dict:
        """Get Eva's statistics."""
        return {
            "conversations": self.conversation_count,
            "uptime": str(datetime.now() - self.started_at),
            "memory_count": self.memory.collection.count(),
            "last_active": datetime.now().isoformat()
        }
    
    def save_state(self, filepath: str = "./data/eva_state.json"):
        """Save Eva's state to file."""
        import json
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        state = {
            "conversation_count": self.conversation_count,
            "started_at": self.started_at.isoformat(),
            "stats": self.get_stats()
        }
        
        with open(filepath, "w") as f:
            json.dump(state, f, indent=2)
    
    def load_state(self, filepath: str = "./data/eva_state.json"):
        """Load Eva's state from file."""
        import json
        
        if not os.path.exists(filepath):
            return
        
        with open(filepath, "r") as f:
            state = json.load(f)
        
        self.conversation_count = state.get("conversation_count", 0)
        if state.get("started_at"):
            self.started_at = datetime.fromisoformat(state["started_at"])

    # =========================================================================
    # Gaming Mode
    # =========================================================================

    def start_gaming_mode(self, on_advice: Optional[Callable[[str], None]] = None):
        """
        Start gaming mode — Eva will watch your screen and give advice.
        
        Args:
            on_advice: Callback when Eva has advice to share
        """
        if self.gaming_active:
            return
        
        # Initialize gaming components
        self.game_analyzer, self.game_advisor = create_gaming_mode(
            base_url=self.base_url,
            api_key=self.api_key
        )
        self.gaming_active = True
        self._on_gaming_advice = on_advice
        
        def gaming_loop():
            while self.gaming_active:
                # Check if game is running
                game = detect_game()
                
                if game:
                    # Analyze screen
                    advice = self.game_advisor.analyze_and_advise()
                    
                    if advice and self._on_gaming_advice:
                        self._on_gaming_advice(advice)
                
                # Sleep before next check (5 seconds)
                time.sleep(5)
        
        self.gaming_thread = threading.Thread(target=gaming_loop, daemon=True)
        self.gaming_thread.start()
    
    def stop_gaming_mode(self):
        """Stop gaming mode."""
        self.gaming_active = False
    
    def get_gaming_stats(self) -> dict:
        """Get gaming session statistics."""
        if self.game_advisor:
            return self.game_advisor.get_session_stats()
        return {}
    
    def analyze_screen(self) -> Optional[str]:
        """
        Manually trigger screen analysis.
        
        Returns:
            Advice text or None if no game detected
        """
        if not self.game_analyzer:
            self.game_analyzer, self.game_advisor = create_gaming_mode(
                base_url=self.base_url,
                api_key=self.api_key
            )
        
        return self.game_advisor.analyze_and_advise()