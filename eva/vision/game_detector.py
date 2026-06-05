"""
Eva's Game Detector

Определяет запущенную игру по активному окну.
Работает через xprop (доступен везде) + /proc + ps.

Как это работает:
1. Получаем ID активного окна через xprop -root _NET_ACTIVE_WINDOW
2. Получаем имя окна через xprop -id <wid> WM_NAME
3. Матчим имя с базой известных игр
4. Дополнительно проверяем процессы через ps

Поддерживает: League of Legends, Wild Rift, Dota 2, CS2, Valorant и другие.
"""

import subprocess
import re
from typing import Optional, List, Tuple
from dataclasses import dataclass
from enum import Enum


class GameType(Enum):
    """Типы игр."""
    LEAGUE_OF_LEGENDS = "league_of_legends"
    WILD_RIFT = "wild_rift"
    DOTA_2 = "dota_2"
    CS2 = "cs2"
    VALORANT = "valorant"
    MINECRAFT = "minecraft"
    OTHER = "other"


@dataclass
class GameInfo:
    """Информация об игре."""
    name: str           # Читаемое имя (e.g. "League of Legends")
    type: GameType      # Enum тип
    window_title: str   # Оригинальное имя окна
    process_name: str   # Имя процесса (если найден)
    is_fullscreen: bool # Полноэкранный режим
    confidence: float   # Уверенность определения (0.0 - 1.0)


# База известных игр и их паттернов
GAME_PATTERNS: List[Tuple[GameType, str, str, List[str]]] = [
    # (GameType, display_name, process_pattern, window_name_patterns)
    (
        GameType.LEAGUE_OF_LEGENDS,
        "League of Legends",
        "League of Legends",
        ["league of legends", "leagueclientux", "league of legends:*", "lcu"]
    ),
    (
        GameType.WILD_RIFT,
        "Wild Rift",
        "WildRift",
        ["wild rift", "wildrift", "league of legends: wild rift"]
    ),
    (
        GameType.DOTA_2,
        "Dota 2",
        "dota2",
        ["dota 2", "dota2"]
    ),
    (
        GameType.CS2,
        "Counter-Strike 2",
        "cs2",
        ["counter-strike 2", "cs2", "csgo"]
    ),
    (
        GameType.VALORANT,
        "Valorant",
        "valorant",
        ["valorant"]
    ),
    (
        GameType.MINECRAFT,
        "Minecraft",
        "java",
        ["minecraft", "minecraft*"]
    ),
]


