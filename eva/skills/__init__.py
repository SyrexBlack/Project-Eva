"""
Eva Skills Module

Exports:
- get_proactive: Get proactive AI instance
- InterestEngine: Monitor interests
- TaskAutomation: Reminders and scheduling
- EvaProactive: Proactive AI system
"""

from eva.skills.proactive import (
    get_proactive,
    InterestEngine,
    TaskAutomation,
    ProactiveScheduler,
    EvaProactive,
    ProactiveAction,
    ProactiveType,
    Interest
)

__all__ = [
    "get_proactive",
    "InterestEngine",
    "TaskAutomation",
    "ProactiveScheduler",
    "EvaProactive",
    "ProactiveAction",
    "ProactiveType",
    "Interest",
]