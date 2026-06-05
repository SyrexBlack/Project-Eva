"""
Eva's Proactive AI Module

Ева действует сама, не ждёт команд.
- Interest Engine: мониторит новости и интересы
- Task Automation: напоминания и планирование
- Proactive Schedule: утренняя/вечерняя рутина

Как это работает:
1. Периодически проверяет интересы Гриши
2. Ищет релевантную информацию
3. Делится когда что-то интересное
4. Напоминает о делах и встречах
"""

import os
import time
import threading
from typing import Optional, List, Callable, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class ProactiveType(Enum):
    """Типы проактивных действий."""
    NEWS_CHECK = "news_check"
    REMINDER = "reminder"
    CHECK_IN = "check_in"
    PROJECT_UPDATE = "project_update"
    LEARNING = "learning"
    SCHEDULE = "schedule"


@dataclass
class ProactiveAction:
    """Проактивное действие."""
    action_type: ProactiveType
    content: str
    timestamp: datetime
    priority: float  # 0.0 - 1.0
    delivered: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Interest:
    """Интерес Гриши для мониторинга."""
    topic: str
    keywords: List[str]
    last_check: Optional[datetime] = None
    last_found: Optional[datetime] = None
    alert_threshold: float = 0.5  # Минимум важности для алерта


class InterestEngine:
    """
    Мониторит интересы и ищет релевантную информацию.
    
    Гриша интересуется:
    - AI/LLM новости
    - Криптовалюта (BTC, ETH, SOL, DOGE)
    - League of Legends / Wild Rift
    - Технологии
    """
    
    def __init__(self):
        self.interests: List[Interest] = []
        self._init_default_interests()
    
    def _init_default_interests(self):
        """Инициализировать дефолтные интересы."""
        self.interests = [
            Interest(
                topic="AI/LLM News",
                keywords=["AI", "LLM", "Claude", "GPT", "artificial intelligence", "machine learning"],
                alert_threshold=0.6
            ),
            Interest(
                topic="Crypto",
                keywords=["Bitcoin", "Ethereum", "SOL", "DOGE", "cryptocurrency", "blockchain"],
                alert_threshold=0.5
            ),
            Interest(
                topic="Gaming/League of Legends",
                keywords=["League of Legends", "Wild Rift", "LoL", "Riot Games", "patch notes"],
                alert_threshold=0.4
            ),
            Interest(
                topic="Tech",
                keywords=["Python", "Linux", "Docker", "open source", "programming"],
                alert_threshold=0.5
            ),
        ]
    
    def add_interest(self, topic: str, keywords: List[str], alert_threshold: float = 0.5):
        """Добавить интерес."""
        self.interests.append(Interest(
            topic=topic,
            keywords=keywords,
            alert_threshold=alert_threshold
        ))
    
    def remove_interest(self, topic: str):
        """Удалить интерес."""
        self.interests = [i for i in self.interests if i.topic != topic]
    
    def get_keywords_for_topic(self, topic: str) -> List[str]:
        """Получить ключевые слова для топика."""
        for interest in self.interests:
            if interest.topic == topic:
                return interest.keywords
        return []
    
    def get_all_keywords(self) -> List[str]:
        """Получить все ключевые слова."""
        keywords = []
        for interest in self.interests:
            keywords.extend(interest.keywords)
        return keywords


