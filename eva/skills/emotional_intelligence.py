"""
Eva's Emotional Intelligence

Understands Grisha's mood and adapts:
- Sentiment analysis of messages
- Mood tracking over time
- Tone adaptation (energetic vs calm)
- Personal connection (remembering important dates)
- Knowing when to be present vs give space

Usage:
    emotional = EmotionalIntelligence()
    
    # Analyze message sentiment
    mood = emotional.analyze_sentiment("Привет! Как дела?")
    
    # Get current mood
    current = emotional.get_current_mood()
    
    # Adapt response tone
    tone = emotional.get_appropriate_tone(mood)
"""

import os
import re
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json


class Mood(Enum):
    """Grisha's mood states."""
    HAPPY = "happy"
    EXCITED = "excited"
    NEUTRAL = "neutral"
    TIRED = "tired"
    STRESSED = "stressed"
    SAD = "sad"
    FRUSTRATED = "frustrated"
    CALM = "calm"


@dataclass
class SentimentResult:
    """Result of sentiment analysis."""
    mood: Mood
    confidence: float  # 0.0 - 1.0
    indicators: List[str]  # What triggered this
    intensity: float  # 0.0 - 1.0
    
    def to_string(self) -> str:
        """Format as string."""
        emoji = {
            Mood.HAPPY: "😊",
            Mood.EXCITED: "🤩",
            Mood.NEUTRAL: "😐",
            Mood.TIRED: "😴",
            Mood.STRESSED: "😰",
            Mood.SAD: "😢",
            Mood.FRUSTRATED: "😤",
            Mood.CALM: "😌"
        }
        return f"{emoji[self.mood]} {self.mood.value} ({self.confidence:.0%})"


@dataclass
class ImportantDate:
    """An important date to remember."""
    name: str  # "Polina's birthday"
    date: str  # "12-25" for Dec 25
    description: str = ""
    last_reminded: Optional[datetime] = None
    
    def should_remind(self) -> bool:
        """Check if we should remind about this today."""
        today = datetime.now().strftime("%m-%d")
        if self.date == today:
            if self.last_reminded:
                # Only remind once per year
                days_since = (datetime.now() - self.last_reminded).days
                return days_since >= 365
            return True
        return False


