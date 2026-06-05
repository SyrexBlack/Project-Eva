"""
Eva Skills Package

Все навыки Евы в одном месте.

Импорт:
    from eva.skills import (
        get_system_monitor,
        get_proactive,
        get_api_client,
        get_emotional_intelligence,
        get_telegram_bot,
        get_github_client,
        get_local_calendar,
        get_notification_manager
    )
"""

# System integration
from eva.skills.system import (
    SystemMonitor,
    ServerMonitor,
    SystemHealth,
    FileOperations,
    get_system_monitor,
    ServerType,
    AlertLevel,
    SystemAlert,
    ServerStatus
)

# Proactive AI
from eva.skills.proactive import (
    ProactiveScheduler,
    InterestEngine,
    TaskAutomation,
    EvaProactive,
    get_proactive,
    ProactiveType,
    ProactiveAction,
    Interest
)

# API Integration
from eva.skills.api_integration import (
    APIClient,
    get_api_client,
    WeatherData,
    CryptoPrice,
    NewsItem
)

# Emotional Intelligence
from eva.skills.emotional_intelligence import (
    EmotionalIntelligence,
    get_emotional_intelligence,
    Mood,
    SentimentResult,
    ImportantDate
)

# Telegram Bot
from eva.skills.telegram_bot import (
    TelegramBot,
    NotificationManager,
    get_telegram_bot,
    get_notification_manager,
    Command,
    TelegramMessage,
    MessageType
)

# GitHub Integration
from eva.skills.github_integration import (
    GitHubClient,
    ProjectMonitor,
    get_github_client,
    get_project_monitor,
    Repository,
    Commit,
    Activity,
    ActivityType
)

# Calendar Integration
from eva.skills.calendar_integration import (
    LocalCalendar,
    GoogleCalendarClient,
    ReminderScheduler,
    get_local_calendar,
    get_google_calendar,
    CalendarEvent,
    EventStatus,
    EventPriority
)

# Crypto Tracker
from eva.skills.crypto_tracker import (
    CryptoTracker,
    CryptoPrice,
    PortfolioPosition,
    get_crypto_tracker
)

# Health Tracker
from eva.skills.health_tracker import (
    HealthTracker,
    WeightEntry,
    SupplementDose,
    get_health_tracker
)

__all__ = [
    # System
    "get_system_monitor",
    "SystemMonitor",
    "ServerMonitor", 
    "SystemHealth",
    
    # Proactive
    "get_proactive",
    "ProactiveScheduler",
    "InterestEngine",
    "TaskAutomation",
    
    # API
    "get_api_client",
    "APIClient",
    
    # Emotional
    "get_emotional_intelligence",
    "EmotionalIntelligence",
    "Mood",
    
    # Telegram
    "get_telegram_bot",
    "get_notification_manager",
    "TelegramBot",
    "NotificationManager",
    
    # GitHub
    "get_github_client",
    "get_project_monitor",
    "GitHubClient",
    "ProjectMonitor",
    
    # Calendar
    "get_local_calendar",
    "get_google_calendar",
    "LocalCalendar",
    "CalendarEvent",
    
    # Crypto
    "get_crypto_tracker",
    "CryptoTracker",
    "CryptoPrice",
    
    # Health
    "get_health_tracker",
    "HealthTracker",
    "WeightEntry",
]