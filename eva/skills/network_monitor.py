"""
Eva's Network & Servers Monitor

Monitors network connectivity and services:
- Ping checks to servers
- Service health (wg-easy, 3x-ui, Vitbon, etc.)
- Port availability
- DNS resolution
- Web service health checks

Usage:
    network = NetworkMonitor()
    
    # Check specific host
    result = network.ping("wg-easy.local")
    
    # Check service health
    services = network.check_services()
    if services['unhealthy']:
        eva.alert("Services down!")
    
    # Continuous monitoring
    network.start(callback=lambda alert: print(alert))
"""

import os
import time
import socket
import subprocess
import threading
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    UNKNOWN = "unknown"


@dataclass
class ServiceCheck:
    """Result of a service check."""
    name: str
    status: ServiceStatus
    latency_ms: Optional[float] = None
    message: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_string(self) -> str:
        """Format as string."""
        emoji = {
            ServiceStatus.HEALTHY: "✅",
            ServiceStatus.DEGRADED: "⚠️",
            ServiceStatus.DOWN: "❌",
            ServiceStatus.UNKNOWN: "❓"
        }
        
        if self.latency_ms is not None:
            return f"{emoji[self.status]} {self.name}: {self.message} ({self.latency_ms:.0f}ms)"
        return f"{emoji[self.status]} {self.name}: {self.message}"


@dataclass
class NetworkAlert:
    """A network alert."""
    service: str
    status: ServiceStatus
    message: str
    timestamp: datetime = field(default_factory=datetime.now)


