"""
Eva's System Monitor

Monitors system health: CPU, RAM, temperature, disk, network.
Eva alerts Grisha when something needs attention.

Features:
- CPU usage tracking
- RAM monitoring
- Temperature checks (if available)
- Disk space warnings
- Process monitoring
- Service health checks

Usage:
    monitor = SystemMonitor()
    
    # One-time check
    health = monitor.check_health()
    if health['status'] != 'healthy':
        eva.alert(health)
    
    # Continuous monitoring
    monitor.start(callback=lambda alert: print(alert))
"""

import os
import time
import psutil
import threading
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class HealthStatus(Enum):
    """System health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class Alert:
    """A system alert."""
    component: str
    status: HealthStatus
    message: str
    value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_string(self) -> str:
        """Format alert as string."""
        emoji = {
            HealthStatus.HEALTHY: "✅",
            HealthStatus.WARNING: "⚠️",
            HealthStatus.CRITICAL: "🚨"
        }
        return f"{emoji[self.status]} *{self.component}*: {self.message} ({self.value:.1f})"


@dataclass
class SystemMetrics:
    """System metrics snapshot."""
    timestamp: datetime
    
    # CPU
    cpu_percent: float
    cpu_count: int
    
    # Memory
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    
    # Disk
    disk_percent: float
    disk_free_gb: float
    
    # Network
    network_sent_mb: float
    network_recv_mb: float
    
    # Temperature (if available)
    cpu_temp: Optional[float] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_percent": self.cpu_percent,
            "cpu_count": self.cpu_count,
            "memory_percent": self.memory_percent,
            "memory_used_gb": self.memory_used_gb,
            "memory_total_gb": self.memory_total_gb,
            "disk_percent": self.disk_percent,
            "disk_free_gb": self.disk_free_gb,
            "cpu_temp": self.cpu_temp
        }


class SystemMonitor:
    """
    Eva's system health monitor.
    
    Tracks CPU, RAM, disk, network, and temperature.
    Generates alerts when thresholds are exceeded.
    """
    
    # Thresholds
    CPU_WARNING = 80.0
    CPU_CRITICAL = 95.0
    
    MEMORY_WARNING = 80.0
    MEMORY_CRITICAL = 95.0
    
    DISK_WARNING = 85.0
    DISK_CRITICAL = 95.0
    
    TEMP_WARNING = 80.0
    TEMP_CRITICAL = 90.0
    
    def __init__(
        self,
        check_interval_seconds: int = 60,
        history_size: int = 60
    ):
        """
        Initialize System Monitor.
        
        Args:
            check_interval_seconds: How often to check
            history_size: Number of snapshots to keep
        """
        self.check_interval = check_interval_seconds
        self.history_size = history_size
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[Alert], None]] = None
        
        self.history: List[SystemMetrics] = []
        self.alerts: List[Alert] = []
        
        # Track previous network stats
        self._prev_net_io = None
    
    def check_health(self) -> Dict[str, Any]:
        """
        Perform a health check.
        
        Returns:
            Health status and any alerts
        """
        metrics = self.get_metrics()
        self.history.append(metrics)
        
        # Trim history
        if len(self.history) > self.history_size:
            self.history = self.history[-self.history_size:]
        
        # Generate alerts
        alerts = self._check_thresholds(metrics)
        self.alerts.extend(alerts)
        
        # Determine overall status
        statuses = [a.status for a in alerts]
        if HealthStatus.CRITICAL in statuses:
            overall = HealthStatus.CRITICAL
        elif HealthStatus.WARNING in statuses:
            overall = HealthStatus.WARNING
        else:
            overall = HealthStatus.HEALTHY
        
        return {
            "status": overall.value,
            "metrics": metrics.to_dict(),
            "alerts": [a.to_string() for a in alerts]
        }
    
    def get_metrics(self) -> SystemMetrics:
        """Get current system metrics."""
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory
        mem = psutil.virtual_memory()
        memory_percent = mem.percent
        memory_used_gb = mem.used / (1024 ** 3)
        memory_total_gb = mem.total / (1024 ** 3)
        
        # Disk
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        disk_free_gb = disk.free / (1024 ** 3)
        
        # Network
        net_io = psutil.net_io_counters()
        network_sent_mb = net_io.bytes_sent / (1024 ** 2)
        network_recv_mb = net_io.bytes_recv / (1024 ** 2)
        
        # Temperature
        cpu_temp = self._get_cpu_temp()
        
        return SystemMetrics(
            timestamp=datetime.now(),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            memory_percent=memory_percent,
            memory_used_gb=memory_used_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=disk_percent,
            disk_free_gb=disk_free_gb,
            network_sent_mb=network_sent_mb,
            network_recv_mb=network_recv_mb,
            cpu_temp=cpu_temp
        )
    
    def _get_cpu_temp(self) -> Optional[float]:
        """Get CPU temperature if available."""
        try:
            # Try psutil
            temps = psutil.sensors_temperatures()
            if temps:
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except Exception:
            pass
        
        # Try reading thermal zone
        try:
            for path in ['/sys/class/thermal/thermal_zone0/temp',
                         '/proc/acpi/thermal_zone/THM0/temperature']:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        temp_str = f.read().strip()
                        return float(temp_str) / 1000
        except Exception:
            pass
        
        return None
    
    def _check_thresholds(self, metrics: SystemMetrics) -> List[Alert]:
        """Check metrics against thresholds."""
        alerts = []
        
        # CPU
        if metrics.cpu_percent >= self.CPU_CRITICAL:
            alerts.append(Alert(
                component="CPU",
                status=HealthStatus.CRITICAL,
                message=f"CPU usage critical: {metrics.cpu_percent:.1f}%",
                value=metrics.cpu_percent,
                threshold=self.CPU_CRITICAL
            ))
        elif metrics.cpu_percent >= self.CPU_WARNING:
            alerts.append(Alert(
                component="CPU",
                status=HealthStatus.WARNING,
                message=f"CPU usage high: {metrics.cpu_percent:.1f}%",
                value=metrics.cpu_percent,
                threshold=self.CPU_WARNING
            ))
        
        # Memory
        if metrics.memory_percent >= self.MEMORY_CRITICAL:
            alerts.append(Alert(
                component="Memory",
                status=HealthStatus.CRITICAL,
                message=f"Memory critical: {metrics.memory_percent:.1f}%",
                value=metrics.memory_percent,
                threshold=self.MEMORY_CRITICAL
            ))
        elif metrics.memory_percent >= self.MEMORY_WARNING:
            alerts.append(Alert(
                component="Memory",
                status=HealthStatus.WARNING,
                message=f"Memory warning: {metrics.memory_percent:.1f}%",
                value=metrics.memory_percent,
                threshold=self.MEMORY_WARNING
            ))
        
        # Disk
        if metrics.disk_percent >= self.DISK_CRITICAL:
            alerts.append(Alert(
                component="Disk",
                status=HealthStatus.CRITICAL,
                message=f"Disk almost full: {metrics.disk_percent:.1f}%",
                value=metrics.disk_percent,
                threshold=self.DISK_CRITICAL
            ))
        elif metrics.disk_percent >= self.DISK_WARNING:
            alerts.append(Alert(
                component="Disk",
                status=HealthStatus.WARNING,
                message=f"Disk space low: {metrics.disk_percent:.1f}%",
                value=metrics.disk_percent,
                threshold=self.DISK_WARNING
            ))
        
        # Temperature
        if metrics.cpu_temp:
            if metrics.cpu_temp >= self.TEMP_CRITICAL:
                alerts.append(Alert(
                    component="Temperature",
                    status=HealthStatus.CRITICAL,
                    message=f"CPU temperature critical: {metrics.cpu_temp:.1f}°C",
                    value=metrics.cpu_temp,
                    threshold=self.TEMP_CRITICAL
                ))
            elif metrics.cpu_temp >= self.TEMP_WARNING:
                alerts.append(Alert(
                    component="Temperature",
                    status=HealthStatus.WARNING,
                    message=f"CPU temperature high: {metrics.cpu_temp:.1f}°C",
                    value=metrics.cpu_temp,
                    threshold=self.TEMP_WARNING
                ))
        
        return alerts
    
    def get_processes(self, limit: int = 10) -> List[Dict]:
        """Get top processes by CPU/Memory usage."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append({
                    'pid': proc.info['pid'],
                    'name': proc.info['name'],
                    'cpu': proc.info['cpu_percent'] or 0,
                    'memory': proc.info['memory_percent'] or 0
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        return processes[:limit]
    
    def start(self, callback: Optional[Callable[[Alert], None]] = None):
        """
        Start continuous monitoring.
        
        Args:
            callback: Function to call when alert is generated
        """
        if self._running:
            return
        
        self._running = True
        self._callback = callback
        
        def monitoring_loop():
            while self._running:
                health = self.check_health()
                
                if health['alerts'] and self._callback:
                    for alert_str in health['alerts']:
                        # Find the alert object
                        for alert in self.alerts[-10:]:
                            if alert_str.startswith(alert.component):
                                self._callback(alert)
                                break
                
                time.sleep(self.check_interval)
        
        self._thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop continuous monitoring."""
        self._running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        latest = self.history[-1] if self.history else None
        
        return {
            "running": self._running,
            "history_size": len(self.history),
            "total_alerts": len(self.alerts),
            "latest": latest.to_dict() if latest else None
        }
    
    def format_health_report(self) -> str:
        """Format a human-readable health report."""
        if not self.history:
            return "No data available yet."
        
        latest = self.history[-1]
        
        lines = [
            "💻 System Health Report",
            "─" * 40,
            f"🖥️  CPU: {latest.cpu_percent:.1f}% ({latest.cpu_count} cores)",
            f"🧠 Memory: {latest.memory_percent:.1f}% ({latest.memory_used_gb:.1f}/{latest.memory_total_gb:.1f} GB)",
            f"💾 Disk: {latest.disk_percent:.1f}% free ({latest.disk_free_gb:.1f} GB)",
        ]
        
        if latest.cpu_temp:
            lines.append(f"🌡️  Temperature: {latest.cpu_temp:.1f}°C")
        
        # Check for alerts
        recent_alerts = [a for a in self.alerts if (datetime.now() - a.timestamp).seconds < 300]
        if recent_alerts:
            lines.append("")
            lines.append("⚠️  Recent Alerts:")
            for alert in recent_alerts[:3]:
                lines.append(f"   {alert.to_string()}")
        
        lines.append("─" * 40)
        
        return "\n".join(lines)


# =============================================================================
# Singleton accessor
# =============================================================================

_monitor_instance: Optional[SystemMonitor] = None


def get_system_monitor() -> SystemMonitor:
    """Get or create the global System Monitor instance."""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SystemMonitor()
    return _monitor_instance