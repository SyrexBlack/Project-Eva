"""
Eva Vision Module

Exports:
- get_vision: Get vision instance (screen capture)
- GameDetector: Detect running games
- GameAnalyzer: Analyze game screen
- GamingAdvisor: AI gaming advisor
"""

from eva.vision.screen import get_vision, EvaVision
from eva.vision.game_detector import (
    detect_game,
    GameInfo,
    GameType,
    GameMonitor,
    get_active_window_info,
    is_game_active
)
from eva.vision.game_analyzer import (
    GameAnalyzer,
    GameAnalysis,
    GameSituation,
    GamingAdvisor,
    create_gaming_mode
)

__all__ = [
    # Screen
    "get_vision",
    "EvaVision",
    
    # Game Detection
    "detect_game",
    "GameInfo",
    "GameType",
    "GameMonitor",
    "get_active_window_info",
    "is_game_active",
    
    # Game Analysis
    "GameAnalyzer",
    "GameAnalysis",
    "GameSituation",
    "GamingAdvisor",
    "create_gaming_mode",
]