"""
Eva's Health Tracker Skill

Tracks Grisha's health metrics:
- Weight: 120→111.9 kg (goal progress)
- Diet: ~1700 kcal/day
- Supplements: L-carnitine, caffeine, yohimbine, citrulline
- Recovery: post-surgery (fracture, November 19)

Usage:
    from eva.skills.health_tracker import HealthTracker
    
    tracker = HealthTracker()
    
    # Log weight
    tracker.log_weight(111.5)
    
    # Get progress
    progress = tracker.get_weight_progress()
    
    # Check supplements
    supplements = tracker.get_supplement_status()
"""

import os
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta


@dataclass
class WeightEntry:
    """A weight log entry."""
    date: str
    weight_kg: float
    note: Optional[str] = None


@dataclass
class SupplementDose:
    """A supplement dose."""
    name: str
    amount: str
    timing: str  # "morning", "pre-workout", "evening"
    notes: Optional[str] = None


class HealthTracker:
    """
    Tracks Grisha's health and fitness metrics.
    
    Key metrics:
    - Weight: starting 120kg, current ~111.9kg
    - Goal: continue to healthy weight
    - Diet: ~1700 kcal/day
    - Supplements: L-carnitine, caffeine, yohimbine, citrulline
    """
    
    # Data file
    DATA_DIR = os.path.expanduser("~/Project-Eva/data")
    WEIGHT_FILE = os.path.join(DATA_DIR, "health", "weight_log.json")
    FOOD_FILE = os.path.join(DATA_DIR, "health", "food_log.json")
    
    def __init__(self):
        os.makedirs(os.path.join(self.DATA_DIR, "health"), exist_ok=True)
        
        # Grisha's baseline data
        self.start_weight = 120.0  # kg
        self.goal_weight = 85.0  # kg (healthy weight)
        self.target_kcal = 1700
        
        # Supplements
        self.supplements = [
            SupplementDose("L-карнитин", "2г", "утро", "жиросжигание"),
            SupplementDose("Кофеин", "200мг", "пре-тренировка", "энергия"),
            SupplementDose("Йохимбин", "5мг", "пре-тренировка", "жиросжигание"),
            SupplementDose("Цитруллин", "6г", "пре-тренировка", "пампинг"),
        ]
    
    def log_weight(self, weight_kg: float, note: Optional[str] = None) -> WeightEntry:
        """Log today's weight."""
        entry = WeightEntry(
            date=datetime.now().strftime("%Y-%m-%d"),
            weight_kg=weight_kg,
            note=note,
        )
        
        # Save to file
        self._save_weight_entry(entry)
        
        return entry
    
    def _save_weight_entry(self, entry: WeightEntry):
        """Save weight entry to file."""
        entries = self._load_weight_log()
        entries.append(asdict(entry))
        
        with open(self.WEIGHT_FILE, "w") as f:
            json.dump(entries, f, indent=2)
    
    def _load_weight_log(self) -> List[Dict]:
        """Load weight log from file."""
        if os.path.exists(self.WEIGHT_FILE):
            with open(self.WEIGHT_FILE, "r") as f:
                return json.load(f)
        return []
    
    def get_weight_progress(self) -> Dict[str, Any]:
        """Get weight loss progress summary."""
        entries = self._load_weight_log()
        
        if not entries:
            return {
                "status": "no_data",
                "message": "Нет данных о весе. Начни с /log_weight",
            }
        
        # Get latest entry
        latest = entries[-1]
        current_weight = latest["weight_kg"]
        
        # Calculate progress
        lost = self.start_weight - current_weight
        remaining = current_weight - self.goal_weight
        progress_percent = (lost / (self.start_weight - self.goal_weight)) * 100
        
        # Days tracking
        first_entry = entries[0]
        start_date = datetime.fromisoformat(first_entry["date"])
        days_elapsed = (datetime.now() - start_date).days
        
        return {
            "status": "success",
            "current_weight": current_weight,
            "start_weight": self.start_weight,
            "goal_weight": self.goal_weight,
            "lost_kg": round(lost, 1),
            "remaining_kg": round(remaining, 1),
            "progress_percent": round(progress_percent, 1),
            "days_elapsed": days_elapsed,
            "last_updated": latest["date"],
        }
    
    def format_progress_report(self) -> str:
        """Format a nice progress report for Grisha."""
        progress = self.get_weight_progress()
        
        if progress["status"] == "no_data":
            return "❌ Нет данных о весе 😔\nДобавь через `tracker.log_weight(111.5)`"
        
        # Progress bar
        filled = int(progress["progress_percent"] / 5)
        bar = "🟢" * filled + "⚪️" * (20 - filled)
        
        lines = [
            "⚖️ **Вес:**",
            f"`{bar}`",
            f"Текущий: **{progress['current_weight']} кг**",
            f"Потеряно: **-{progress['lost_kg']} кг** ({progress['progress_percent']}% к цели)",
            f"Осталось: {progress['remaining_kg']} кг",
            f"Дней: {progress['days_elapsed']}",
        ]
        
        return "\n".join(lines)
    
    def get_supplement_status(self) -> str:
        """Get today's supplement status."""
        lines = [
            "💊 **Добавки сегодня:**\n",
        ]
        
        for supp in self.supplements:
            lines.append(f"• **{supp.name}** — {supp.amount} ({supp.timing})")
            if supp.notes:
                lines.append(f"  └ {supp.notes}")
        
        lines.append(f"\n📅 Цель: **{self.target_kcal} ккал/день**")
        
        return "\n".join(lines)
    
    def check_recovery_status(self) -> str:
        """Check post-surgery recovery status."""
        surgery_date = datetime(2024, 11, 19)
        days_since = (datetime.now() - surgery_date).days
        
        # Typical recovery for fracture with hardware: 12-16 weeks
        recovery_weeks = days_since // 7
        recovery_percent = min(100, (recovery_weeks / 14) * 100)
        
        lines = [
            "🏥 **Восстановление после операции:**",
            f"Дней прошло: **{days_since}** ({recovery_weeks} недель)",
            f"Прогресс: **{recovery_percent:.0f}%**",
        ]
        
        if recovery_percent < 50:
            lines.append("⚠️ Ещё рано для интенсивных нагрузок")
        elif recovery_percent < 100:
            lines.append("✅ Можно постепенно увеличивать активность")
        else:
            lines.append("🎉 Полное восстановление!")
        
        return "\n".join(lines)


# Singleton
_tracker: Optional[HealthTracker] = None


def get_health_tracker() -> HealthTracker:
    """Get or create HealthTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = HealthTracker()
    return _tracker


# CLI
if __name__ == "__main__":
    tracker = HealthTracker()
    
    print(tracker.format_progress_report())
    print("\n" + tracker.get_supplement_status())
    print("\n" + tracker.check_recovery_status())