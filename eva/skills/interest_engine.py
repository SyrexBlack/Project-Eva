"""
Eva's Interest Engine

Proactive information monitoring for Grisha's interests.
Eva watches for relevant news, updates, and shares what matters.

Features:
- Interest tracking (tech, gaming, crypto, etc.)
- Periodic web searches
- Relevance scoring
- Proactive sharing

Usage:
    engine = InterestEngine()
    engine.add_interest("Claude AI", priority=0.8)
    engine.add_interest("LoL esports", priority=0.7)
    
    # Check for updates
    news = engine.check_updates()
    if news:
        eva.share(news)
"""

import os
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import threading


class InterestCategory(Enum):
    """Categories of interests."""
    TECH = "tech"
    GAMING = "gaming"
    CRYPTO = "crypto"
    WORK = "work"
    NEWS = "news"
    PERSONAL = "personal"


@dataclass
class Interest:
    """An interest topic to monitor."""
    topic: str
    category: InterestCategory
    priority: float  # 0.0 - 1.0
    last_check: Optional[datetime] = None
    last_found: Optional[datetime] = None
    last_content: Optional[str] = None
    check_interval_hours: int = 6
    enabled: bool = True
    
    def should_check(self) -> bool:
        """Check if it's time to refresh this interest."""
        if not self.enabled:
            return False
        if self.last_check is None:
            return True
        
        hours_since = (datetime.now() - self.last_check).total_seconds() / 3600
        return hours_since >= self.check_interval_hours


@dataclass 
class NewsItem:
    """A news item found for an interest."""
    title: str
    summary: str
    url: Optional[str] = None
    interest_topic: str = ""
    found_at: datetime = field(default_factory=datetime.now)
    relevance_score: float = 0.5
    shared: bool = False


class InterestEngine:
    """
    Eva's proactive interest monitoring.
    
    Monitors topics Grisha cares about and shares relevant updates.
    Runs in background, checking periodically.
    """
    
    def __init__(
        self,
        check_interval_minutes: int = 30,
        max_items_per_check: int = 5
    ):
        """
        Initialize Interest Engine.
        
        Args:
            check_interval_minutes: How often to check for updates
            max_items_per_check: Max news items to collect per check
        """
        self.check_interval = check_interval_minutes * 60
        self.max_items = max_items_per_check
        
        self.interests: Dict[str, Interest] = {}
        self.news_buffer: List[NewsItem] = []
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        # Initialize default interests
        self._init_default_interests()
    
    def _init_default_interests(self):
        """Set up default interests based on Grisha's profile."""
        # Tech
        self.add_interest("AI language models", InterestCategory.TECH, priority=0.9)
        self.add_interest("Claude Anthropic", InterestCategory.TECH, priority=0.8)
        self.add_interest("OpenAI GPT updates", InterestCategory.TECH, priority=0.7)
        
        # Gaming
        self.add_interest("League of Legends esports", InterestCategory.GAMING, priority=0.8)
        self.add_interest("Wild Rift updates", InterestCategory.GAMING, priority=0.6)
        
        # Crypto
        self.add_interest("Bitcoin news", InterestCategory.CRYPTO, priority=0.5)
        
        # Work
        self.add_interest("Python programming", InterestCategory.WORK, priority=0.7)
        self.add_interest("DevOps tools", InterestCategory.WORK, priority=0.6)
    
    def add_interest(
        self,
        topic: str,
        category: InterestCategory = InterestCategory.NEWS,
        priority: float = 0.5,
        check_interval_hours: int = 6
    ):
        """Add an interest to monitor."""
        self.interests[topic.lower()] = Interest(
            topic=topic,
            category=category,
            priority=priority,
            check_interval_hours=check_interval_hours
        )
    
    def remove_interest(self, topic: str):
        """Remove an interest."""
        self.interests.pop(topic.lower(), None)
    
    def update_priority(self, topic: str, priority: float):
        """Update interest priority."""
        if topic.lower() in self.interests:
            self.interests[topic.lower()].priority = priority
    
    def get_interests(self) -> List[Interest]:
        """Get all interests sorted by priority."""
        return sorted(
            self.interests.values(),
            key=lambda x: x.priority,
            reverse=True
        )
    
    def check_updates(self) -> List[NewsItem]:
        """
        Check all interests for updates.
        
        Returns:
            List of new relevant items found
        """
        new_items = []
        
        for topic, interest in self.interests.items():
            if not interest.should_check():
                continue
            
            # Update last check time
            interest.last_check = datetime.now()
            
            # Search for updates
            items = self._search_topic(interest)
            
            for item in items:
                # Check if this is actually new
                if interest.last_content and item.title in interest.last_content:
                    continue
                
                new_items.append(item)
                
                # Update last found
                if not interest.last_found:
                    interest.last_found = datetime.now()
                
                # Store content
                if interest.last_content:
                    interest.last_content = interest.last_content[:500] + item.title
                else:
                    interest.last_content = item.title
        
        # Sort by relevance
        new_items.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Limit results
        self.news_buffer.extend(new_items[:self.max_items])
        
        return new_items[:self.max_items]
    
    def _search_topic(self, interest: Interest) -> List[NewsItem]:
        """
        Search for updates on a topic.
        
        Note: This is a placeholder. In production, integrate with:
        - News API (NewsAPI, HackerNews, etc.)
        - RSS feeds
        - Web search via SerpAPI or similar
        
        For now, returns mock results to demonstrate the structure.
        """
        # TODO: Integrate with actual search API
        # For demo, return empty list (no news search in cron)
        return []
    
    def get_pending_news(self) -> List[NewsItem]:
        """Get news items that haven't been shared yet."""
        return [n for n in self.news_buffer if not n.shared]
    
    def mark_shared(self, news_item: NewsItem):
        """Mark a news item as shared."""
        for n in self.news_buffer:
            if n.title == news_item.title:
                n.shared = True
    
    def format_for_sharing(self, news: NewsItem) -> str:
        """Format a news item for sharing with Grisha."""
        if news.url:
            return f"📰 *{news.interest_topic}*: {news.title}\n{news.summary}\n🔗 {news.url}"
        return f"📰 *{news.interest_topic}*: {news.title}\n{news.summary}"
    
    def start_background_monitoring(self, callback=None):
        """
        Start background monitoring.
        
        Args:
            callback: Function to call when new news found
        """
        if self._running:
            return
        
        self._running = True
        self._callback = callback
        
        def monitoring_loop():
            while self._running:
                time.sleep(self.check_interval)
                
                if not self._running:
                    break
                
                news = self.check_updates()
                
                if news and self._callback:
                    for item in news:
                        self._callback(item)
        
        self._thread = threading.Thread(target=monitoring_loop, daemon=True)
        self._thread.start()
    
    def stop_background_monitoring(self):
        """Stop background monitoring."""
        self._running = False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics."""
        active = sum(1 for i in self.interests.values() if i.enabled)
        pending = len(self.get_pending_news())
        
        return {
            "total_interests": len(self.interests),
            "active_interests": active,
            "pending_news": pending,
            "check_interval_minutes": self.check_interval // 60
        }


# =============================================================================
# Singleton accessor
# =============================================================================

_engine_instance: Optional[InterestEngine] = None


def get_interest_engine() -> InterestEngine:
    """Get or create the global Interest Engine instance."""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = InterestEngine()
    return _engine_instance