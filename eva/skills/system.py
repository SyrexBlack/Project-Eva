"""
Eva's System Integration Module

Глубокая интеграция с системой:
- Server Monitor: wg-easy, 3x-ui, Vitbon
- File Operations: поиск, создание, редактирование
- Network Monitor: VPN, серверы
- System Health: CPU, RAM, температура

Как это работает:
1. Мониторит серверы и систему
2. Уведомляет при проблемах
3. Позволяет выполнять операции
"""

import os
import time
import threading
import subprocess
from typing import Optional, List, Dict, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class ServerType(Enum):
    """Типы серверов."""
    VPN_WG_EASY = "wg_easy"
    VPN_3X_UI = "3x_ui"
    VITBON = "vitbon"
    CUSTOM = "custom"


class AlertLevel(Enum):
    """Уровни алертов."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class ServerStatus:
    """Статус сервера."""
    name: str
    server_type: ServerType
    url: str
    is_online: bool
    last_check: datetime
    response_time: Optional[float] = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemAlert:
    """Системный алерт."""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ServerMonitor:
    """
    Мониторинг серверов.
    
    Серверы Гриши:
    - wg-easy (VPN)
    - 3x-ui (VPN panel)
    - Vitbon Max
    """
    
    def __init__(self):
        self.servers: List[Dict[str, Any]] = []
        self._init_default_servers()
    
    def _init_default_servers(self):
        """Инициализировать дефолтные серверы."""
        # WG-Easy
        self.add_server(
            name="wg-easy",
            server_type=ServerType.VPN_WG_EASY,
            url=os.getenv("WG_EASY_URL", "http://localhost:51821"),
            check_interval=300
        )
        
        # 3X-UI
        self.add_server(
            name="3x-ui",
            server_type=ServerType.VPN_3X_UI,
            url=os.getenv("3X_UI_URL", "http://localhost:2053"),
            check_interval=300
        )
        
        # Vitbon
        self.add_server(
            name="vitbon",
            server_type=ServerType.VITBON,
            url=os.getenv("VITBON_URL", "http://localhost:8080"),
            check_interval=300
        )
    
    def add_server(
        self,
        name: str,
        server_type: ServerType,
        url: str,
        check_interval: int = 300
    ):
        """Добавить сервер для мониторинга."""
        self.servers.append({
            "name": name,
            "type": server_type,
            "url": url,
            "check_interval": check_interval,
            "last_status": None,
            "last_check": None
        })
    
    def remove_server(self, name: str):
        """Удалить сервер."""
        self.servers = [s for s in self.servers if s["name"] != name]
    
    def check_server(self, server: Dict[str, Any]) -> ServerStatus:
        """Проверить один сервер."""
        import urllib.request
        import urllib.error
        
        name = server["name"]
        url = server["url"]
        
        start_time = time.time()
        
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Eva/1.0"}
            )
            
            response = urllib.request.urlopen(req, timeout=5)
            response_time = (time.time() - start_time) * 1000  # ms
            
            return ServerStatus(
                name=name,
                server_type=server["type"],
                url=url,
                is_online=True,
                last_check=datetime.now(),
                response_time=response_time
            )
        
        except urllib.error.URLError as e:
            return ServerStatus(
                name=name,
                server_type=server["type"],
                url=url,
                is_online=False,
                last_check=datetime.now(),
                error=str(e)
            )
        
        except Exception as e:
            return ServerStatus(
                name=name,
                server_type=server["type"],
                url=url,
                is_online=False,
                last_check=datetime.now(),
                error=str(e)
            )
    
    def check_all(self) -> List[ServerStatus]:
        """Проверить все серверы."""
        return [self.check_server(s) for s in self.servers]
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Получить сводку по всем серверам."""
        statuses = self.check_all()
        
        online = sum(1 for s in statuses if s.is_online)
        offline = len(statuses) - online
        
        return {
            "total": len(statuses),
            "online": online,
            "offline": offline,
            "servers": [
                {
                    "name": s.name,
                    "online": s.is_online,
                    "response_time": s.response_time,
                    "error": s.error
                }
                for s in statuses
            ]
        }


