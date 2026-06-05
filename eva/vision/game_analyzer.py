"""
Eva's Game Analyzer

Анализирует игровой экран: распознаёт ситуацию, даёт советы.
Работает через Vision API (Opus 4.6) + опционально OCR.

Как это работает:
1. Захватываем экран через mss
2. Отправляем в Opus Vision для анализа
3. Получаем описание ситуации + советы
4. Ева говорит совет вслух

Поддержка: League of Legends, Wild Rift, Dota 2, CS2, Valorant
"""

import os
import time
import base64
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

import mss
import cv2
import numpy as np
from PIL import Image
from dotenv import load_dotenv

from eva.vision.screen import get_vision
from eva.vision.game_detector import detect_game, GameInfo, GameType

load_dotenv()


class GameSituation(Enum):
    """Игровые ситуации."""
    # LoL / Wild Rift
    TEAMFIGHT = "teamfight"
    DUEL = "duel"
    JUNGLING = "jungling"
    FARMING = "farming"
    RECALLING = "recalling"
    BACKING = "backing"
    ROAMING = "roaming"
    SIEGING = "sieging"
    DEFENDING = "defending"
    
    # Общие
    BASE = "base"
    SHOP = "shop"
    LOADING = "loading"
    UNKNOWN = "unknown"


@dataclass
class GameAnalysis:
    """Результат анализа игрового экрана."""
    situation: GameSituation
    situation_confidence: float
    description: str          # Что видим
    advice: str               # Совет от Евы
    key_metrics: Dict[str, Any]  # HP, gold, items, etc
    timestamp: datetime
    game: GameInfo


# =============================================================================
# LoL / Wild Rift база знаний
# =============================================================================

LOL_SITUATION_PROMPTS = {
    GameSituation.TEAMFIGHT: {
        "detection": ["много championov", "fight", "brawl", "skirmish", "combat"],
        "prompt": """Ты видишь командный бой (teamfight).
Оцени:
1. Кто из вашей команды участвует?
2. Кто из врагов участвует?
3. Кто в опасности (низкое HP)?
4. Есть ли CC abilities готовые?
5. Какие cooldowns критичны?

Дай короткий совет (1-2 предложения) что делать Грише.
Отвечай на русском, будь конкретным."""
    },
    GameSituation.DUEL: {
        "detection": ["1v1", "duel", "all-in", "engage"],
        "prompt": """Ты в дуэли 1v1.
Оцени:
1. Кто сильнее в данный момент?
2. Какие abilities доступны?
3. Какие summoners готовы?
4. В чью сторону флуктуация HP?

Дай короткий совет (1-2 предложения).
Отвечай на русском."""
    },
    GameSituation.JUNGLING: {
        "detection": ["jungle", "camp", "neutral", "buff", "dragon", "baron"],
        "prompt": """Ты в джунглях.
Оцени:
1. Какие лагеря доступны?
2. Какой jungler (ваш/враг)?
3. Объективы (dragon, baron, herald)?
4. Готов ли smite?

Дай короткий совет по приоритетам.
Отвечай на русском."""
    },
    GameSituation.FARMING: {
        "detection": ["minion", "wave", "farm", "lane"],
        "prompt": """Ты фармишь в лейне.
Оцени:
1. Какая волна (большая/маленькая)?
2. Пуш или фриз?
3. Есть ли враг в лейне?
4. Позиция jungler?

Дай совет по wave management.
Отвечай на русском."""
    },
    GameSituation.RECALLING: {
        "detection": ["recall", "back", "base"],
        "prompt": """Ты回城 (recall/backing).
Оцени:
1. Сколько gold?
2. Что нужно купить?
3. Сколько времени занял recall?
4. Волна у башни?

Дай совет по покупкам и timing.
Отвечай на русском."""
    },
    GameSituation.SHOP: {
        "detection": ["shop", "store", "item", "buy"],
        "prompt": """Ты в магазине.
Оцени:
1. Сколько gold?
2. Какие предметы нужны?
3. Приоритет покупок?
4. Есть ли good recall timing?

Дай совет по покупкам.
Отвечай на русском."""
    },
}


# =============================================================================
# Base64 encoding
# =============================================================================