def _run_cmd(cmd: List[str]) -> str:
    """Запуск shell команды, возврат stdout."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError, PermissionError):
        return ""


def get_active_window_info() -> Tuple[Optional[int], Optional[str]]:
    """
    Получить ID и название активного окна через xprop.
    
    Returns:
        (window_id, window_title) или (None, None) если не удалось
    """
    # Получаем ID активного окна
    wid_output = _run_cmd(["xprop", "-root", "_NET_ACTIVE_WINDOW"])
    if not wid_output:
        return None, None
    
    # Парсим: _NET_ACTIVE_WINDOW(WINDOW): window id # 0x4a00004
    match = re.search(r'window id # (0x[0-9a-f]+)', wid_output, re.IGNORECASE)
    if not match:
        return None, None
    
    wid = match.group(1)
    
    # Получаем имя окна
    title = _run_cmd(["xprop", "-id", wid, "WM_NAME"])
    if not title:
        return None, None
    
    # Парсим: WM_NAME(STRING) = "League of Legends"
    match = re.search(r'= "(.*)"', title)
    if not match:
        return None, None
    
    window_title = match.group(1).lower()
    
    # Конвертируем hex wid в int
    try:
        wid_int = int(wid, 16)
    except ValueError:
        wid_int = None
    
    return wid_int, window_title


def find_game_processes() -> List[str]:
    """
    Найти запущенные игровые процессы через ps.
    
    Returns:
        Список имён найденных процессов
    """
    # Получаем все процессы
    ps_output = _run_cmd(["ps", "aux"])
    if not ps_output:
        return []
    
    found = []
    lines = ps_output.lower().split('\n')
    
    for game_type, _, process_pattern, _ in GAME_PATTERNS:
        if process_pattern.lower() in ps_output.lower():
            found.append(game_type.value)
    
    return found


def detect_game() -> Optional[GameInfo]:
    """
    Определить запущенную игру.
    
    Returns:
        GameInfo если игра найдена, None если нет
    """
    # 1. Пробуем через активное окно (приоритет)
    wid, window_title = get_active_window_info()
    
    if window_title:
        # Ищем совпадение в базе игр
        for game_type, display_name, process_name, patterns in GAME_PATTERNS:
            for pattern in patterns:
                if pattern.lower() in window_title:
                    return GameInfo(
                        name=display_name,
                        type=game_type,
                        window_title=window_title,
                        process_name=process_name,
                        is_fullscreen=True,  # TODO: определить точно
                        confidence=0.95
                    )
    
    # 2. Фоллбэк — ищем процессы
    processes = find_game_processes()
    if processes:
        # Берём первый найденный
        for game_type, display_name, process_name, patterns in GAME_PATTERNS:
            if game_type.value in processes:
                return GameInfo(
                    name=display_name,
                    type=game_type,
                    window_title="",
                    process_name=process_name,
                    is_fullscreen=False,
                    confidence=0.7  # Ниже, т.к. не через окно
                )
    
    return None


def is_game_active() -> bool:
    """Быстрая проверка — запущена ли какая-то игра."""
    return detect_game() is not None


def get_all_monitors_info() -> dict:
    """Получить информацию о всех мониторах через xrandr."""
    output = _run_cmd(["xrandr"])
    
    if not output:
        return {"error": "xrandr not available"}
    
    monitors = []
    for line in output.split('\n'):
        if 'connected' in line.lower():
            # "DP-1 connected primary 1920x1080+0+0 ..."
            parts = line.split()
            if len(parts) >= 4:
                monitors.append({
                    "name": parts[0],
                    "connected": "connected" in line.lower(),
                    "primary": "primary" in line.lower(),
                    "resolution": parts[2] if len(parts) > 2 else "unknown"
                })
    
    return {"monitors": monitors}


# ============================================================================
# Для интеграции с companion.py
# ============================================================================

class GameMonitor:
    """
    Мониторит активность игр в реальном времени.
    
    Использование:
        monitor = GameMonitor()
        
        # Периодическая проверка
        if monitor.is_game_running():
            game = monitor.get_current_game()
            print(f"Играем в {game.name}")
    """
    
    def __init__(self, check_interval: float = 2.0):
        """
        Args:
            check_interval: Интервал проверки в секундах
        """
        self.check_interval = check_interval
        self.last_game: Optional[GameInfo] = None
        self.game_started_at: Optional[float] = None
    
    def check(self) -> Optional[GameInfo]:
        """Проверить текущую игру."""
        import time
        
        game = detect_game()
        
        # Отслеживаем когда игра началась
        if game and not self.last_game:
            self.game_started_at = time.time()
        
        self.last_game = game
        return game
    
    def get_current_game(self) -> Optional[GameInfo]:
        """Получить текущую игру (кешировано)."""
        return self.last_game
    
    def was_game_played(self) -> bool:
        """Проверить была ли запущена игра за последнее время."""
        return self.last_game is not None


# Тест
if __name__ == "__main__":
    print("=== Game Detector Test ===\n")
    
    # Информация о мониторах
    print("Monitors:")
    monitors = get_all_monitors_info()
    for m in monitors.get("monitors", []):
        print(f"  {m['name']} - {m['resolution']} {'(primary)' if m['primary'] else ''}")
    
    print()
    
    # Проверка активного окна
    print("Active window:")
    wid, title = get_active_window_info()
    print(f"  Window ID: {wid}")
    print(f"  Title: {title}")
    
    print()
    
    # Проверка игры
    print("Game detection:")
    game = detect_game()
    if game:
        print(f"  ✅ Found: {game.name}")
        print(f"  Type: {game.type.value}")
        print(f"  Confidence: {game.confidence:.0%}")
    else:
        print("  ❌ No game detected")