class SystemHealth:
    """
    Мониторинг здоровья системы.
    
    CPU, RAM, температура, диски.
    """
    
    def get_cpu_usage(self) -> float:
        """Получить использование CPU."""
        try:
            # Linux
            with open('/proc/loadavg', 'r') as f:
                load = float(f.read().split()[0])
            return min(load / os.cpu_count() * 100, 100) if os.cpu_count() else load * 25
        except Exception:
            return 0.0
    
    def get_memory_usage(self) -> Dict[str, float]:
        """Получить использование памяти."""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
            
            mem = {}
            for line in lines:
                parts = line.split()
                if len(parts) >= 2:
                    key = parts[0].rstrip(':')
                    value = int(parts[1]) / 1024  # KB to MB
                    mem[key] = value
            
            total = mem.get('MemTotal', 0)
            available = mem.get('MemAvailable', mem.get('MemFree', 0))
            used = total - available
            
            return {
                "total_mb": total,
                "used_mb": used,
                "available_mb": available,
                "percent": (used / total * 100) if total else 0
            }
        except Exception:
            return {"total_mb": 0, "used_mb": 0, "available_mb": 0, "percent": 0}
    
    def get_disk_usage(self, path: str = "/") -> Dict[str, float]:
        """Получить использование диска."""
        try:
            import shutil
            stat = shutil.disk_usage(path)
            
            total = stat.total / (1024**3)  # GB
            used = stat.used / (1024**3)
            free = stat.free / (1024**3)
            
            return {
                "total_gb": total,
                "used_gb": used,
                "free_gb": free,
                "percent": (used / total * 100) if total else 0
            }
        except Exception:
            return {"total_gb": 0, "used_gb": 0, "free_gb": 0, "percent": 0}
    
    def get_temperature(self) -> Optional[float]:
        """Получить температуру CPU (если доступно)."""
        temp_paths = [
            '/sys/class/thermal/thermal_zone0/temp',
            '/proc/acpi/thermal_zone/TZ0/temperature',
            '/sys/class/hwmon/hwmon0/temp1_input'
        ]
        
        for path in temp_paths:
            try:
                with open(path, 'r') as f:
                    temp = int(f.read().strip())
                    # Конвертируем в градусы
                    if temp > 1000:
                        temp = temp / 1000
                    return temp
            except Exception:
                continue
        
        return None
    
    def get_full_report(self) -> Dict[str, Any]:
        """Получить полный отчёт о системе."""
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": {
                "usage_percent": self.get_cpu_usage()
            },
            "memory": self.get_memory_usage(),
            "disk": self.get_disk_usage(),
            "temperature": self.get_temperature()
        }