def encode_image_to_base64(image_path: str) -> str:
    """Кодировать изображение в base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def encode_cv2_image(image: np.ndarray) -> str:
    """Кодировать CV2 изображение в base64."""
    _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode("utf-8")


# =============================================================================
# Game Analyzer
# =============================================================================

class GameAnalyzer:
    """
    Анализирует игровой экран и даёт советы.
    
    Использование:
        analyzer = GameAnalyzer()
        
        # Анализ текущего экрана
        analysis = analyzer.analyze_screen()
        
        if analysis:
            print(f"Ситуация: {analysis.situation.value}")
            print(f"Совет: {analysis.advice}")
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model: str = "claude-opus-4.6"
    ):
        """
        Args:
            base_url: API proxy URL
            api_key: API key
            model: Model name
        """
        self.base_url = base_url or os.getenv("BASE_URL", "http://89.167.8.202:8000/v1")
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model
        
        # Vision компонент
        self.vision = get_vision()
        
        # Кеш последнего анализа
        self.last_analysis: Optional[GameAnalysis] = None
        self.last_analysis_time: float = 0
        self.analysis_cooldown: float = 5.0  # Минимум 5 сек между анализами
    
    def _detect_situation(self, screenshot: np.ndarray) -> GameSituation:
        """
        Быстрое определение ситуации через HSV анализ и шаблоны.
        
        Используем цветовые паттерны для определения:
        - Синие/красные индикаторы = HP/комбат
        - Зелёные линии = мини-карта
        - Золотые искры = gold/shop
        """
        # TODO: Реализовать HSV анализ для каждой игры
        # Пока возвращаем UNKNOWN — будет определяться через Vision API
        
        # Простой анализ яркости
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
        avg_brightness = np.mean(hsv[:, :, 2])
        
        # Тёмный экран = скорее всего loading screen
        if avg_brightness < 50:
            return GameSituation.LOADING
        
        return GameSituation.UNKNOWN
    
    def _build_vision_prompt(self, game: GameInfo, situation: GameSituation) -> str:
        """Построить промпт для Vision API."""
        
        # Базовый промпт
        base = f"""Ты — Ева, AI-компаньон для игрока в {game.name}.
Ты видишь экран игры прямо сейчас.

Опиши что происходит на экране. Будь конкретным:
- Какая ситуация (бой, фарм, шоп и т.д.)
- Что видишь на мини-карте
- HP союзников и врагов (приблизительно)
- Кто из врагов представляет угрозу
- Какие abilities важны в данный момент

Затем дай короткий совет (1-2 предложения) что делать игроку.
Совет должен быть:
- Конкретным (когда и куда идти, что делать)
- Полезным для победы
- На русском языке

Формат ответа:
СИТУАЦИЯ: <описание>
СОВЕТ: <1-2 предложения>"""
        
        return base
    
    def analyze_screen(
        self,
        screenshot_path: Optional[str] = None,
        screenshot: Optional[np.ndarray] = None,
        force: bool = False
    ) -> Optional[GameAnalysis]:
        """
        Анализировать текущий игровой экран.
        
        Args:
            screenshot_path: Путь к скриншоту (если уже есть)
            screenshot: CV2 изображение (если уже захвачено)
            force: Игнорировать cooldown
        
        Returns:
            GameAnalysis с описанием и советами
        """
        # Проверяем cooldown
        if not force and time.time() - self.last_analysis_time < self.analysis_cooldown:
            return self.last_analysis
        
        # 1. Определяем игру
        game = detect_game()
        if not game:
            return None
        
        # 2. Захватываем экран
        if screenshot is None and screenshot_path is None:
            screenshot_path = self.vision.capture_screen()
            screenshot = cv2.imread(screenshot_path)
        
        if screenshot is None:
            return None
        
        # 3. Определяем ситуацию (быстрый анализ)
        situation = self._detect_situation(screenshot)
        
        # 4. Анализ через Vision API
        image_base64 = encode_cv2_image(screenshot)
        
        # Формируем промпт
        vision_prompt = self._build_vision_prompt(game, situation)
        
        # Отправляем в API
        try:
            from openai import OpenAI
            client = OpenAI(base_url=self.base_url, api_key=self.api_key)
            
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": vision_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{image_base64}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=512,
                temperature=0.7
            )
            
            analysis_text = response.choices[0].message.content or ""
            
        except Exception as e:
            analysis_text = f"[Ошибка анализа: {e}]"
        
        # 5. Парсим ответ
        situation_name, advice = self._parse_analysis(analysis_text)
        
        # 6. Создаём результат
        analysis = GameAnalysis(
            situation=situation_name,
            situation_confidence=0.8,
            description=analysis_text,
            advice=advice,
            key_metrics={},
            timestamp=datetime.now(),
            game=game
        )
        
        # Кешируем
        self.last_analysis = analysis
        self.last_analysis_time = time.time()
        
        return analysis
    
    def _parse_analysis(self, text: str) -> tuple[GameSituation, str]:
        """Парсим ответ от Vision API."""
        
        # Ищем "СОВЕТ:" в тексте
        if "СОВЕТ:" in text.upper():
            parts = text.upper().split("СОВЕТ:")
            advice = parts[-1].strip()
        else:
            advice = text.strip()
        
        # Определяем ситуацию по ключевым словам
        text_lower = text.lower()
        
        if any(w in text_lower for w in ["бой", "fight", "combat", "teamfight", "драка"]):
            situation = GameSituation.TEAMFIGHT
        elif any(w in text_lower for w in ["1v1", "дуэль", "duel", "1 на 1"]):
            situation = GameSituation.DUEL
        elif any(w in text_lower for w in ["джунгл", "jungle", "нейтрал", "лагерь", "buff"]):
            situation = GameSituation.JUNGLING
        elif any(w in text_lower for w in ["фарм", "farm", "лейн", "lane", "волна", "minion"]):
            situation = GameSituation.FARMING
        elif any(w in text_lower for w in ["шоп", "shop", "магазин", "buy", "покупка"]):
            situation = GameSituation.SHOP
        elif any(w in text_lower for w in ["реколл", "recall", "back", "база", "башня"]):
            situation = GameSituation.RECALLING
        else:
            situation = GameSituation.UNKNOWN
        
        return situation, advice
    
    def get_advice(self) -> Optional[str]:
        """Получить совет для текущей ситуации (кешировано)."""
        if self.last_analysis:
            return self.last_analysis.advice
        return None


