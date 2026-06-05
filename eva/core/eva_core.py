"""
Eva's Core Integration

Объединяет все модули Евы в единую систему.
Главная точка входа для всех возможностей.

Использование:
    from eva import EvaCore
    
    eva = EvaCore()
    eva.initialize()
    
    # Проверка статуса
    status = eva.get_status()
    
    # Отправка уведомления
    eva.notify("Hello from Eva!")
"""

import os
import time
import threading
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


@dataclass
class EvaConfig:
    """Конфигурация Евы."""
    # Модули
    enable_telegram: bool = True
    enable_github: bool = True
    enable_calendar: bool = True
    enable_proactive: bool = True
    enable_notifications: bool = True
    
    # Интервалы (секунды)
    health_check_interval: int = 300  # 5 минут
    proactive_check_interval: int = 300  # 5 минут
    github_check_interval: int = 900  # 15 минут
    
    # Тихие часы
    quiet_hours_start: int = 22
    quiet_hours_end: int = 8


class EvaCore:
    """
    Eva's Core — объединяет все системы.
    
    Использование:
        eva = EvaCore()
        eva.initialize()
        
        # Система
        status = eva.get_system_status()
        
        # Уведомления
        eva.notify("Test message")
        
        # Календарь
        events = eva.get_today_events()
        
        # GitHub
        github_summary = eva.get_github_summary()
    """
    
    def __init__(self, config: Optional[EvaConfig] = None):
        self.config = config or EvaConfig()
        
        # Системы (lazy initialization)
        self._system = None
        self._proactive = None
        self._api = None
        self._emotional = None
        self._telegram = None
        self._github = None
        self._calendar = None
        self._notifications = None
        
        # Состояние
        self._is_initialized = False
        self._is_running = False
        self._threads: List[threading.Thread] = []
        
        # Callbacks
        self._on_notification: Optional[Callable[[str, str], None]] = None
    
    # =========================================================================
    # Lazy Initialization — загружаем модули только когда нужны
    # =========================================================================
    
    @property
    def system(self):
        """System monitor."""
        if self._system is None:
            from eva.skills import get_system_monitor
            self._system = get_system_monitor()
        return self._system
    
    @property
    def proactive(self):
        """Proactive scheduler."""
        if self._proactive is None:
            from eva.skills import get_proactive
            self._proactive = get_proactive(self.config.proactive_check_interval)
        return self._proactive
    
    @property
    def api(self):
        """API client."""
        if self._api is None:
            from eva.skills import get_api_client
            self._api = get_api_client()
        return self._api
    
    @property
    def emotional(self):
        """Emotional intelligence."""
        if self._emotional is None:
            from eva.skills import get_emotional_intelligence
            self._emotional = get_emotional_intelligence()
        return self._emotional
    
    @property
    def telegram(self):
        """Telegram bot."""
        if self._telegram is None and self.config.enable_telegram:
            from eva.skills import get_telegram_bot
            self._telegram = get_telegram_bot()
        return self._telegram
    
    @property
    def notifications(self):
        """Notification manager."""
        if self._notifications is None:
            from eva.skills import get_notification_manager
            self._notifications = get_notification_manager()
        return self._notifications
    
    @property
    def github(self):
        """GitHub client."""
        if self._github is None and self.config.enable_github:
            from eva.skills import get_github_client
            self._github = get_github_client()
        return self._github
    
    @property
    def calendar(self):
        """Local calendar."""
        if self._calendar is None and self.config.enable_calendar:
            from eva.skills import get_local_calendar
            self._calendar = get_local_calendar()
        return self._calendar
    
    # =========================================================================
    # Initialization
    # =========================================================================
    
    def initialize(self):
        """Инициализировать все системы."""
        if self._is_initialized:
            return
        
        print("🔧 Eva Core initializing...")
        
        # Проверяем конфигурацию
        self._check_config()
        
        # Инициализируем модули
        if self.config.enable_telegram:
            _ = self.telegram  # Инициализируем telegram
            print("   ✅ Telegram bot ready")
        
        if self.config.enable_github:
            _ = self.github
            print("   ✅ GitHub integration ready")
        
        if self.config.enable_calendar:
            _ = self.calendar
            print("   ✅ Calendar ready")
        
        if self.config.enable_proactive:
            _ = self.proactive
            print("   ✅ Proactive scheduler ready")
        
        # Инициализируем остальные
        _ = self.system
        _ = self.api
        _ = self.emotional
        _ = self.notifications
        
        self._is_initialized = True
        print("✅ Eva Core initialized!\n")
    
    def _check_config(self):
        """Проверить конфигурацию."""
        warnings = []
        
        if self.config.enable_telegram and not os.getenv("TELEGRAM_BOT_TOKEN"):
            warnings.append("TELEGRAM_BOT_TOKEN not set — Telegram disabled")
            self.config.enable_telegram = False
        
        if self.config.enable_github and not os.getenv("GITHUB_USERNAME"):
            warnings.append("GITHUB_USERNAME not set — GitHub disabled")
            self.config.enable_github = False
        
        if warnings:
            print("⚠️ Configuration warnings:")
            for w in warnings:
                print(f"   {w}")
    
    def start(self):
        """Запустить все системы."""
        if self._is_running:
            return
        
        self.initialize()
        self._is_running = True
        
        # Запускаем мониторинг
        if self.config.enable_proactive:
            self.proactive.start()
        
        # Telegram polling
        if self.config.enable_telegram and self.telegram:
            self.telegram.start()
        
        print("🚀 Eva Core running")
    
    def stop(self):
        """Остановить все системы."""
        self._is_running = False
        
        if self.proactive:
            self.proactive.stop()
        
        if self.telegram:
            self.telegram.stop()
        
        print("⏹️ Eva Core stopped")
    
    # =========================================================================
    # System Status
    # =========================================================================
    
    def get_status(self) -> Dict[str, Any]:
        """Получить общий статус всех систем."""
        return {
            "initialized": self._is_initialized,
            "running": self._is_running,
            "timestamp": datetime.now().isoformat(),
            "modules": {
                "telegram": self.config.enable_telegram,
                "github": self.config.enable_github,
                "calendar": self.config.enable_calendar,
                "proactive": self.config.enable_proactive
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Получить статус системы (CPU, RAM, диски)."""
        return self.system.health.get_full_report()
    
    def get_server_status(self) -> Dict[str, Any]:
        """Получить статус серверов."""
        return self.system.servers.get_status_summary()
    
    # =========================================================================
    # Notifications
    # =========================================================================
    
    def notify(
        self,
        message: str,
        title: str = "Eva",
        level: str = "info"
    ):
        """Отправить уведомление."""
        if not self.config.enable_notifications:
            return
        
        # Проверяем тихие часы
        hour = datetime.now().hour
        is_quiet = self.quiet_hours_start <= hour or hour < self.quiet_hours_end
        
        if is_quiet and level == "info":
            # Сохраняем для later
            pass
        else:
            self.notifications.send(message, level)
    
    def notify_server_down(self, server_name: str):
        """Уведомить о падении сервера."""
        self.notifications.notify_server_down(server_name)
    
    def notify_crypto_alert(self, symbol: str, price: float, change: float):
        """Уведомить об изменении крипты."""
        self.notifications.notify_crypto_alert(symbol, price, change)
    
    # =========================================================================
    # Quick Commands
    # =========================================================================
    
    def get_weather(self, city: str = "Moscow") -> str:
        """Получить погоду."""
        weather = self.api.get_weather(city)
        return weather.format() if weather else "Не удалось получить погоду"
    
    def get_crypto(self, symbols: List[str] = None) -> str:
        """Получить курсы криптовалют."""
        if symbols is None:
            symbols = ["bitcoin", "ethereum", "solana"]
        
        lines = ["💰 Криптовалюта:"]
        for symbol in symbols:
            price = self.api.get_crypto_price(symbol)
            if price:
                lines.append(price.format())
        
        return "\n".join(lines)
    
    def get_github_summary(self) -> str:
        """Получить сводку GitHub."""
        if not self.github:
            return "GitHub не настроен"
        return self.github.get_status_summary()
    
    def get_today_events(self) -> str:
        """Получить события на сегодня."""
        if not self.calendar:
            return "Календарь не настроен"
        return self.calendar.get_summary()
    
    # =========================================================================
    # Interactive Commands
    # =========================================================================
    
    def analyze_mood(self, text: str) -> Dict[str, Any]:
        """Анализировать настроение текста."""
        result = self.emotional.analyze_sentiment(text)
        tone = self.emotional.get_appropriate_tone(result.mood)
        
        return {
            "mood": result.mood.value,
            "confidence": result.confidence,
            "tone": tone
        }
    
    # =========================================================================
    # Full Report
    # =========================================================================
    
    def get_full_report(self) -> str:
        """Получить полный отчёт для Гриши."""
        lines = [
            "📊 *Eva — Полный отчёт*",
            "=" * 40,
            ""
        ]
        
        # Система
        health = self.get_system_status()
        lines.extend([
            "🖥️ *Система*",
            f"   CPU: {health['cpu']['usage_percent']:.1f}%",
            f"   RAM: {health['memory']['percent']:.1f}%",
            f"   Disk: {health['disk']['percent']:.1f}%",
            ""
        ])
        
        # Погода
        weather = self.api.get_weather("Moscow")
        if weather:
            lines.extend([
                f"🌤️ *{weather.city}*",
                f"   {weather.temperature:.0f}°C, {weather.description}",
                ""
            ])
        
        # Крипта
        btc = self.api.get_crypto_price("bitcoin")
        if btc:
            lines.extend([
                f"₿ Bitcoin: ${btc.price_usd:,.0f} ({btc.change_24h:+.1f}%)",
                ""
            ])
        
        # Календарь
        if self.calendar:
            today = self.calendar.get_today()
            if today:
                lines.append(f"📅 *События сегодня:* {len(today)}")
            else:
                lines.append("📅 Сегодня нет событий")
        
        # GitHub
        if self.github and self.github.username:
            lines.extend([
                "",
                f"🐙 GitHub: {self.github.username}",
                f"   Repos: {len(self.github.get_repos())}"
            ])
        
        lines.append("")
        lines.append(f"🕐 Обновлено: {datetime.now().strftime('%H:%M')}")
        
        return "\n".join(lines)


# =============================================================================
# Singleton
# =============================================================================

_eva_core: Optional[EvaCore] = None


def get_eva_core() -> EvaCore:
    """Get or create global Eva Core instance."""
    global _eva_core
    if _eva_core is None:
        _eva_core = EvaCore()
    return _eva_core


# =============================================================================
# CLI Entry Point
# =============================================================================

def main():
    """CLI интерфейс."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Eva AI Companion")
    parser.add_argument("--report", action="store_true", help="Get full report")
    parser.add_argument("--status", action="store_true", help="System status")
    parser.add_argument("--weather", action="store_true", help="Weather")
    parser.add_argument("--crypto", action="store_true", help="Crypto prices")
    
    args = parser.parse_args()
    
    eva = get_eva_core()
    
    if args.report:
        print(eva.get_full_report())
    elif args.status:
        import json
        print(json.dumps(eva.get_system_status(), indent=2))
    elif args.weather:
        print(eva.get_weather())
    elif args.crypto:
        print(eva.get_crypto())
    else:
        print(eva.get_full_report())


if __name__ == "__main__":
    main()