"""
Eva's Calendar Integration

Управление событиями, встречами и расписанием.
Гриша не пропустит ни одну важную встречу!

Поддержка:
- Google Calendar
- ICS календари (файловый формат)
- Локальное хранение событий
- Напоминания и уведомления

.env:
GOOGLE_CALENDAR_ID=primary
GOOGLE_SERVICE_ACCOUNT_JSON=path/to/service-account.json
"""

import os
import json
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from enum import Enum
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


class EventStatus(Enum):
    """Статус события."""
    CONFIRMED = "confirmed"
    TENTATIVE = "tentative"
    CANCELLED = "cancelled"


class EventPriority(Enum):
    """Приоритет события."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    URGENT = 3


@dataclass
class CalendarEvent:
    """Событие календаря."""
    id: str = ""
    title: str = ""
    description: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    end_time: datetime = field(default_factory=lambda: datetime.now() + timedelta(hours=1))
    all_day: bool = False
    location: str = ""
    status: EventStatus = EventStatus.CONFIRMED
    priority: EventPriority = EventPriority.NORMAL
    reminders: List[int] = field(default_factory=list)  # минуты до события
    attendees: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def is_upcoming(self, hours: int = 24) -> bool:
        """Проверить, скоро ли событие."""
        now = datetime.now()
        return now <= self.start_time <= now + timedelta(hours=hours)
    
    def is_today(self) -> bool:
        """Проверить, сегодня ли событие."""
        return self.start_time.date() == date.today()
    
    def minutes_until(self) -> int:
        """Минут до начала события."""
        delta = self.start_time - datetime.now()
        return int(delta.total_seconds() / 60)
    
    def format_short(self) -> str:
        """Краткий формат для отображения."""
        time_str = self.start_time.strftime("%H:%M") if not self.all_day else "🌅"
        priority_emoji = {
            EventPriority.LOW: "⬇️",
            EventPriority.NORMAL: "➡️",
            EventPriority.HIGH: "⬆️",
            EventPriority.URGENT: "🚨"
        }
        
        return f"{priority_emoji[self.priority]} {time_str} {self.title}"
    
    def format_full(self) -> str:
        """Полный формат."""
        time_str = self.start_time.strftime("%H:%M")
        end_str = self.end_time.strftime("%H:%M")
        duration_min = int((self.end_time - self.start_time).total_seconds() / 60)
        
        lines = [
            f"📅 *{self.title}*",
            f"   🕐 {time_str} — {end_str} ({duration_min} мин)",
        ]
        
        if self.location:
            lines.append(f"   📍 {self.location}")
        
        if self.attendees:
            lines.append(f"   👥 {', '.join(self.attendees[:3])}")
        
        if self.reminders:
            reminder_str = ", ".join(f"{r}min" for r in self.reminders)
            lines.append(f"   🔔 Reminders: {reminder_str}")
        
        return "\n".join(lines)


class LocalCalendar:
    """
    Локальный календарь с файловым хранением.
    
    Простой способ хранить события без внешних сервисов.
    """
    
    def __init__(self, storage_path: str = "./data/calendar.json"):
        self.storage_path = storage_path
        self.events: List[CalendarEvent] = []
        self._load()
    
    def _load(self):
        """Загрузить события из файла."""
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            self.events = []
            for item in data.get("events", []):
                self.events.append(CalendarEvent(
                    id=item["id"],
                    title=item["title"],
                    description=item.get("description", ""),
                    start_time=datetime.fromisoformat(item["start_time"]),
                    end_time=datetime.fromisoformat(item["end_time"]),
                    all_day=item.get("all_day", False),
                    location=item.get("location", ""),
                    status=EventStatus(item.get("status", "confirmed")),
                    priority=EventPriority(item.get("priority", 1)),
                    reminders=item.get("reminders", []),
                    attendees=item.get("attendees", [])
                ))
        except Exception as e:
            print(f"Calendar load error: {e}")
    
    def _save(self):
        """Сохранить события в файл."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        data = {
            "events": [
                {
                    "id": e.id,
                    "title": e.title,
                    "description": e.description,
                    "start_time": e.start_time.isoformat(),
                    "end_time": e.end_time.isoformat(),
                    "all_day": e.all_day,
                    "location": e.location,
                    "status": e.status.value,
                    "priority": e.priority.value,
                    "reminders": e.reminders,
                    "attendees": e.attendees
                }
                for e in self.events
            ],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_event(
        self,
        title: str,
        start_time: datetime,
        end_time: Optional[datetime] = None,
        description: str = "",
        location: str = "",
        priority: EventPriority = EventPriority.NORMAL,
        reminders: List[int] = None,
        all_day: bool = False
    ) -> CalendarEvent:
        """
        Добавить событие.
        
        Args:
            title: Название
            start_time: Начало
            end_time: Конец (по умолчанию +1 час)
            description: Описание
            location: Место
            priority: Приоритет
            reminders: Минуты до напоминания
            all_day: Целый день
            
        Returns:
            Созданное событие
        """
        import uuid
        
        if end_time is None:
            end_time = start_time + timedelta(hours=1)
        
        event = CalendarEvent(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            start_time=start_time,
            end_time=end_time,
            all_day=all_day,
            location=location,
            priority=priority,
            reminders=reminders or [15, 60]  # 15 мин и 1 час
        )
        
        self.events.append(event)
        self._save()
        
        return event
    
    def remove_event(self, event_id: str) -> bool:
        """Удалить событие."""
        before = len(self.events)
        self.events = [e for e in self.events if e.id != event_id]
        
        if len(self.events) < before:
            self._save()
            return True
        return False
    
    def update_event(self, event_id: str, **kwargs) -> Optional[CalendarEvent]:
        """Обновить событие."""
        for event in self.events:
            if event.id == event_id:
                for key, value in kwargs.items():
                    if hasattr(event, key):
                        setattr(event, key, value)
                
                event.updated_at = datetime.now()
                self._save()
                return event
        
        return None
    
    def get_today(self) -> List[CalendarEvent]:
        """Получить события на сегодня."""
        today = date.today()
        return [
            e for e in self.events
            if e.start_time.date() == today and e.status != EventStatus.CANCELLED
        ]
    
    def get_upcoming(self, days: int = 7) -> List[CalendarEvent]:
        """Получить предстоящие события."""
        now = datetime.now()
        cutoff = now + timedelta(days=days)
        
        return sorted([
            e for e in self.events
            if now <= e.start_time <= cutoff and e.status != EventStatus.CANCELLED
        ], key=lambda e: e.start_time)
    
    def get_due_reminders(self) -> List[CalendarEvent]:
        """Получить события с активными напоминаниями."""
        now = datetime.now()
        due = []
        
        for event in self.events:
            if event.status == EventStatus.CANCELLED:
                continue
            
            for reminder_minutes in event.reminders:
                event_time = event.start_time - timedelta(minutes=reminder_minutes)
                
                # Событие в течение 1 минуты
                if abs((now - event_time).total_seconds()) < 60:
                    due.append(event)
                    break
        
        return due
    
    def get_summary(self) -> str:
        """Получить сводку календаря."""
        today = self.get_today()
        upcoming = self.get_upcoming(7)
        
        lines = ["📅 *Календарь*", ""]
        
        if today:
            lines.append(f"📆 Сегодня ({len(today)}):")
            for event in today:
                lines.append(f"   {event.format_short()}")
            lines.append("")
        else:
            lines.append("📆 Сегодня: нет событий")
        
        if upcoming:
            # Пропускаем сегодняшние
            future = [e for e in upcoming if not e.is_today()][:5]
            if future:
                lines.append(f"\n📅 Скоро ({len(future)}):")
                for event in future:
                    day_str = event.start_time.strftime("%a %d")
                    time_str = event.start_time.strftime("%H:%M")
                    lines.append(f"   {day_str} {time_str} {event.title}")
        
        return "\n".join(lines)