# =============================================================================
# Gaming Advisor — советы с учётом контекста
# =============================================================================

class GamingAdvisor:
    """
    AI-советник для игр — даёт контекстные советы.
    
    В отличие от GameAnalyzer, здесь:
    - Учитывается история игры
    - Есть база знаний по играм
    - Адаптация под стиль Гриши
    """
    
    def __init__(self, analyzer: GameAnalyzer):
        self.analyzer = analyzer
        self.game_history: List[GameAnalysis] = []
        self.session_start = datetime.now()
    
    def analyze_and_advise(self) -> Optional[str]:
        """Полный цикл: анализ → совет → сохранение в историю."""
        analysis = self.analyzer.analyze_screen()
        
        if not analysis:
            return None
        
        # Сохраняем в историю
        self.game_history.append(analysis)
        
        # Ограничиваем историю (последние 100)
        if len(self.game_history) > 100:
            self.game_history = self.game_history[-100:]
        
        return analysis.advice
    
    def get_session_stats(self) -> dict:
        """Статистика текущей игровой сессии."""
        return {
            "duration": str(datetime.now() - self.session_start),
            "analyses": len(self.game_history),
            "last_situation": self.game_history[-1].situation.value if self.game_history else None,
            "game": self.game_history[-1].game.name if self.game_history else None
        }


# =============================================================================
# Для интеграции с companion.py
# =============================================================================

def create_gaming_mode(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> tuple[GameAnalyzer, GamingAdvisor]:
    """
    Создать gaming mode для Евы.
    
    Returns:
        (GameAnalyzer, GamingAdvisor)
    """
    analyzer = GameAnalyzer(base_url=base_url, api_key=api_key)
    advisor = GamingAdvisor(analyzer)
    return analyzer, advisor


# Тест
if __name__ == "__main__":
    print("=== Game Analyzer Test ===\n")
    
    # Проверяем game detector
    game = detect_game()
    if game:
        print(f"✅ Game detected: {game.name}")
    else:
        print("❌ No game running")
        print("Game analyzer ready — will analyze when game is detected")
