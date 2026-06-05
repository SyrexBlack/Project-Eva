"""
Eva's Task Automation

Reminders, scheduling, and task management.
Eva helps Grisha stay organized and never misses important things.

Features:
- Task creation and tracking
- Reminders with snooze
- Meeting detection from conversation
- Smart scheduling suggestions

Usage:
    tasks = TaskAutomation()
    tasks.add_reminder("Позвонить Полине", priority=high, time=datetime.now())
    tasks.add_reminder("Закончить Project-Eva", priority=medium)
    
    due = tasks.get_due_tasks()
    if due:
        eva.remind(due)
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
import uuid


class TaskPriority(Enum):
    """Task priority levels."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    DUE = "due"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    SNOOZED = "snoozed"


@dataclass
class Task:
    """A task or reminder."""
    id: str
    title: str
    description: Optional[str] = None
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    
    # Timing
    created_at: datetime = field(default_factory=datetime.now)
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    snoozed_until: Optional[datetime] = None
    
    # Context
    category: str = "general"
    source: str = "manual"  # manual, detected, proactive
    related_entities: List[str] = field(default_factory=list)
    
    # Reminders
    reminder_sent: bool = False
    reminder_count: int = 0
    
    def is_due(self) -> bool:
        """Check if task is due now."""
        if self.status != TaskStatus.PENDING:
            return False
        if self.due_at is None:
            return False
        return datetime.now() >= self.due_at
    
    def snooze(self, minutes: int = 30):
        """Snooze this task."""
        self.snoozed_until = datetime.now() + timedelta(minutes=minutes)
        self.status = TaskStatus.SNOOZED
    
    def complete(self):
        """Mark task as completed."""
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.now()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "due_at": self.due_at.isoformat() if self.due_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "snoozed_until": self.snoozed_until.isoformat() if self.snoozed_until else None,
            "category": self.category,
            "source": self.source,
            "related_entities": self.related_entities,
            "reminder_sent": self.reminder_sent,
            "reminder_count": self.reminder_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        """Create task from dictionary."""
        return cls(
            id=data["id"],
            title=data["title"],
            description=data.get("description"),
            priority=TaskPriority(data.get("priority", 2)),
            status=TaskStatus(data.get("status", "pending")),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            due_at=datetime.fromisoformat(data["due_at"]) if data.get("due_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            snoozed_until=datetime.fromisoformat(data["snoozed_until"]) if data.get("snoozed_until") else None,
            category=data.get("category", "general"),
            source=data.get("source", "manual"),
            related_entities=data.get("related_entities", []),
            reminder_sent=data.get("reminder_sent", False),
            reminder_count=data.get("reminder_count", 0)
        )


class TaskAutomation:
    """
    Eva's task and reminder management.
    
    Manages tasks, reminders, and scheduling.
    Automatically detects tasks from conversation.
    """
    
    def __init__(self, storage_path: str = "./data/tasks.json"):
        """
        Initialize Task Automation.
        
        Args:
            storage_path: Where to store tasks
        """
        self.storage_path = storage_path
        self.tasks: Dict[str, Task] = {}
        
        # Load existing tasks
        self._load_tasks()
    
    def _load_tasks(self):
        """Load tasks from storage."""
        if not os.path.exists(self.storage_path):
            return
        
        try:
            with open(self.storage_path, "r") as f:
                data = json.load(f)
            
            for task_data in data.get("tasks", []):
                task = Task.from_dict(task_data)
                self.tasks[task.id] = task
        except Exception as e:
            print(f"Failed to load tasks: {e}")
    
    def _save_tasks(self):
        """Save tasks to storage."""
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        
        data = {
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "updated_at": datetime.now().isoformat()
        }
        
        with open(self.storage_path, "w") as f:
            json.dump(data, f, indent=2)
    
    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: TaskPriority = TaskPriority.MEDIUM,
        due_at: Optional[datetime] = None,
        category: str = "general",
        source: str = "manual"
    ) -> Task:
        """
        Add a new task.
        
        Returns:
            The created task
        """
        task = Task(
            id=str(uuid.uuid4())[:8],
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
            category=category,
            source=source
        )
        
        self.tasks[task.id] = task
        self._save_tasks()
        
        return task
    
    def add_reminder(
        self,
        title: str,
        minutes_from_now: int = 0,
        due_at: Optional[datetime] = None,
        priority: TaskPriority = TaskPriority.MEDIUM
    ) -> Task:
        """Add a reminder (convenience method)."""
        if due_at is None and minutes_from_now > 0:
            due_at = datetime.now() + timedelta(minutes=minutes_from_now)
        
        return self.add_task(
            title=title,
            priority=priority,
            due_at=due_at,
            category="reminder"
        )
    
    def detect_task_from_text(self, text: str) -> Optional[Task]:
        """
        Try to detect a task from text.
        
        Looks for patterns like:
        - "нужно сделать X"
        - "не забыть Y"
        - "надо позвонить Z"
        """
        import re
        
        # Simple pattern matching
        patterns = [
            (r"(?:нужно|надо|должен|должна)\s+(?:сделать|купить|заказать)\s+(.+)", "need_to_do"),
            (r"не\s+(?:забыть|забудь)\s+(.+)", "dont_forget"),
            (r"(?:надо|нужно)\s+(?:позвонить|написать)\s+(.+)", "call_someone"),
            (r"(?:созвон|встреч|митинг)\s+(?:в|завтра|через)\s+(.+)", "meeting"),
        ]
        
        for pattern, task_type in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                
                # Create task
                return self.add_task(
                    title=title,
                    category=task_type,
                    source="detected"
                )
        
        return None
    
    def get_due_tasks(self) -> List[Task]:
        """Get tasks that are due now."""
        due = []
        
        for task in self.tasks.values():
            if task.is_due():
                due.append(task)
            elif task.status == TaskStatus.SNOOZED:
                if task.snoozed_until and datetime.now() >= task.snoozed_until:
                    task.status = TaskStatus.PENDING
                    due.append(task)
        
        # Sort by priority
        due.sort(key=lambda t: t.priority.value, reverse=True)
        return due
    
    def get_pending_tasks(self, limit: int = 10) -> List[Task]:
        """Get pending tasks sorted by priority."""
        pending = [
            t for t in self.tasks.values()
            if t.status == TaskStatus.PENDING
        ]
        
        pending.sort(key=lambda t: (t.priority.value, t.due_at or datetime.max), reverse=True)
        return pending[:limit]
    
    def complete_task(self, task_id: str) -> bool:
        """Mark a task as completed."""
        if task_id in self.tasks:
            self.tasks[task_id].complete()
            self._save_tasks()
            return True
        return False
    
    def snooze_task(self, task_id: str, minutes: int = 30) -> bool:
        """Snooze a task."""
        if task_id in self.tasks:
            self.tasks[task_id].snooze(minutes)
            self._save_tasks()
            return True
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a task."""
        if task_id in self.tasks:
            self.tasks[task_id].status = TaskStatus.CANCELLED
            self._save_tasks()
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get task statistics."""
        pending = sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING)
        due = len(self.get_due_tasks())
        completed = sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED)
        
        return {
            "total_tasks": len(self.tasks),
            "pending": pending,
            "due_now": due,
            "completed": completed,
            "categories": list(set(t.category for t in self.tasks.values()))
        }
    
    def format_task_for_sharing(self, task: Task) -> str:
        """Format a task for sharing with Grisha."""
        priority_emoji = {
            TaskPriority.LOW: "📋",
            TaskPriority.MEDIUM: "📌",
            TaskPriority.HIGH: "🔴",
            TaskPriority.URGENT: "🚨"
        }
        
        emoji = priority_emoji.get(task.priority, "📌")
        
        if task.due_at:
            time_str = task.due_at.strftime("%H:%M")
            return f"{emoji} *{task.title}* — до {time_str}"
        
        return f"{emoji} *{task.title}*"
    
    def format_due_tasks(self) -> str:
        """Format all due tasks for a reminder message."""
        due = self.get_due_tasks()
        
        if not due:
            return None
        
        lines = ["📋 Напоминаю:"]
        for task in due:
            lines.append(self.format_task_for_sharing(task))
        
        return "\n".join(lines)


# =============================================================================
# Singleton accessor
# =============================================================================

_tasks_instance: Optional[TaskAutomation] = None


def get_task_automation() -> TaskAutomation:
    """Get or create the global Task Automation instance."""
    global _tasks_instance
    if _tasks_instance is None:
        _tasks_instance = TaskAutomation()
    return _tasks_instance