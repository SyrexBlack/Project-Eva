"""
Eva Skills Module

Exports:
- get_proactive: Get proactive AI instance
- get_system_monitor: Get system monitor instance
- get_emotional_intelligence: Get emotional intelligence instance
- InterestEngine: Monitor interests
- TaskAutomation: Reminders and scheduling
- EvaProactive: Proactive AI system
- SystemMonitor: Server and system monitoring
- EmotionalIntelligence: Mood detection, personal connection
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

from eva.skills.system import (
    get_system_monitor,
    SystemMonitor,
    ServerMonitor,
    SystemHealth,
    FileOperations,
    ServerStatus,
    SystemAlert,
    AlertLevel,
    ServerType
)

from eva.skills.emotional import (
    get_emotional_intelligence,
    EmotionalIntelligence,
    MoodDetector,
    PersonalConnection,
    Mood,
    EmotionalState,
    ImportantDate
)

__all__ = [
    # Proactive
    "get_proactive",
    "InterestEngine",
    "TaskAutomation",
    "ProactiveScheduler",
    "EvaProactive",
    "ProactiveAction",
    "ProactiveType",
    "Interest",
    
    # System
    "get_system_monitor",
    "SystemMonitor",
    "ServerMonitor",
    "SystemHealth",
    "FileOperations",
    "ServerStatus",
    "SystemAlert",
    "AlertLevel",
    "ServerType",
    
    # Emotional
    "get_emotional_intelligence",
    "EmotionalIntelligence",
    "MoodDetector",
    "PersonalConnection",
    "Mood",
    "EmotionalState",
    "ImportantDate",
]