class TaskAutomation:
    """
    Автоматизация задач: напоминания, планирование.
    
    Использование:
        tasks = TaskAutomation()
        tasks.add_reminder("Позвонить Полине", datetime.now() + timedelta(hours=2))
        tasks.add_recurring("Утренняя сводка", "0 8 * * *")
    """
    
    def __init__(self):
        self.reminders: List[Dict[str, Any]] = []
        self.recurring: List[Dict[str, Any]] = []
    
    def add_reminder(
        self,
        text: str,
        due_time: datetime,
        priority: float = 0.5,
        repeat: bool = False
    ) -> str:
        """
        Добавить напоминание.
        
        Args:
            text: Текст напоминания
            due_time: Когда напомнить
            priority: Приоритет (0.0 - 1.0)
            repeat: Повторять ли
            
        Returns:
            ID напоминания
        """
        import uuid
        
        reminder_id = str(uuid.uuid4())[:8]
        
        self.reminders.append({
            "id": reminder_id,
            "text": text,
            "due_time": due_time,
            "priority": priority,
            "repeat": repeat,
            "created_at": datetime.now()
        })
        
        return reminder_id
    
    def add_recurring(
        self,
        name: str,
        schedule: str,  # cron format
        task_type: str = "check_in"
    ) -> str:
        """
        Добавить повторяющуюся задачу.
        
        Args:
            name: Название задачи
            schedule: Cron schedule (e.g. "0 8 * * *")
            task_type: Тип задачи
            
        Returns:
            ID задачи
        """
        import uuid
        
        task_id = str(uuid.uuid4())[:8]
        
        self.recurring.append({
            "id": task_id,
            "name": name,
            "schedule": schedule,
            "task_type": task_type,
            "last_run": None,
            "next_run": self._parse_schedule(schedule)
        })
        
        return task_id
    
    def _parse_schedule(self, schedule: str) -> Optional[datetime]:
        """Парсить cron schedule в datetime."""
        # Простой парсинг для базовых форматов
        # TODO: Использовать croniter для полного парсинга
        parts = schedule.split()
        
        if len(parts) < 5:
            return None
        
        now = datetime.now()
        
        # Простой расчёт следующего запуска
        try:
            minute = int(parts[0])
            hour = int(parts[1])
            
            next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            if next_run <= now:
                next_run += timedelta(days=1)
            
            return next_run
        except (ValueError, IndexError):
            return None
    
    def get_due_reminders(self) -> List[Dict[str, Any]]:
        """Получить напоминания которые пора показать."""
        now = datetime.now()
        due = []
        
        for reminder in self.reminders:
            if reminder["due_time"] <= now:
                due.append(reminder)
        
        return due
    
    def dismiss_reminder(self, reminder_id: str):
        """Удалить напоминание."""
        self.reminders = [r for r in self.reminders if r["id"] != reminder_id]
    
    def get_upcoming(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Получить предстоящие напоминания."""
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        upcoming = [
            r for r in self.reminders
            if now <= r["due_time"] <= cutoff
        ]
        
        return sorted(upcoming, key=lambda r: r["due_time"])


class ProactiveScheduler:
    """
    Планировщик проактивных действий.
    
    Утренняя сводка, вечерний wrap-up, адаптивная частота.
    """
    
    def __init__(
        self,
        check_interval: int = 300,  # 5 минут
        quiet_hours_start: int = 22,
        quiet_hours_end: int = 8
    ):
        """
        Args:
            check_interval: Интервал проверки (сек)
            quiet_hours_start: Начало тихих часов (час)
            quiet_hours_end: Конец тихих часов (час)
        """
        self.check_interval = check_interval
        self.quiet_hours_start = quiet_hours_start
        self.quiet_hours_end = quiet_hours_end
        
        self.interest_engine = InterestEngine()
        self.task_automation = TaskAutomation()
        
        self.is_running = False
        self._thread: Optional[threading.Thread] = None
        self._callbacks: List[Callable[[ProactiveAction], None]] = []
    
    def add_callback(self, callback: Callable[[ProactiveAction], None]):
        """Добавить callback для проактивных действий."""
        self._callbacks.append(callback)
    
    def _should_notify(self) -> bool:
        """Проверить можно ли отправлять уведомления."""
        hour = datetime.now().hour
        
        # Тихие часы (22:00 - 8:00)
        if self.quiet_hours_start > self.quiet_hours_end:
            # Ночной режим (22:00 - 08:00)
            return hour < self.quiet_hours_end or hour >= self.quiet_hours_start
        else:
            # Дневной режим
            return not (self.quiet_hours_start <= hour < self.quiet_hours_end)
    
    def _generate_morning_check_in(self) -> Optional[ProactiveAction]:
        """Генерация утреннего приветствия."""
        hour = datetime.now().hour
        
        if 7 <= hour <= 10:
            return ProactiveAction(
                action_type=ProactiveType.CHECK_IN,
                content="Доброе утро, Гриша! ☀️ Как планы на сегодня?",
                timestamp=datetime.now(),
                priority=0.7
            )
        
        return None
    
    def _generate_evening_wrap_up(self) -> Optional[ProactiveAction]:
        """Генерация вечернего wrap-up."""
        hour = datetime.now().hour
        
        if 20 <= hour <= 22:
            return ProactiveAction(
                action_type=ProactiveType.SCHEDULE,
                content="Добрый вечер! Как прошёл день? Есть что-то важное на завтра? 🌙",
                timestamp=datetime.now(),
                priority=0.6
            )
        
        return None
    
    def _check_reminders(self) -> List[ProactiveAction]:
        """Проверить напоминания."""
        actions = []
        
        for reminder in self.task_automation.get_due_reminders():
            actions.append(ProactiveAction(
                action_type=ProactiveType.REMINDER,
                content=f"📌 Напоминание: {reminder['text']}",
                timestamp=datetime.now(),
                priority=reminder["priority"],
                metadata={"reminder_id": reminder["id"]}
            ))
            
            # Удаляем если не повторяющееся
            if not reminder["repeat"]:
                self.task_automation.dismiss_reminder(reminder["id"])
        
        return actions
    
    def _generate_proactive_content(self) -> Optional[ProactiveAction]:
        """Генерация проактивного контента (новости, обновления)."""
        # TODO: Интеграция с web search
        # Пока заглушка — возвращает None
        
        return None
    
    def check(self) -> List[ProactiveAction]:
        """Проверить всё и вернуть действия."""
        if not self._should_notify():
            return []
        
        actions = []
        
        # Утреннее приветствие
        morning = self._generate_morning_check_in()
        if morning:
            actions.append(morning)
        
        # Вечерний wrap-up
        evening = self._generate_evening_wrap_up()
        if evening:
            actions.append(evening)
        
        # Напоминания
        reminders = self._check_reminders()
        actions.extend(reminders)
        
        # Проактивный контент
        proactive = self._generate_proactive_content()
        if proactive:
            actions.append(proactive)
        
        return actions
    
    def start(self):
        """Запустить проактивный мониторинг."""
        if self.is_running:
            return
        
        self.is_running = True
        
        def loop():
            while self.is_running:
                actions = self.check()
                
                for action in actions:
                    for callback in self._callbacks:
                        try:
                            callback(action)
                        except Exception as e:
                            print(f"Callback error: {e}")
                
                time.sleep(self.check_interval)
        
        self._thread = threading.Thread(target=loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Остановить мониторинг."""
        self.is_running = False


# =============================================================================
# Eva Proactive Integration
# =============================================================================

class EvaProactive:
    """
    Проактивная система для Евы.
    
    Использование:
        proactive = EvaProactive()
        
        def on_action(action):
            print(f"Ева: {action.content}")
        
        proactive.add_callback(on_action)
        proactive.start()
    """
    
    def __init__(self, check_interval: int = 300):
        self.scheduler = ProactiveScheduler(check_interval=check_interval)
        self.action_history: List[ProactiveAction] = []
    
    def add_callback(self, callback: Callable[[ProactiveAction], None]):
        """Добавить callback."""
        self.scheduler.add_callback(callback)
    
    def add_reminder(self, text: str, due_time: datetime, priority: float = 0.5):
        """Добавить напоминание."""
        return self.scheduler.task_automation.add_reminder(text, due_time, priority)
    
    def add_interest(self, topic: str, keywords: List[str]):
        """Добавить интерес для мониторинга."""
        self.scheduler.interest_engine.add_interest(topic, keywords)
    
    def start(self):
        """Запустить проактивную систему."""
        self.scheduler.start()
    
    def stop(self):
        """Остановить."""
        self.scheduler.stop()
    
    def get_stats(self) -> dict:
        """Статистика."""
        return {
            "is_running": self.scheduler.is_running,
            "interests": len(self.scheduler.interest_engine.interests),
            "reminders": len(self.scheduler.task_automation.reminders),
            "recurring": len(self.scheduler.task_automation.recurring),
            "actions_today": len([
                a for a in self.action_history
                if a.timestamp.date() == datetime.now().date()
            ])
        }


# =============================================================================
# Global instance
# =============================================================================

_proactive: Optional[EvaProactive] = None


def get_proactive(check_interval: int = 300) -> EvaProactive:
    """Get or create global proactive instance."""
    global _proactive
    if _proactive is None:
        _proactive = EvaProactive(check_interval=check_interval)
    return _proactive


# Тест
if __name__ == "__main__":
    print("=== Proactive AI Test ===\n")
    
    proactive = EvaProactive()
    
    # Добавляем напоминание
    reminder_id = proactive.add_reminder(
        "Позвонить Полине",
        datetime.now() + timedelta(minutes=1),
        priority=0.8
    )
    print(f"✅ Added reminder: {reminder_id}")
    
    # Добавляем интерес
    proactive.add_interest("Python", ["async", "asyncio", "concurrency"])
    print("✅ Added interest: Python")
    
    print(f"\n📊 Stats: {proactive.get_stats()}")
    print()
    
    # Проверяем действия
    print("Checking for actions...")
    actions = proactive.scheduler.check()
    
    if actions:
        for action in actions:
            print(f"  🎯 {action.content}")
    else:
        print("  No actions at this time")
    
    print("\n📝 Usage:")
    print("  proactive = EvaProactive()")
    print("  proactive.add_callback(lambda a: print(a.content))")
    print("  proactive.start()  # Runs in background")