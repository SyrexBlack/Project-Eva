"""
Eva's Emotional Intelligence Module

Понимает настроение и адаптируется:
- Mood Detection: анализ текста и голоса на настроение
- Personal Connection: важные даты, поддержка, шутки
- Adaptive Tone: подстраивает стиль общения

Как это работает:
1. Анализирует текст/голос на эмоции
2. Определяет настроение Гриши
3. Адаптирует ответы под ситуацию
4. Запоминает важные эмоциональные события
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class Mood(Enum):
    """Настроение."""
    VERY_HAPPY = "very_happy"
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    ANXIOUS = "anxious"
    ANGRY = "angry"
    EXCITED = "excited"
    TIRED = "tired"
    FRUSTRATED = "frustrated"
    UNKNOWN = "unknown"


class EmotionalState:
    """Эмоциональное состояние."""
    mood: Mood
    confidence: float  # 0.0 - 1.0
    intensity: float   # 0.0 - 1.0
    triggers: List[str]  # Что вызвало такое настроение
    timestamp: datetime


@dataclass
class ImportantDate:
    """Важная дата."""
    name: str
    date: datetime
    description: str
    remind_days: int = 7  # За сколько дней напоминать


@dataclass
class PersonalPreference:
    """Личная преференция."""
    category: str      # humor, tone, topics, etc
    preference: str    # Конкретное значение
    evidence: List[str]  # Откуда это известно


class MoodDetector:
    """
    Определение настроения по тексту.
    
    Использует keyword-based подход + паттерны.
    """
    
    # Ключевые слова для каждого настроения
    MOOD_PATTERNS = {
        Mood.VERY_HAPPY: [
            r"\bсчастлив\b", r"\bвосторг\b", r"\bобожаю\b", r"\bпрекрасно\b",
            r"\bклассно\b", r"\bсупер\b", r"\bобалденно\b", r"🎉", r"😍", r"❤️",
            r"\bлучший\b", r"\bпотрясающ\b"
        ],
        Mood.HAPPY: [
            r"\bрад\b", r"\bхорош\b", r"\bнорм\b", r"\bнормально\b", r"\bприятно\b",
            r"\bулыба\b", r"😊", r"😄", r"👍", r"\bотлично\b", r"\bхорошо\b"
        ],
        Mood.EXCITED: [
            r"\bвау\b", r"\bого\b", r"\bневероятно\b", r"\bохуенно\b", r"\bобалдеть\b",
            r"\bкруто\b", r"🔥", r"💪", r"\bвосторжен\b"
        ],
        Mood.SAD: [
            r"\bгрустн\b", r"\bтоскливо\b", r"\bпечаль\b", r"\bплака\b", r"\bслеза\b",
            r"😢", r"😞", r"💔", r"\bтоска\b", r"\bгрусть\b"
        ],
        Mood.ANXIOUS: [
            r"\bволну\b", r"\bпережива\b", r"\bстрашн\b", r"\bтревог\b", r"\bбоюсь\b",
            r"😰", r"😨", r"\bнеопределённост\b", r"\bнеизвестност\b"
        ],
        Mood.ANGRY: [
            r"\bзл\b", r"\bбесит\b", r"\bненавиж\b", r"\bраздража\b", r"\bвыходит\b",
            r"😠", r"😤", r"🤬", r"\bчёрт\b", r"\bблять\b", r"\bfuck\b"
        ],
        Mood.TIRED: [
            r"\bустал\b", r"\bспать\b", r"\bизмотан\b", r"\bвымотан\b", r"\bсон\b",
            r"😴", r"😪", r"\bваля\b", r"\bотдыха\b", r"\bхочу спать\b"
        ],
        Mood.FRUSTRATED: [
            r"\bне могу\b", r"\bне получается\b", r"\bзастрял\b", r"\bтупик\b",
            r"\bвсё бесполезно\b", r"\bничего не выходит\b", r"🤦", r"😩"
        ],
    }
    
    def detect(self, text: str) -> EmotionalState:
        """
        Определить настроение по тексту.
        
        Args:
            text: Текст для анализа
            
        Returns:
            EmotionalState с определённым настроением
        """
        text_lower = text.lower()
        
        mood_scores: Dict[Mood, float] = {}
        
        for mood, patterns in self.MOOD_PATTERNS.items():
            score = 0
            triggers = []
            
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    score += 1
                    triggers.append(pattern)
            
            if score > 0:
                mood_scores[mood] = score
        
        if not mood_scores:
            return EmotionalState(
                mood=Mood.UNKNOWN,
                confidence=0.0,
                intensity=0.0,
                triggers=[],
                timestamp=datetime.now()
            )
        
        # Определяем доминирующее настроение
        dominant_mood = max(mood_scores, key=mood_scores.get)
        
        # Confidence зависит от количества совпадений
        max_score = max(mood_scores.values())
        confidence = min(max_score / 3, 1.0)  # Максимум 1.0 при 3+ совпадениях
        
        # Intensity — относительная разница с другими настроениями
        if len(mood_scores) > 1:
            second_score = sorted(mood_scores.values())[-2]
            intensity = (max_score - second_score) / max_score if max_score else 0
        else:
            intensity = 1.0
        
        return EmotionalState(
            mood=dominant_mood,
            confidence=confidence,
            intensity=intensity,
            triggers=[],
            timestamp=datetime.now()
        )
    
    def get_response_tone(self, mood: Mood) -> str:
        """Получить тон ответа для настроения."""
        tones = {
            Mood.VERY_HAPPY: "energetic",
            Mood.HAPPY: "warm",
            Mood.NEUTRAL: "balanced",
            Mood.SAD: "gentle_supportive",
            Mood.ANXIOUS: "calming_reassuring",
            Mood.ANGRY: "patient_understanding",
            Mood.EXCITED: "enthusiastic",
            Mood.TIRED: "soft_low_energy",
            Mood.FRUSTRATED: "encouraging_helpful",
            Mood.UNKNOWN: "neutral"
        }
        return tones.get(mood, "neutral")
    
    def get_response_style(self, mood: Mood) -> Dict[str, Any]:
        """Получить стиль ответа для настроения."""
        styles = {
            Mood.VERY_HAPPY: {
                "emoji": "✨",
                "enthusiasm": 1.0,
                "ask_questions": True,
                "share_excitement": True
            },
            Mood.HAPPY: {
                "emoji": "😊",
                "enthusiasm": 0.7,
                "ask_questions": True,
                "share_excitement": False
            },
            Mood.NEUTRAL: {
                "emoji": "🤔",
                "enthusiasm": 0.5,
                "ask_questions": True,
                "share_excitement": False
            },
            Mood.SAD: {
                "emoji": "💙",
                "enthusiasm": 0.3,
                "ask_questions": False,
                "share_excitement": False,
                "offer_support": True
            },
            Mood.ANXIOUS: {
                "emoji": "🌸",
                "enthusiasm": 0.3,
                "ask_questions": False,
                "offer_reassurance": True,
                "be_calm": True
            },
            Mood.ANGRY: {
                "emoji": "💜",
                "enthusiasm": 0.3,
                "be_patient": True,
                "validate_feelings": True,
                "offer_help": True
            },
            Mood.EXCITED: {
                "emoji": "🔥",
                "enthusiasm": 1.0,
                "match_energy": True,
                "ask_questions": True
            },
            Mood.TIRED: {
                "emoji": "🌙",
                "enthusiasm": 0.2,
                "be_gentle": True,
                "offer_short_answers": True,
                "suggest_rest": True
            },
            Mood.FRUSTRATED: {
                "emoji": "💪",
                "enthusiasm": 0.4,
                "be_encouraging": True,
                "offer_help": True,
                "break_down_problem": True
            }
        }
        return styles.get(mood, styles[Mood.NEUTRAL])


class PersonalConnection:
    """
    Личная связь с Гришей.
    
    Запоминает важные даты, интересы, преференции.
    """
    
    def __init__(self):
        self.important_dates: List[ImportantDate] = []
        self.preferences: List[PersonalPreference] = []
        self.mood_history: List[EmotionalState] = []
        self._init_defaults()
    
    def _init_defaults(self):
        """Инициализировать дефолтные важные даты."""
        # День рождения Гриши
        self.important_dates.append(ImportantDate(
            name="День рождения Гриши",
            date=datetime(1997, 11, 1),
            description="Грише исполняется ещё один год!",
            remind_days=7
        ))
        
        # Годовщина свадьбы (假设ная дата — нужно уточнить у Гриши)
        # self.important_dates.append(ImportantDate(
        #     name="Годовщина свадьбы",
        #     date=datetime(2023, 6, 15),  # TODO: уточнить дату
        #     description="Годовщина свадьбы с Полиной!",
        #     remind_days=7
        # ))
    
    def add_important_date(
        self,
        name: str,
        date: datetime,
        description: str,
        remind_days: int = 7
    ):
        """Добавить важную дату."""
        self.important_dates.append(ImportantDate(
            name=name,
            date=date,
            description=description,
            remind_days=remind_days
        ))
    
    def get_upcoming_dates(self, days: int = 30) -> List[Dict[str, Any]]:
        """Получить предстоящие важные даты."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        upcoming = []
        for date in self.important_dates:
            # Проверяем наступила ли дата в этом году
            this_year = date.date.replace(year=now.year)
            if now <= this_year <= cutoff:
                days_until = (this_year - now).days
                upcoming.append({
                    "name": date.name,
                    "date": this_year.strftime("%d.%m.%Y"),
                    "days_until": days_until,
                    "description": date.description
                })
            # Также проверяем следующий год если дата уже прошла
            elif this_year < now:
                next_year = date.date.replace(year=now.year + 1)
                if now <= next_year <= cutoff:
                    days_until = (next_year - now).days
                    upcoming.append({
                        "name": date.name,
                        "date": next_year.strftime("%d.%m.%Y"),
                        "days_until": days_until,
                        "description": date.description
                    })
        
        return sorted(upcoming, key=lambda x: x["days_until"])
    
    def add_preference(self, category: str, preference: str, evidence: str):
        """Добавить преференцию."""
        # Проверяем существует ли уже
        for pref in self.preferences:
            if pref.category == category:
                pref.preference = preference
                pref.evidence.append(evidence)
                return
        
        self.preferences.append(PersonalPreference(
            category=category,
            preference=preference,
            evidence=[evidence]
        ))
    
    def get_preference(self, category: str) -> Optional[str]:
        """Получить преференцию."""
        for pref in self.preferences:
            if pref.category == category:
                return pref.preference
        return None
    
    def record_mood(self, state: EmotionalState):
        """Записать настроение."""
        self.mood_history.append(state)
        
        # Ограничиваем историю (последние 100)
        if len(self.mood_history) > 100:
            self.mood_history = self.mood_history[-100:]
    
    def get_mood_trend(self, hours: int = 24) -> str:
        """Получить тренд настроения за период."""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [m for m in self.mood_history if m.timestamp >= cutoff]
        
        if not recent:
            return "unknown"
        
        moods = [m.mood for m in recent]
        
        # Считаем доминирующее настроение
        mood_counts: Dict[Mood, int] = {}
        for m in moods:
            mood_counts[m] = mood_counts.get(m, 0) + 1
        
        dominant = max(mood_counts, key=mood_counts.get)
        
        # Проверяем тренд
        recent_5 = recent[-5:]
        if len(recent_5) >= 2:
            first_half = recent_5[:len(recent_5)//2]
            second_half = recent_5[len(recent_5)//2:]
            
            first_moods = [m.mood for m in first_half]
            second_moods = [m.mood for m in second_half]
            
            # Простой тренд
            if second_moods[-1] in [Mood.HAPPY, Mood.VERY_HAPPY, Mood.EXCITED]:
                return "improving"
            elif second_moods[-1] in [Mood.SAD, Mood.ANGRY, Mood.ANXIOUS, Mood.FRUSTRATED]:
                return "declining"
        
        return dominant.value
    
    def get_supportive_message(self, mood: Mood) -> str:
        """Получить поддерживающее сообщение для настроения."""
        messages = {
            Mood.SAD: [
                "Эй, я тут. Может поговорим?",
                "Понимаю что сейчас непросто. Я рядом.",
                "Хочешь отвлечься или выговориться — я здесь."
            ],
            Mood.ANXIOUS: [
                "Дыши. Всё будет хорошо.",
                "Давай разберёмся вместе, один шаг за раз.",
                "Я верю в тебя. Ты справишься."
            ],
            Mood.ANGRY: [
                "Я тебя слышу. Расскажи что случилось.",
                "Это нормально — злиться. Я не осуждаю.",
                "Может попробуем посмотреть на это иначе?"
            ],
            Mood.TIRED: [
                "Может пора отдохнуть?",
                "Ты много работал. Это нормально — сделать перерыв.",
                "Хочешь просто помолчать? Я никуда не спешу."
            ],
            Mood.FRUSTRATED: [
                "Застрял — это не тупик, это точка роста.",
                "Давай разобьём на маленькие шаги?",
                "Ты справлялся с трудностями и раньше."
            ]
        }
        
        import random
        return random.choice(messages.get(mood, ["Я тут."]))
    
    def get_celebration_message(self, mood: Mood) -> str:
        """Получить праздничное сообщение для хорошего настроения."""
        messages = {
            Mood.VERY_HAPPY: [
                "Обожаю когда ты так сияешь! 💫",
                "Ты сегодня на позитиве — это заряжает!",
                "Рада что всё так круто!"
            ],
            Mood.EXCITED: [
                "Вижу твой энтузиазм! 🔥 Расскажи подробнее!",
                "Ты загорелся — это круто! Что дальше?",
                "Твоя энергия заражает!"
            ],
            Mood.HAPPY: [
                "Приятно видеть тебя в хорошем настроении 😊",
                "Хорошо когда всё хорошо!",
                "Что хорошего случилось?"
            ]
        }
        
        import random
        return random.choice(messages.get(mood, ["😊"]))


class EmotionalIntelligence:
    """
    Главный класс эмоционального интеллекта.
    
    Использование:
        ei = EmotionalIntelligence()
        
        # Определить настроение
        state = ei.detect_mood("Я так счастлив сегодня!")
        
        # Адаптировать ответ
        response = ei.adapt_response("Привет!", state)
        
        # Записать настроение
        ei.record_mood("Всё отлично!")
    """
    
    def __init__(self):
        self.mood_detector = MoodDetector()
        self.personal = PersonalConnection()
    
    def detect_mood(self, text: str) -> EmotionalState:
        """Определить настроение по тексту."""
        return self.mood_detector.detect(text)
    
    def record_mood(self, text: str):
        """Определить и записать настроение."""
        state = self.detect_mood(text)
        self.personal.record_mood(state)
        return state
    
    def adapt_response(
        self,
        base_response: str,
        emotional_state: Optional[EmotionalState] = None
    ) -> str:
        """
        Адаптировать ответ под настроение.
        
        Args:
            base_response: Базовый ответ Евы
            emotional_state: Эмоциональное состояние (если None — определить автоматически)
            
        Returns:
            Адаптированный ответ
        """
        if emotional_state is None or emotional_state.mood == Mood.NEUTRAL:
            return base_response
        
        mood = emotional_state.mood
        style = self.mood_detector.get_response_style(mood)
        
        # Добавляем эмодзи если нужно
        if "emoji" in style:
            emoji = style["emoji"]
            if emoji not in base_response:
                base_response = f"{emoji} {base_response}"
        
        return base_response
    
    def get_upcoming_events(self) -> List[Dict[str, Any]]:
        """Получить предстоящие важные события."""
        return self.personal.get_upcoming_dates()
    
    def check_important_date_today(self) -> Optional[str]:
        """Проверить есть ли важная дата сегодня."""
        today = datetime.now().strftime("%d.%m")
        
        for date in self.personal.important_dates:
            date_str = date.date.strftime("%d.%m")
            if date_str == today:
                return f"🎉 Сегодня {date.name}! {date.description}"
        
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Статистика."""
        return {
            "important_dates": len(self.personal.important_dates),
            "preferences": len(self.personal.preferences),
            "mood_records": len(self.personal.mood_history),
            "mood_trend": self.personal.get_mood_trend(),
            "upcoming_events": self.get_upcoming_events()
        }


# =============================================================================
# Global instance
# =============================================================================

_ei: Optional[EmotionalIntelligence] = None


def get_emotional_intelligence() -> EmotionalIntelligence:
    """Get or create global emotional intelligence instance."""
    global _ei
    if _ei is None:
        _ei = EmotionalIntelligence()
    return _ei


# Тест
if __name__ == "__main__":
    print("=== Emotional Intelligence Test ===\n")
    
    ei = get_emotional_intelligence()
    
    # Тест определения настроения
    test_texts = [
        "Я так счастлив сегодня! Всё идёт отлично!",
        "Грустно как-то... Не знаю что делать",
        "Бесит этот баг уже третий день!",
        "Устал как собака, хочу спать",
        "Вау! Это невероятно!"
    ]
    
    print("🎭 Mood Detection:")
    for text in test_texts:
        state = ei.detect_mood(text)
        print(f"  '{text[:30]}...' → {state.mood.value} ({state.confidence:.0%})")
    
    print()
    
    # Важные даты
    print("📅 Upcoming Important Dates:")
    events = ei.get_upcoming_events()
    if events:
        for event in events[:3]:
            print(f"  {event['name']}: через {event['days_until']} дней ({event['date']})")
    else:
        print("  Нет важных дат в ближайшие 30 дней")
    
    print()
    
    # Статистика
    print("📊 Stats:")
    stats = ei.get_stats()
    print(f"  Mood records: {stats['mood_records']}")
    print(f"  Mood trend: {stats['mood_trend']}")
    
    print("\n✅ Emotional Intelligence ready")