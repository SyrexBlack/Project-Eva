"""
Eva's Proactive Scheduler

Scheduled proactive behaviors:
- Morning check-in (9-11 AM)
- Evening wrap-up (8-10 PM)
- Interest updates (periodic)
- Task reminders (as due)

Eva acts autonomously, reaching out to Grisha when appropriate.

Usage:
    scheduler = ProactiveScheduler(eva)
    scheduler.start()
    
    # Or integrate with companion
    eva = Eva()
    eva.start_proactive_mode()  # Already has this!
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass

from eva.skills.interest_engine import get_interest_engine
from eva.skills.task_automation import get_task_automation


@dataclass
class ProactiveAction:
    """A proactive action Eva can take."""
    name: str
    trigger_time: Optional[datetime] = None  # For one-time
    interval_hours: Optional[float] = None   # For recurring
    enabled: bool = True
    
    # Callbacks
    condition_fn: Optional[Callable[[], bool]] = None
    action_fn: Optional[Callable[[], Optional[str]]] = None
    
    # State
    last_executed: Optional[datetime] = None
    execute_count: int = 0
    
    def should_execute(self) -> bool:
        """Check if this action should run now."""
        if not self.enabled:
            return False
        
        # Check condition
        if self.condition_fn and not self.condition_fn():
            return False
        
        # Time-based trigger
        if self.trigger_time:
            return datetime.now() >= self.trigger_time
        
        # Interval-based trigger
        if self.interval_hours and self.last_executed:
            hours_since = (datetime.now() - self.last_executed).total_seconds() / 3600
            return hours_since >= self.interval_hours
        
        return False
    
    def execute(self) -> Optional[str]:
        """Execute this action."""
        if self.action_fn:
            result = self.action_fn()
            self.last_executed = datetime.now()
            self.execute_count += 1
            return result
        return None


class ProactiveScheduler:
    """
    Eva's proactive behavior scheduler.
    
    Manages scheduled and conditional proactive actions.
    Runs in background, calling callbacks when actions trigger.
    
    Built-in actions:
    - Morning check-in (9:00 AM)
    - Evening wrap-up (8:00 PM)
    - Task reminders (when due)
    - Interest updates (every 4 hours)
    """
    
    # Time windows
    MORNING_START = 9   # 9 AM
    MORNING_END = 11    # 11 AM
    EVENING_START = 20  # 8 PM
    EVENING_END = 22    # 10 PM
    
    def __init__(
        self,
        callback: Optional[Callable[[str], None]] = None
    ):
        """
        Initialize Proactive Scheduler.
        
        Args:
            callback: Callback when Eva has something to share
        """
        self.on_message = callback
        
        self.actions: List[ProactiveAction] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Components
        self.interest_engine = get_interest_engine()
        self.task_automation = get_task_automation()
        
        # Initialize default actions
        self._init_default_actions()
    
    def _init_default_actions(self):
        """Set up default proactive actions."""
        # Morning check-in (once per day, between 9-11 AM)
        self.add_action(
            name="morning_checkin",
            interval_hours=24,
            condition_fn=self._is_morning_time,
            action_fn=self._do_morning_checkin
        )
        
        # Evening wrap-up (once per day, between 8-10 PM)
        self.add_action(
            name="evening_wrapup",
            interval_hours=24,
            condition_fn=self._is_evening_time,
            action_fn=self._do_evening_wrapup
        )
        
        # Task reminders (every 30 minutes during active hours)
        self.add_action(
            name="task_reminder",
            interval_hours=0.5,
            condition_fn=self._is_active_hours,
            action_fn=self._do_task_reminder
        )
        
        # Interest updates (every 4 hours during active hours)
        self.add_action(
            name="interest_update",
            interval_hours=4,
            condition_fn=self._is_active_hours,
            action_fn=self._do_interest_update
        )
    
    def _is_morning_time(self) -> bool:
        """Check if current time is in morning window."""
        hour = datetime.now().hour
        return self.MORNING_START <= hour <= self.MORNING_END
    
    def _is_evening_time(self) -> bool:
        """Check if current time is in evening window."""
        hour = datetime.now().hour
        return self.EVENING_START <= hour <= self.EVENING_END
    
    def _is_active_hours(self) -> bool:
        """Check if current time is during active hours (9 AM - 10 PM)."""
        hour = datetime.now().hour
        return 9 <= hour <= 22
    
    def _do_morning_checkin(self) -> Optional[str]:
        """Morning check-in message."""
        # Check for due tasks first
        due_tasks = self.task_automation.get_due_tasks()
        
        if due_tasks:
            task_list = "\n".join(
                f"- {t.title}" for t in due_tasks[:3]
            )
            return f"☀️ Доброе утро, Гриша! У тебя есть дела на сегодня:\n{task_list}\n\nКак спалось?"
        
        return "☀️ Доброе утро, Гриша! Как планы на сегодня?"
    
    def _do_evening_wrapup(self) -> Optional[str]:
        """Evening wrap-up message."""
        # Check completed tasks
        pending = self.task_automation.get_pending_tasks(limit=3)
        
        if pending:
            task_list = "\n".join(
                f"- {t.title}" for t in pending[:3]
            )
            return f"🌙 Добрый вечер! Незавершённые дела:\n{task_list}\n\nКак день прошёл?"
        
        return "🌙 Добрый вечер, Гриша! Чем занимался сегодня?"
    
    def _do_task_reminder(self) -> Optional[str]:
        """Check and remind about due tasks."""
        due = self.task_automation.get_due_tasks()
        
        if not due:
            return None
        
        # Only remind once per task
        to_remind = [t for t in due if not t.reminder_sent]
        
        if not to_remind:
            return None
        
        # Mark as reminded
        for task in to_remind:
            task.reminder_sent = True
            task.reminder_count += 1
        
        if len(to_remind) == 1:
            return f"🔔 Напоминание: *{to_remind[0].title}*"
        
        task_list = "\n".join(f"- {t.title}" for t in to_remind[:3])
        return f"🔔 Напоминания:\n{task_list}"
    
    def _do_interest_update(self) -> Optional[str]:
        """Check for interest updates."""
        news = self.interest_engine.check_updates()
        
        if not news:
            return None
        
        # Pick most relevant
        top = news[0]
        return f"📰 Интересное по теме \"{top.interest_topic}\": {top.title}"
    
    def add_action(
        self,
        name: str,
        trigger_time: Optional[datetime] = None,
        interval_hours: Optional[float] = None,
        condition_fn: Optional[Callable[[], bool]] = None,
        action_fn: Optional[Callable[[], str]] = None
    ):
        """Add a proactive action."""
        action = ProactiveAction(
            name=name,
            trigger_time=trigger_time,
            interval_hours=interval_hours,
            condition_fn=condition_fn,
            action_fn=action_fn
        )
        self.actions.append(action)
    
    def remove_action(self, name: str):
        """Remove a proactive action."""
        self.actions = [a for a in self.actions if a.name != name]
    
    def enable_action(self, name: str):
        """Enable an action."""
        for action in self.actions:
            if action.name == name:
                action.enabled = True
    
    def disable_action(self, name: str):
        """Disable an action."""
        for action in self.actions:
            if action.name == name:
                action.enabled = False
    
    def trigger_now(self, action_name: str) -> Optional[str]:
        """Manually trigger an action."""
        for action in self.actions:
            if action.name == action_name:
                return action.execute()
        return None
    
    def check_and_execute(self) -> List[str]:
        """
        Check all actions and execute those that should run.
        
        Returns:
            List of messages that were generated
        """
        messages = []
        
        for action in self.actions:
            if action.should_execute():
                message = action.execute()
                if message and self.on_message:
                    self.on_message(message)
                    messages.append(message)
        
        return messages
    
    def start(self):
        """Start the proactive scheduler in background."""
        if self._running:
            return
        
        self._running = True
        
        def scheduler_loop():
            while self._running:
                # Check actions every minute
                self.check_and_execute()
                time.sleep(60)
        
        self._thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the proactive scheduler."""
        self._running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        return {
            "active_actions": sum(1 for a in self.actions if a.enabled),
            "total_actions": len(self.actions),
            "running": self._running,
            "actions": [
                {
                    "name": a.name,
                    "enabled": a.enabled,
                    "last_executed": a.last_executed.isoformat() if a.last_executed else None,
                    "execute_count": a.execute_count
                }
                for a in self.actions
            ]
        }


# =============================================================================
# Singleton accessor
# =============================================================================

_scheduler_instance: Optional[ProactiveScheduler] = None


def get_proactive_scheduler(
    callback: Optional[Callable[[str], None]] = None
) -> ProactiveScheduler:
    """Get or create the global Proactive Scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = ProactiveScheduler(on_message=callback)
    return _scheduler_instance