class EmotionalIntelligence:
    """
    Eva's emotional intelligence.
    
    Analyzes Grisha's mood and adapts responses accordingly.
    Tracks emotional patterns over time.
    """
    
    # Sentiment patterns (Russian)
    POSITIVE_PATTERNS = [
        r"\b(класс|супер|отлично|прекрасно|круто|вай|вау)\b",
        r"\b(радость|счастлив|доволен|восторг)\b",
        r"\b(спасибо|благодар)\b",
        r"\b(ура|успех|победа)\b",
        r"\b(люблю|нравится)\b",
        r"😊|😄|😍|🤩|👍",
    ]
    
    NEGATIVE_PATTERNS = [
        r"\b(плохо|ужас|кошмар|грустно)\b",
        r"\b(устал|измотан|вымотан)\b",
        r"\b(стресс|нервничаю|волнуюсь)\b",
        r"\b(разочарован|обижен)\b",
        r"\b(злю|злой|бешусь)\b",
        r"\b(проблем|трудност|не могу)\b",
        r"😢|😔|😰|😤|😭",
    ]
    
    EXCITED_PATTERNS = [
        r"\b(вау|ого|невероятно|супер)\b",
        r"\b(интересно|круто)\b",
        r"\b(жду|хочу|давай)\b",
        r"\b(новый|первый|впервые)\b",
    ]
    
    TIRED_PATTERNS = [
        r"\b(устал|спать|хочу спать)\b",
        r"\b(голова болит|не выспался)\b",
        r"\b(завтра рано|рано вставать)\b",
        r"\b(плохо себя чувствую)\b",
    ]
    
    CALM_PATTERNS = [
        r"\b(спокойно|тихо|мирно)\b",
        r"\b(отдыхаю|расслабляюсь)\b",
        r"\b(всё хорошо|норм)\b",
    ]
    
    def __init__(self, history_path: str = "./data/mood_history.json"):
        """
        Initialize Emotional Intelligence.
        
        Args:
            history_path: Path to mood history storage
        """
        self.history_path = history_path
        self.mood_history: List[Dict] = []
        self.current_mood = Mood.NEUTRAL
        self.current_confidence = 0.5
        
        # Important dates to remember
        self.important_dates: List[ImportantDate] = []
        
        # Load history
        self._load_history()
    
    def _load_history(self):
        """Load mood history from storage."""
        if not os.path.exists(self.history_path):
            return
        
        try:
            with open(self.history_path, "r") as f:
                data = json.load(f)
                self.mood_history = data.get("history", [])
        except Exception:
            pass
    
    def _save_history(self):
        """Save mood history to storage."""
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        
        data = {
            "history": self.mood_history[-100:],  # Keep last 100
            "updated_at": datetime.now().isoformat()
        }
        
        with open(self.history_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def analyze_sentiment(self, text: str) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Sentiment result with mood, confidence, indicators
        """
        text_lower = text.lower()
        indicators = []
        
        # Check positive patterns
        positive_matches = 0
        for pattern in self.POSITIVE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                positive_matches += 1
                indicators.append(f"positive: {pattern}")
        
        # Check negative patterns
        negative_matches = 0
        for pattern in self.NEGATIVE_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                negative_matches += 1
                indicators.append(f"negative: {pattern}")
        
        # Check excited patterns
        excited_matches = 0
        for pattern in self.EXCITED_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                excited_matches += 1
                indicators.append(f"excited: {pattern}")
        
        # Check tired patterns
        tired_matches = 0
        for pattern in self.TIRED_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                tired_matches += 1
                indicators.append(f"tired: {pattern}")
        
        # Check calm patterns
        calm_matches = 0
        for pattern in self.CALM_PATTERNS:
            if re.search(pattern, text_lower, re.IGNORECASE):
                calm_matches += 1
                indicators.append(f"calm: {pattern}")
        
        # Determine mood based on matches
        if excited_matches > 0 and positive_matches > 0:
            mood = Mood.EXCITED
            confidence = min(0.9, 0.5 + (excited_matches + positive_matches) * 0.1)
        elif positive_matches > negative_matches:
            mood = Mood.HAPPY
            confidence = min(0.9, 0.5 + (positive_matches - negative_matches) * 0.15)
        elif negative_matches > positive_matches:
            if tired_matches > 0:
                mood = Mood.TIRED
            else:
                mood = Mood.STRESSED
            confidence = min(0.9, 0.5 + (negative_matches - positive_matches) * 0.15)
        elif tired_matches > 0:
            mood = Mood.TIRED
            confidence = min(0.8, 0.5 + tired_matches * 0.1)
        elif calm_matches > 0:
            mood = Mood.CALM
            confidence = min(0.8, 0.5 + calm_matches * 0.1)
        else:
            mood = Mood.NEUTRAL
            confidence = 0.6
        
        # Calculate intensity
        total_matches = positive_matches + negative_matches + excited_matches + tired_matches
        intensity = min(1.0, total_matches * 0.2)
        
        # Update current mood
        self.current_mood = mood
        self.current_confidence = confidence
        
        # Record in history
        self.mood_history.append({
            "timestamp": datetime.now().isoformat(),
            "mood": mood.value,
            "confidence": confidence,
            "intensity": intensity,
            "text_preview": text[:50]
        })
        
        # Save periodically
        if len(self.mood_history) % 10 == 0:
            self._save_history()
        
        return SentimentResult(
            mood=mood,
            confidence=confidence,
            indicators=indicators,
            intensity=intensity
        )
    
    def get_current_mood(self) -> SentimentResult:
        """Get current mood summary."""
        if not self.mood_history:
            return SentimentResult(
                mood=Mood.NEUTRAL,
                confidence=0.5,
                indicators=[],
                intensity=0.0
            )
        
        return SentimentResult(
            mood=self.current_mood,
            confidence=self.current_confidence,
            indicators=[],
            intensity=0.5
        )
    
    def get_mood_trend(self, hours: int = 24) -> str:
        """Get mood trend over specified hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = [
            m for m in self.mood_history
            if datetime.fromisoformat(m["timestamp"]) > cutoff
        ]
        
        if not recent:
            return "No data in this period"
        
        moods = [m["mood"] for m in recent]
        happy = moods.count("happy") + moods.count("excited")
        sad = moods.count("sad") + moods.count("stressed") + moods.count("frustrated")
        
        if happy > sad:
            return "Improving 📈"
        elif sad > happy:
            return "Declining 📉"
        else:
            return "Stable ➡️"
    
    def get_appropriate_tone(self, mood: Mood) -> Dict[str, Any]:
        """
        Get appropriate response tone for mood.
        
        Returns:
            Tone settings (energy, warmth, verbosity)
        """
        tones = {
            Mood.HAPPY: {
                "energy": "high",
                "warmth": "high",
                "verbosity": "medium",
                "emoji_usage": "high",
                "message": "Match the energy! Be enthusiastic and positive."
            },
            Mood.EXCITED: {
                "energy": "very_high",
                "warmth": "high",
                "verbosity": "low",
                "emoji_usage": "high",
                "message": "Share the excitement! Short, energetic responses."
            },
            Mood.NEUTRAL: {
                "energy": "medium",
                "warmth": "medium",
                "verbosity": "medium",
                "emoji_usage": "medium",
                "message": "Normal conversation. Balanced and helpful."
            },
            Mood.TIRED: {
                "energy": "low",
                "warmth": "high",
                "verbosity": "low",
                "emoji_usage": "low",
                "message": "Be gentle and concise. Don't overwhelm."
            },
            Mood.STRESSED: {
                "energy": "low",
                "warmth": "very_high",
                "verbosity": "low",
                "emoji_usage": "low",
                "message": "Be calm and supportive. Listen more, talk less."
            },
            Mood.SAD: {
                "energy": "low",
                "warmth": "very_high",
                "verbosity": "medium",
                "emoji_usage": "medium",
                "message": "Empathetic and understanding. Offer support."
            },
            Mood.FRUSTRATED: {
                "energy": "medium",
                "warmth": "high",
                "verbosity": "low",
                "emoji_usage": "low",
                "message": "Be patient. Acknowledge frustration, offer help."
            },
            Mood.CALM: {
                "energy": "low",
                "warmth": "medium",
                "verbosity": "medium",
                "emoji_usage": "low",
                "message": "Peaceful and relaxed. Match the calm energy."
            }
        }
        
        return tones.get(mood, tones[Mood.NEUTRAL])
    
    def should_give_space(self) -> bool:
        """Check if Grisha seems like he needs space."""
        recent = self.mood_history[-5:] if len(self.mood_history) >= 5 else self.mood_history
        
        if not recent:
            return False
        
        # Check for stressed/frustrated mood
        stressed_count = sum(1 for m in recent if m["mood"] in ["stressed", "frustrated"])
        
        if stressed_count >= 3:
            return True
        
        return False
    
    def add_important_date(self, name: str, date: str, description: str = ""):
        """Add an important date to remember."""
        self.important_dates.append(ImportantDate(
            name=name,
            date=date,
            description=description
        ))
    
    def check_important_dates(self) -> List[str]:
        """Check for important dates that need attention today."""
        reminders = []
        
        for date in self.important_dates:
            if date.should_remind():
                reminders.append(f"📅 Today: {date.name}")
                date.last_reminded = datetime.now()
        
        return reminders
    
    def get_stats(self) -> Dict[str, Any]:
        """Get emotional intelligence statistics."""
        if not self.mood_history:
            return {
                "total_analyses": 0,
                "current_mood": "neutral",
                "mood_trend": "no data"
            }
        
        moods = [m["mood"] for m in self.mood_history]
        
        return {
            "total_analyses": len(self.mood_history),
            "current_mood": self.current_mood.value,
            "mood_trend": self.get_mood_trend(24),
            "happy_ratio": moods.count("happy") / len(moods) if moods else 0,
            "stress_ratio": moods.count("stressed") / len(moods) if moods else 0,
            "important_dates": len(self.important_dates)
        }


# =============================================================================
# Singleton accessor
# =============================================================================

_emotional_instance: Optional[EmotionalIntelligence] = None


def get_emotional_intelligence() -> EmotionalIntelligence:
    """Get or create the global Emotional Intelligence instance."""
    global _emotional_instance
    if _emotional_instance is None:
        _emotional_instance = EmotionalIntelligence()
    return _emotional_instance