class NetworkMonitor:
    """
    Eva's network and service monitor.
    
    Monitors network connectivity, server health, and services.
    """
    
    # Default services to monitor
    DEFAULT_SERVICES = [
        {"name": "Internet", "host": "8.8.8.8", "port": 53, "type": "ping"},
        {"name": "Cloudflare DNS", "host": "1.1.1.1", "port": 53, "type": "ping"},
        {"name": "OpenAI", "host": "api.openai.com", "port": 443, "type": "tcp"},
        {"name": "Anthropic", "host": "api.anthropic.com", "port": 443, "type": "tcp"},
    ]
    
    def __init__(
        self,
        check_interval_seconds: int = 300,  # 5 minutes
        timeout_seconds: int = 5
    ):
        """
        Initialize Network Monitor.
        
        Args:
            check_interval_seconds: How often to check
            timeout_seconds: Timeout for checks
        """
        self.check_interval = check_interval_seconds
        self.timeout = timeout_seconds
        
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._callback: Optional[Callable[[NetworkAlert], None]] = None
        
        self.services: List[Dict] = self.DEFAULT_SERVICES.copy()
        self.last_results: List[ServiceCheck] = []
        self.alerts: List[NetworkAlert] = []
    
    def add_service(
        self,
        name: str,
        host: str,
        port: int = 80,
        check_type: str = "tcp"
    ):
        """Add a service to monitor."""
        self.services.append({
            "name": name,
            "host": host,
            "port": port,
            "type": check_type
        })
    
    def remove_service(self, name: str):
        """Remove a service from monitoring."""
        self.services = [s for s in self.services if s["name"] != name]
    
    def ping(self, host: str, count: int = 1) -> Optional[float]:
        """
        Ping a host.
        
        Returns:
            Latency in ms or None if failed
        """
        try:
            cmd = ["ping", "-c", str(count), "-W", "2", host]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout + 2
            )
            
            if result.returncode == 0:
                # Parse output
                for line in result.stdout.split('\n'):
                    if 'time=' in line:
                        time_str = line.split('time=')[1].split()[0]
                        return float(time_str)
            return None
        except Exception:
            return None
    
    def check_port(self, host: str, port: int) -> bool:
        """Check if a port is open."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except Exception:
            return False
    
    def check_dns(self, hostname: str) -> bool:
        """Check if hostname resolves."""
        try:
            socket.gethostbyname(hostname)
            return True
        except socket.gaierror:
            return False
    
    def check_service(self, service: Dict) -> ServiceCheck:
        """Check a single service."""
        name = service["name"]
        host = service["host"]
        port = service["port"]
        check_type = service["type"]
        
        try:
            if check_type == "ping":
                latency = self.ping(host)
                if latency is not None:
                    return ServiceCheck(
                        name=name,
                        status=ServiceStatus.HEALTHY,
                        latency_ms=latency,
                        message=f"Response time {latency:.0f}ms"
                    )
                else:
                    return ServiceCheck(
                        name=name,
                        status=ServiceStatus.DOWN,
                        message="No response"
                    )
            
            elif check_type == "tcp":
                if self.check_port(host, port):
                    return ServiceCheck(
                        name=name,
                        status=ServiceStatus.HEALTHY,
                        message=f"Port {port} open"
                    )
                else:
                    return ServiceCheck(
                        name=name,
                        status=ServiceStatus.DOWN,
                        message=f"Port {port} closed"
                    )
            
            elif check_type == "dns":
                if self.check_dns(host):
                    return ServiceCheck(
                        name=name,
                        status=ServiceStatus.HEALTHY,
                        message="DNS resolved"
                    )
                else:
                    return ServiceCheck(
                        name=name,
                        status=ServiceStatus.DOWN,
                        message="DNS resolution failed"
                    )
            
            else:
                return ServiceCheck(
                    name=name,
                    status=ServiceStatus.UNKNOWN,
                    message=f"Unknown check type: {check_type}"
                )
        
        except Exception as e:
            return ServiceCheck(
                name=name,
                status=ServiceStatus.UNKNOWN,
                message=str(e)
            )
    
    def check_all_services(self) -> Dict[str, Any]:
        """
        Check all configured services.
        
        Returns:
            Results and any alerts
        """
        results = []
        for service in self.services:
            result = self.check_service(service)
            results.append(result)
            
            # Generate alerts for down services
            if result.status == ServiceStatus.DOWN:
                alert = NetworkAlert(
                    service=result.name,
                    status=ServiceStatus.DOWN,
                    message=result.message
                )
                self.alerts.append(alert)
                
                if self._callback:
                    self._callback(alert)
        
        self.last_results = results
        
        # Summary
        healthy = sum(1 for r in results if r.status == ServiceStatus.HEALTHY)
        down = sum(1 for r in results if r.status == ServiceStatus.DOWN)
        
        return {
            "total": len(results),
            "healthy": healthy,
            "down": down,
            "results": [r.to_string() for r in results]
        }
    
    def get_internet_speed(self) -> Optional[Dict]:
        """Estimate internet speed (simple ping-based)."""
        hosts = [("Google DNS", "8.8.8.8"), ("Cloudflare", "1.1.1.1")]
        latencies = []
        
        for name, host in hosts:
            latency = self.ping(host, count=3)
            if latency:
                latencies.append(latency)
        
        if latencies:
            avg = sum(latencies) / len(latencies)
            return {
                "average_latency_ms": avg,
                "hosts_tested": len(latencies)
            }
        
        return None
    
    def start(self, callback: Optional[Callable[[NetworkAlert], None]] = None):
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
                self.check_all_services()
                time.sleep(self.check_interval)
        
        self._thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop continuous monitoring."""
        self._running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get monitor statistics."""
        return {
            "services_monitored": len(self.services),
            "last_check": self.last_results[0].timestamp.isoformat() if self.last_results else None,
            "total_alerts": len(self.alerts),
            "running": self._running
        }
    
    def format_status_report(self) -> str:
        """Format a human-readable status report."""
        if not self.last_results:
            return "No data available yet. Run check_all_services() first."
        
        lines = [
            "🌐 Network Status Report",
            "─" * 40
        ]
        
        for result in self.last_results:
            lines.append(result.to_string())
        
        # Summary
        healthy = sum(1 for r in self.last_results if r.status == ServiceStatus.HEALTHY)
        down = sum(1 for r in self.last_results if r.status == ServiceStatus.DOWN)
        
        lines.append("─" * 40)
        lines.append(f"Summary: {healthy} healthy, {down} down")
        
        # Internet speed
        speed = self.get_internet_speed()
        if speed:
            lines.append(f"Latency: {speed['average_latency_ms']:.0f}ms average")
        
        lines.append("─" * 40)
        
        return "\n".join(lines)


# =============================================================================
# Singleton accessor
# =============================================================================

_network_instance: Optional[NetworkMonitor] = None


def get_network_monitor() -> NetworkMonitor:
    """Get or create the global Network Monitor instance."""
    global _network_instance
    if _network_instance is None:
        _network_instance = NetworkMonitor()
    return _network_instance