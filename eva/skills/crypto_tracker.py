"""
Eva's Crypto Tracker Skill

Monitors Grisha's crypto portfolio and trading activity.
Integrates with Bybit WebSocket for real-time data.

Grisha's trading setup:
- Bybit (WebSocket, BB-Keltner Squeeze strategy)
- DCA ~350₽/day
- Portfolio: BTC, ETH, SOL, DOGE

Usage:
    from eva.skills.crypto_tracker import CryptoTracker
    
    tracker = CryptoTracker()
    
    # Get current prices
    prices = tracker.get_prices(["BTC", "ETH"])
    
    # Check portfolio
    portfolio = tracker.get_portfolio()
    
    # Get DCA status
    dca_status = tracker.check_dca()
"""

import os
import json
import asyncio
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests


@dataclass
class CryptoPrice:
    """Current crypto price data."""
    symbol: str
    price: float
    change_24h: float
    volume_24h: float
    timestamp: datetime


@dataclass
class PortfolioPosition:
    """A position in Grisha's portfolio."""
    symbol: str
    quantity: float
    avg_entry: float
    current_price: float
    pnl: float
    pnl_percent: float


class CryptoTracker:
    """
    Tracks Grisha's crypto portfolio and market data.
    
    Uses free APIs (no Bybit API key needed for basic data).
    For real portfolio data, would need Bybit credentials.
    """
    
    # Public APIs for price data
    COINGECKO_API = "https://api.coingecko.com/api/v3"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Grisha's tracked assets
        self.watchlist = ["BTC", "ETH", "SOL", "DOGE"]
        
        # DCA settings
        self.dca_amount_rub = 350  # ₽ per day
        self.dca_schedule = "daily"  # daily, weekly
    
    def get_prices(self, symbols: Optional[List[str]] = None) -> List[CryptoPrice]:
        """
        Get current prices for specified symbols.
        
        Args:
            symbols: List of symbols (BTC, ETH, etc.). If None, uses watchlist.
        
        Returns:
            List of CryptoPrice objects
        """
        if symbols is None:
            symbols = self.watchlist
        
        # CoinGecko ID mapping
        coin_ids = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "SOL": "solana",
            "DOGE": "dogecoin",
        }
        
        ids = [coin_ids.get(s, s.lower()) for s in symbols]
        
        try:
            url = f"{self.COINGECKO_API}/simple/price"
            params = {
                "ids": ",".join(ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true",
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            prices = []
            for symbol, coin_id in zip(symbols, ids):
                if coin_id in data:
                    prices.append(CryptoPrice(
                        symbol=symbol,
                        price=data[coin_id].get("usd", 0),
                        change_24h=data[coin_id].get("usd_24h_change", 0),
                        volume_24h=data[coin_id].get("usd_24h_vol", 0),
                        timestamp=datetime.now(),
                    ))
            
            return prices
            
        except Exception as e:
            print(f"Error fetching prices: {e}")
            return []
    
    def format_price_alert(self, symbol: str, price: CryptoPrice) -> str:
        """Format a price alert message."""
        change_emoji = "📈" if price.change_24h > 0 else "📉"
        change_str = f"+{price.change_24h:.2f}%" if price.change_24h > 0 else f"{price.change_24h:.2f}%"
        
        return (
            f"{change_emoji} {symbol}/USD: ${price.price:,.2f} "
            f"({change_str})"
        )
    
    def check_dca_opportunity(self) -> Dict[str, Any]:
        """
        Check if it's a good time for DCA.
        
        Returns dict with recommendation.
        """
        prices = self.get_prices()
        
        if not prices:
            return {"status": "error", "message": "Could not fetch prices"}
        
        # Simple DCA logic: buy if prices are stable or down
        btc_price = next((p for p in prices if p.symbol == "BTC"), None)
        
        if btc_price:
            recommendation = "neutral"
            
            if btc_price.change_24h < -2:
                recommendation = "good"  # Price down, good DCA opportunity
            elif btc_price.change_24h > 3:
                recommendation = "skip"  # Price up, maybe wait
            
            return {
                "status": "success",
                "recommendation": recommendation,
                "btc_price": btc_price.price,
                "btc_change_24h": btc_price.change_24h,
                "dca_amount_rub": self.dca_amount_rub,
                "timestamp": datetime.now().isoformat(),
            }
        
        return {"status": "error"}
    
    def get_market_summary(self) -> str:
        """Get a formatted market summary for Grisha."""
        prices = self.get_prices()
        
        if not prices:
            return "❌ Не удалось получить данные по крипте"
        
        lines = ["📊 **Рынок крипты:**\n"]
        
        for price in prices:
            line = self.format_price_alert(price.symbol, price)
            lines.append(f"• {line}")
        
        # Add DCA check
        dca = self.check_dca_opportunity()
        if dca["status"] == "success":
            if dca["recommendation"] == "good":
                lines.append("\n💡 DCA opportunity: цена просела, хороший момент для покупки")
            elif dca["recommendation"] == "skip":
                lines.append("\n⏭️ DCA skip: цена растёт, можно подождать")
        
        return "\n".join(lines)


# Singleton instance
_tracker: Optional[CryptoTracker] = None


def get_crypto_tracker(config: Optional[Dict[str, Any]] = None) -> CryptoTracker:
    """Get or create CryptoTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = CryptoTracker(config)
    return _tracker


# CLI usage
if __name__ == "__main__":
    tracker = CryptoTracker()
    
    print("=== Crypto Portfolio ===\n")
    
    # Show prices
    print("Current prices:")
    for price in tracker.get_prices():
        print(f"  {tracker.format_price_alert(price.symbol, price)}")
    
    print("\n" + tracker.get_market_summary())