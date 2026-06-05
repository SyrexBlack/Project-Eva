"""
Eva's Telegram Bot Integration

Мгновенные уведомления и управление через Telegram.
Гриша получит доступ к Еве из любой точки мира.

Возможности:
- Отправка уведомлений (серверы, напоминания)
- Команды (/status, /crypto, /weather)
- Голосовые сообщения
- Быстрые ответы на вопросы

Установка:
1. Создай бота через @BotFather в Telegram
2. Получи токен
3. Настрой webhook или polling

.env:
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id  # Опционально для отправки
"""

import os
import json
import threading
from typing import Optional, Callable, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

from dotenv import load_dotenv

load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Типы сообщений."""
    TEXT = "text"
    PHOTO = "photo"
    VOICE = "voice"
    VIDEO = "video"
    DOCUMENT = "document"
    COMMAND = "command"


@dataclass
class TelegramMessage:
    """Сообщение из Telegram."""
    message_id: int
    chat_id: int
    message_type: MessageType
    text: str = ""
    sender_name: str = "Unknown"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Command:
    """Команда бота."""
    name: str
    description: str
    handler: Callable[[TelegramMessage], str]
    aliases: List[str] = field(default_factory=list)


class TelegramBot:
    """
    Eva's Telegram Bot.
    
    Использование:
        bot = TelegramBot()
        
        # Добавить команду
        @bot.command("hello")
        def hello(msg):
            return "Привет, Гриша! 👋"
        
        # Отправить уведомление
        bot.send_message("Сервер Vitbon запущен!")
        
        # Запустить
        bot.start()
    """
    
    def __init__(self, token: Optional[str] = None):
        """
        Инициализировать бота.
        
        Args:
            token: Telegram bot token (или из TELEGRAM_BOT_TOKEN)
        """
        self.token = token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        self._commands: Dict[str, Command] = {}
        self._message_handlers: List[Callable[[TelegramMessage], None]] = []
        self._is_running = False
        self._update_offset = 0
        self._poll_thread: Optional[threading.Thread] = None
        
        # Инициализируем дефолтные команды
        self._init_default_commands()
    
    def _init_default_commands(self):
        """Инициализировать дефолтные команды."""
        self.add_command(Command(
            name="start",
            description="Начать работу с Евой",
            handler=lambda m: "👋 Привет! Я Eva, AI-компаньон Гриши!\n\nКоманды:\n/status - статус системы\n/crypto - цены криптовалют\n/help - помощь",
            aliases=["help"]
        ))
        
        self.add_command(Command(
            name="status",
            description="Статус серверов и системы",
            handler=self._handle_status
        ))
        
        self.add_command(Command(
            name="crypto",
            description="Курсы криптовалют",
            handler=self._handle_crypto
        ))
        
        self.add_command(Command(
            name="weather",
            description="Погода",
            handler=self._handle_weather
        ))
    
    def _handle_status(self, msg: TelegramMessage) -> str:
        """Обработчик команды /status."""
        try:
            from eva.skills.system import get_system_monitor
            monitor = get_system_monitor()
            health = monitor.health.get_full_report()
            
            cpu = health["cpu"]["usage_percent"]
            ram = health["memory"]["percent"]
            disk = health["disk"]["percent"]
            
            return (
                f"📊 *Система*\n"
                f"CPU: {cpu:.1f}%\n"
                f"RAM: {ram:.1f}%\n"
                f"Disk: {disk:.1f}%"
            )
        except Exception as e:
            return f"⚠️ Ошибка: {e}"
    
    def _handle_crypto(self, msg: TelegramMessage) -> str:
        """Обработчик команды /crypto."""
        try:
            from eva.skills.api_integration import get_api_client
            api = get_api_client()
            
            cryptos = ["bitcoin", "ethereum", "solana"]
            lines = ["💰 *Криптовалюта*"]
            
            for symbol in cryptos:
                price = api.get_crypto_price(symbol)
                if price:
                    lines.append(price.format())
            
            return "\n".join(lines)
        except Exception as e:
            return f"⚠️ Ошибка: {e}"
    
    def _handle_weather(self, msg: TelegramMessage) -> str:
        """Обработчик команды /weather."""
        try:
            from eva.skills.api_integration import get_api_client
            api = get_api_client()
            
            weather = api.get_weather("Moscow")
            if weather:
                return f"🌤️ *Москва*\n{weather.format()}"
            return "⚠️ Не удалось получить погоду"
        except Exception as e:
            return f"⚠️ Ошибка: {e}"
    
    def add_command(self, command: Command):
        """Добавить команду."""
        self._commands[command.name] = command
        for alias in command.aliases:
            self._commands[alias] = command
    
    def command(self, name: str, description: str = "", aliases: List[str] = None):
        """Декоратор для добавления команды."""
        def decorator(func: Callable[[TelegramMessage], str]):
            self.add_command(Command(
                name=name,
                description=description,
                handler=func,
                aliases=aliases or []
            ))
            return func
        return decorator
    
    def on_message(self, handler: Callable[[TelegramMessage], None]):
        """Добавить обработчик сообщений."""
        self._message_handlers.append(handler)
    
    def send_message(
        self,
        text: str,
        chat_id: Optional[str] = None,
        parse_mode: str = "Markdown"
    ) -> bool:
        """
        Отправить сообщение.
        
        Args:
            text: Текст сообщения
            chat_id: ID чата (или TELEGRAM_CHAT_ID)
            parse_mode: Markdown или HTML
            
        Returns:
            True если успешно
        """
        if not self.token:
            logger.warning("Telegram bot token not set")
            return False
        
        target_chat = chat_id or self.chat_id
        if not target_chat:
            logger.warning("No chat_id specified")
            return False
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/sendMessage"
            data = {
                "chat_id": target_chat,
                "text": text,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=data, timeout=10)
            result = response.json()
            
            return result.get("ok", False)
        
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def send_photo(
        self,
        photo_url: str,
        caption: str = "",
        chat_id: Optional[str] = None
    ) -> bool:
        """Отправить фото."""
        if not self.token or not self.chat_id:
            return False
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/sendPhoto"
            data = {
                "chat_id": chat_id or self.chat_id,
                "photo": photo_url,
                "caption": caption
            }
            
            response = requests.post(url, json=data, timeout=10)
            return response.json().get("ok", False)
        
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return False
    
    def send_notification(
        self,
        title: str,
        message: str,
        level: str = "info"
    ):
        """
        Отправить уведомление с эмодзи по уровню.
        
        Args:
            title: Заголовок
            message: Сообщение
            level: info, warning, error
        """
        icons = {
            "info": "ℹ️",
            "warning": "⚠️",
            "error": "🚨",
            "success": "✅"
        }
        
        icon = icons.get(level, "📢")
        self.send_message(f"{icon} *{title}*\n{message}")
    
    def _fetch_updates(self) -> List[Dict]:
        """Получить новые обновления."""
        if not self.token:
            return []
        
        try:
            import requests
            
            url = f"https://api.telegram.org/bot{self.token}/getUpdates"
            params = {
                "offset": self._update_offset,
                "timeout": 30,
                "allowed_updates": ["message", "callback_query"]
            }
            
            response = requests.get(url, params=params, timeout=35)
            data = response.json()
            
            if data.get("ok"):
                return data.get("result", [])
        
        except Exception as e:
            logger.error(f"Failed to fetch updates: {e}")
        
        return []
    
    def _process_update(self, update: Dict):
        """Обработать обновление."""
        if "message" not in update:
            return
        
        msg_data = update["message"]
        
        # Создаём объект сообщения
        msg = TelegramMessage(
            message_id=msg_data.get("message_id", 0),
            chat_id=msg_data.get("chat", {}).get("id", 0),
            message_type=MessageType.TEXT,
            text=msg_data.get("text", ""),
            sender_name=msg_data.get("from", {}).get("first_name", "Unknown"),
            timestamp=datetime.fromtimestamp(msg_data.get("date", 0))
        )
        
        # Обработка команд
        if msg.text.startswith("/"):
            parts = msg.text[1:].split()
            command_name = parts[0].lower()
            
            if command_name in self._commands:
                command = self._commands[command_name]
                try:
                    response = command.handler(msg)
                    if response:
                        self.send_message(response, chat_id=str(msg.chat_id))
                except Exception as e:
                    self.send_message(f"⚠️ Ошибка: {e}", chat_id=str(msg.chat_id))
        
        # Обработка обычных сообщений
        else:
            for handler in self._message_handlers:
                try:
                    handler(msg)
                except Exception as e:
                    logger.error(f"Message handler error: {e}")
    
    def _poll_loop(self):
        """Основной цикл опроса."""
        logger.info("Telegram bot polling started")
        
        while self._is_running:
            updates = self._fetch_updates()
            
            for update in updates:
                update_id = update.get("update_id", 0)
                self._update_offset = update_id + 1
                self._process_update(update)
    
    def start(self, polling: bool = True):
        """Запустить бота."""
        if not self.token:
            logger.warning("⚠️ TELEGRAM_BOT_TOKEN not set. Bot not started.")
            return
        
        if self._is_running:
            logger.info("Bot already running")
            return
        
        self._is_running = True
        
        if polling:
            self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
            self._poll_thread.start()
            logger.info("✅ Telegram bot started (polling mode)")
    
    def stop(self):
        """Остановить бота."""
        self._is_running = False
        logger.info("Telegram bot stopped")
    
    def set_webhook(self, url: str) -> bool:
        """Установить webhook."""
        if not self.token:
            return False
        
        try:
            import requests
            
            url_api = f"https://api.telegram.org/bot{self.token}/setWebhook"
            response = requests.post(url_api, json={"url": url}, timeout=10)
            
            return response.json().get("ok", False)
        
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")
            return False


# =============================================================================
# Notification System для интеграции с другими модулями
# =============================================================================

class NotificationManager:
    """
    Менеджер уведомлений.
    
    Интегрируется с SystemMonitor, ProactiveScheduler и другими модулями.
    """
    
    def __init__(self, telegram_bot: Optional[TelegramBot] = None):
        self.bot = telegram_bot
        self._notification_queue: List[Dict] = []
    
    def notify_server_down(self, server_name: str, error: str = ""):
        """Уведомить о падении сервера."""
        msg = f"🔴 Сервер *{server_name}* недоступен"
        if error:
            msg += f"\n`{error}`"
        self.send(msg)
    
    def notify_high_cpu(self, usage: float):
        """Уведомить о высокой нагрузке CPU."""
        self.send(f"⚠️ Высокая нагрузка CPU: {usage:.1f}%", level="warning")
    
    def notify_crypto_alert(self, symbol: str, price: float, change: float):
        """Уведомить об изменении цены крипты."""
        direction = "📈" if change >= 0 else "📉"
        self.send(
            f"{direction} *{symbol.upper()}* ${price:,.2f} ({change:+.2f}%)",
            level="info"
        )
    
    def notify_reminder(self, text: str, priority: float = 0.5):
        """Уведомить о напоминании."""
        self.send(f"📌 *Напоминание*\n{text}")
    
    def send(self, message: str, level: str = "info"):
        """Отправить уведомление."""
        if self.bot:
            self.bot.send_notification("Eva", message, level)
        else:
            # Сохраняем в очередь если бот не инициализирован
            self._notification_queue.append({
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat()
            })
    
    def flush_queue(self):
        """Отправить все накопленные уведомления."""
        for notif in self._notification_queue:
            if self.bot:
                self.bot.send_notification("Eva", notif["message"], notif["level"])
        self._notification_queue.clear()


# =============================================================================
# Singleton accessor
# =============================================================================

_telegram_bot: Optional[TelegramBot] = None
_notification_manager: Optional[NotificationManager] = None


def get_telegram_bot() -> TelegramBot:
    """Get or create global Telegram bot instance."""
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramBot()
    return _telegram_bot


def get_notification_manager() -> NotificationManager:
    """Get or create global notification manager."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager(get_telegram_bot())
    return _notification_manager


# =============================================================================
# Пример использования
# =============================================================================

if __name__ == "__main__":
    print("=== Telegram Bot Setup ===\n")
    
    # Проверяем токен
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("⚠️ Set TELEGRAM_BOT_TOKEN in .env to enable the bot")
        print("   1. Open @BotFather in Telegram")
        print("   2. Send /newbot")
        print("   3. Follow instructions")
        print("   4. Add token to .env\n")
    else:
        bot = get_telegram_bot()
        
        # Добавляем кастомную команду
        @bot.command("ping")
        def ping(msg):
            return "🏓 Pong!"
        
        @bot.command("echo", aliases=["repeat"])
        def echo(msg):
            text = msg.text.replace("/echo", "").replace("/repeat", "").strip()
            return f"Ты написал: {text}"
        
        print("✅ Bot configured")
        print("   Commands: /start, /status, /crypto, /weather, /ping, /echo")
        print("   Add TELEGRAM_CHAT_ID to .env to receive notifications\n")