class GoogleCalendarClient:
    """
    Google Calendar API клиент.
    
    Использование требует service account.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, calendar_id: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
        self.calendar_id = calendar_id or os.getenv("GOOGLE_CALENDAR_ID", "primary")
        self._service = None
    
    def _get_service(self):
        """Получить Google Calendar service."""
        if self._service is not None:
            return self._service
        
        if not self.credentials_path or not os.path.exists(self.credentials_path):
            return None
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=["https://www.googleapis.com/auth/calendar.read"]
            )
            
            self._service = build("calendar", "v3", credentials=credentials)
            return self._service
        
        except ImportError:
            print("Install google-api-python-client: pip install google-api-python-client")
            return None
        except Exception as e:
            print(f"Google Calendar auth error: {e}")
            return None
    
    def get_events(
        self,
        time_min: Optional[datetime] = None,
        time_max: Optional[datetime] = None,
        max_results: int = 100
    ) -> List[CalendarEvent]:
        """Получить события из Google Calendar."""
        service = self._get_service()
        if not service:
            return []
        
        if time_min is None:
            time_min = datetime.now()
        if time_max is None:
            time_max = time_min + timedelta(days=30)
        
        try:
            events_result = service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min.isoformat() + "Z",
                timeMax=time_max.isoformat() + "Z",
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            events = []
            for item in events_result.get("items", []):
                start = item["start"].get("dateTime", item["start"].get("date"))
                end = item["end"].get("dateTime", item["end"].get("date"))
                
                # Парсим дату
                try:
                    if "T" in start:
                        start_dt = datetime.fromisoformat(start.replace("Z", "+00:00"))
                        end_dt = datetime.fromisoformat(end.replace("Z", "+00:00"))
                        all_day = False
                    else:
                        start_dt = datetime.fromisoformat(start)
                        end_dt = datetime.fromisoformat(end)
                        all_day = True
                except:
                    continue
                
                events.append(CalendarEvent(
                    id=item["id"],
                    title=item.get("summary", "No title"),
                    description=item.get("description", ""),
                    start_time=start_dt,
                    end_time=end_dt,
                    all_day=all_day,
                    location=item.get("location", ""),
                    status=EventStatus.CONFIRMED if item.get("status") != "cancelled" else EventStatus.CANCELLED
                ))
            
            return events
        
        except Exception as e:
            print(f"Google Calendar error: {e}")
            return []


# =============================================================================
# Event Reminder System
# =============================================================================

class ReminderScheduler:
    """
    Планировщик напоминаний.
    
    Интегрируется с NotificationManager для отправки уведомлений.
    """
    
    def __init__(self, calendar: LocalCalendar):
        self.calendar = calendar
        self.last_reminded: Dict[str, datetime] = {}
    
    def check_and_notify(
        self,
        notify_callback: Callable[[CalendarEvent], None]
    ) -> List[CalendarEvent]:
        """
        Проверить и отправить напоминания.
        
        Args:
            notify_callback: Функция для отправки уведомления
            
        Returns:
            Список событий для которых отправлены напоминания
        """
        notified = []
        now = datetime.now()
        
        for event in self.calendar.get_due_reminders():
            # Не напоминать дважды
            last = self.last_reminded.get(event.id)
            if last and (now - last).total_seconds() < 60:
                continue
            
            notify_callback(event)
            self.last_reminded[event.id] = now
            notified.append(event)
        
        return notified


# =============================================================================
# Singleton accessor
# =============================================================================

_local_calendar: Optional[LocalCalendar] = None
_google_calendar: Optional[GoogleCalendarClient] = None


def get_local_calendar() -> LocalCalendar:
    """Get or create local calendar."""
    global _local_calendar
    if _local_calendar is None:
        _local_calendar = LocalCalendar()
    return _local_calendar


def get_google_calendar() -> GoogleCalendarClient:
    """Get or create Google Calendar client."""
    global _google_calendar
    if _google_calendar is None:
        _google_calendar = GoogleCalendarClient()
    return _google_calendar


# =============================================================================
# Пример использования
# =============================================================================

if __name__ == "__main__":
    print("=== Calendar Integration ===\n")
    
    calendar = get_local_calendar()
    
    # Добавить событие
    meeting = calendar.add_event(
        title="Встреча с Полиной",
        start_time=datetime.now() + timedelta(hours=2),
        description="Обсудить проект",
        location="Офис",
        priority=EventPriority.HIGH
    )
    
    print(f"✅ Created event: {meeting.title}")
    print(meeting.format_full())
    
    # Получить сводку
    print("\n" + calendar.get_summary())


# =============================================================================
# TODO: Добавить ICS импорт/экспорт
# =============================================================================
# - Импорт .ics файлов
# - Экспорт событий в ICS
# - Синхронизация с iCal
# =============================================================================