class FileOperations:
    """
    Операции с файлами.
    
    Поиск, создание, редактирование.
    """
    
    def __init__(self, base_path: str = "."):
        self.base_path = base_path
    
    def find_files(
        self,
        pattern: str,
        path: Optional[str] = None,
        max_results: int = 50
    ) -> List[str]:
        """Найти файлы по паттерну."""
        import glob
        
        search_path = path or self.base_path
        search_pattern = f"{search_path}/**/{pattern}"
        
        files = glob.glob(search_pattern, recursive=True)
        return files[:max_results]
    
    def read_file(self, filepath: str) -> Optional[str]:
        """Прочитать файл."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            return None
    
    def write_file(self, filepath: str, content: str) -> bool:
        """Записать файл."""
        try:
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception:
            return False
    
    def search_in_files(
        self,
        query: str,
        path: Optional[str] = None,
        file_pattern: str = "*.py"
    ) -> List[Dict[str, Any]]:
        """Поиск текста в файлах."""
        import glob
        
        search_path = path or self.base_path
        results = []
        
        for filepath in glob.glob(f"{search_path}/**/{file_pattern}", recursive=True):
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                if query.lower() in content.lower():
                    lines = content.lower().split('\n')
                    matches = [
                        (i + 1, line)
                        for i, line in enumerate(lines)
                        if query.lower() in line
                    ]
                    
                    results.append({
                        "file": filepath,
                        "matches": len(matches),
                        "lines": matches[:5]  # Первые 5 совпадений
                    })
            except Exception:
                continue
        
        return results


# =============================================================================
# System Monitor — объединяет всё
# =============================================================================

class SystemMonitor:
    """
    Главный монитор системы.
    
    Использование:
        monitor = SystemMonitor()
        
        # Проверка серверов
        status = monitor.servers.get_status_summary()
        
        # Проверка здоровья
        health = monitor.health.get_full_report()
        
        # Поиск файлов
        files = monitor.files.find_files("*.py")
    """
    
    def __init__(self):
        self.servers = ServerMonitor()
        self.health = SystemHealth()
        self.files = FileOperations()
        
        self._alert_callbacks: List[Callable[[SystemAlert], None]] = []
        self._monitor_thread: Optional[threading.Thread] = None
        self._is_running = False
    
    def add_alert_callback(self, callback: Callable[[SystemAlert], None]):
        """Добавить callback для алертов."""
        self._alert_callbacks.append(callback)
    
    def _emit_alert(self, alert: SystemAlert):
        """Отправить алерт."""
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Alert callback error: {e}")
    
    def check_all(self) -> Dict[str, Any]:
        """Проверить всё."""
        server_status = self.servers.get_status_summary()
        system_health = self.health.get_full_report()
        
        # Проверяем на алерты
        for server in server_status.get("servers", []):
            if not server["online"]:
                self._emit_alert(SystemAlert(
                    level=AlertLevel.WARNING,
                    title=f"Server {server['name']} is offline",
                    message=f"Cannot reach {server['name']} at {server.get('url', 'unknown')}",
                    timestamp=datetime.now(),
                    source="server_monitor"
                ))
        
        # CPU alert
        if system_health["cpu"]["usage_percent"] > 90:
            self._emit_alert(SystemAlert(
                level=AlertLevel.WARNING,
                title="High CPU usage",
                message=f"CPU at {system_health['cpu']['usage_percent']:.1f}%",
                timestamp=datetime.now(),
                source="system_health"
            ))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "servers": server_status,
            "system": system_health
        }
    
    def start_monitoring(self, interval: int = 300):
        """Запустить фоновый мониторинг."""
        if self._is_running:
            return
        
        self._is_running = True
        
        def loop():
            while self._is_running:
                self.check_all()
                time.sleep(interval)
        
        self._monitor_thread = threading.Thread(target=loop, daemon=True)
        self._monitor_thread.start()
    
    def stop_monitoring(self):
        """Остановить мониторинг."""
        self._is_running = False


# =============================================================================
# Global instance
# =============================================================================

_system_monitor: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get or create global system monitor instance."""
    global _system_monitor
    if _system_monitor is None:
        _system_monitor = SystemMonitor()
    return _system_monitor


# Тест
if __name__ == "__main__":
    print("=== System Integration Test ===\n")
    
    monitor = get_system_monitor()
    
    # System health
    print("📊 System Health:")
    health = monitor.health.get_full_report()
    print(f"   CPU: {health['cpu']['usage_percent']:.1f}%")
    print(f"   RAM: {health['memory']['percent']:.1f}%")
    print(f"   Disk: {health['disk']['percent']:.1f}%")
    
    if health.get('temperature'):
        print(f"   Temp: {health['temperature']}°C")
    
    print()
    
    # Server status
    print("🖥️ Server Status:")
    server_status = monitor.servers.get_status_summary()
    print(f"   Total: {server_status['total']}")
    print(f"   Online: {server_status['online']}")
    print(f"   Offline: {server_status['offline']}")
    
    print()
    
    # File operations demo
    print("📁 File Operations:")
    py_files = monitor.files.find_files("*.py", path=".")
    print(f"   Found {len(py_files)} Python files")
    
    print("\n✅ System integration ready")