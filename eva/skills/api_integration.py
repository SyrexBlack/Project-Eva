"""
Eva's API Integration

External APIs for:
- Weather
- News
- Crypto prices
- Time/Calendar

Usage:
    api = APIClient()
    
    weather = api.get_weather("Moscow")
    news = api.get_news(category="technology")
    btc_price = api.get_crypto_price("bitcoin")
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


@dataclass
class WeatherData:
    """Weather information."""
    city: str
    temperature: float
    feels_like: float
    description: str
    humidity: int
    wind_speed: float
    icon: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    
    def format(self) -> str:
        """Format weather as string."""
        icons = {
            "01d": "☀️", "01n": "🌙",
            "02d": "⛅", "02n": "☁️",
            "03d": "☁️", "03n": "☁️",
            "04d": "☁️", "04n": "☁️",
            "09d": "🌧️", "09n": "🌧️",
            "10d": "🌦️", "10n": "🌧️",
            "11d": "⛈️", "11n": "⛈️",
            "13d": "❄️", "13n": "❄️",
            "50d": "🌫️", "50n": "🌫️"
        }
        icon = icons.get(self.icon, "🌡️")
        
        return (
            f"{icon} *{self.city}*: {self.temperature:.0f}°C "
            f"(feels like {self.feels_like:.0f}°C)\n"
            f"   {self.description.capitalize()}, "
            f"humidity {self.humidity}%, wind {self.wind_speed:.1f} m/s"
        )


@dataclass
class CryptoPrice:
    """Cryptocurrency price."""
    symbol: str
    name: str
    price_usd: float
    change_24h: float
    market_cap: float
    timestamp: datetime = field(default_factory=datetime.now)
    
    def format(self) -> str:
        """Format price as string."""
        change_str = f"+{self.change_24h:.2f}%" if self.change_24h >= 0 else f"{self.change_24h:.2f}%"
        change_emoji = "📈" if self.change_24h >= 0 else "📉"
        
        return (
            f"{change_emoji} *{self.name}* ({self.symbol}): "
            f"${self.price_usd:,.2f} {change_str}"
        )


@dataclass
class NewsItem:
    """News article."""
    title: str
    description: str
    source: str
    url: str
    published_at: Optional[str] = None
    category: str = "general"
    
    def format(self) -> str:
        """Format news as string."""
        return f"📰 *{self.title}*\n   {self.description[:100]}...\n   🔗 {self.url}"


class APIClient:
    """
    Eva's external API integration.
    
    Provides weather, news, crypto, and time data.
    """
    
    def __init__(self):
        """Initialize API client."""
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: Dict[str, datetime] = {}
        
        # API keys from environment
        self.openweathermap_key = os.getenv("OPENWEATHERMAP_API_KEY", "")
        self.newsapi_key = os.getenv("NEWSAPI_KEY", "")
        self.coinmarketcap_key = os.getenv("COINMARKETCAP_API_KEY", "")
    
    def _get_cached(self, key: str, ttl_minutes: int = 15) -> Optional[Any]:
        """Get cached data if not expired."""
        if key not in self._cache:
            return None
        
        if key in self._cache_ttl:
            if datetime.now() - self._cache_ttl[key] > timedelta(minutes=ttl_minutes):
                return None
        
        return self._cache[key]
    
    def _set_cache(self, key: str, data: Any):
        """Cache data."""
        self._cache[key] = data
        self._cache_ttl[key] = datetime.now()
    
    def get_weather(self, city: str) -> Optional[WeatherData]:
        """
        Get weather for a city.
        
        Args:
            city: City name
            
        Returns:
            Weather data or None
        """
        cache_key = f"weather_{city}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        # Try OpenWeatherMap
        if self.openweathermap_key:
            return self._get_weather_openweathermap(city)
        
        # Fallback - simple mock
        return self._get_weather_mock(city)
    
    def _get_weather_openweathermap(self, city: str) -> Optional[WeatherData]:
        """Get weather via OpenWeatherMap API."""
        try:
            import requests
            
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": self.openweathermap_key,
                "units": "metric",
                "lang": "ru"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                weather = WeatherData(
                    city=data["name"],
                    temperature=data["main"]["temp"],
                    feels_like=data["main"]["feels_like"],
                    description=data["weather"][0]["description"],
                    humidity=data["main"]["humidity"],
                    wind_speed=data["wind"]["speed"],
                    icon=data["weather"][0]["icon"]
                )
                
                self._set_cache(f"weather_{city}", weather)
                return weather
            
        except Exception as e:
            print(f"Weather API failed: {e}")
        
        return self._get_weather_mock(city)
    
    def _get_weather_mock(self, city: str) -> Optional[WeatherData]:
        """Mock weather data."""
        return WeatherData(
            city=city,
            temperature=22.0,
            feels_like=20.0,
            description="clear sky",
            humidity=55,
            wind_speed=3.5,
            icon="01d"
        )
    
    def get_crypto_price(self, symbol: str) -> Optional[CryptoPrice]:
        """
        Get cryptocurrency price.
        
        Args:
            symbol: Crypto symbol (bitcoin, ethereum, etc.)
        """
        cache_key = f"crypto_{symbol}"
        cached = self._get_cached(cache_key, ttl_minutes=5)  # 5 min cache for crypto
        if cached:
            return cached
        
        # Try CoinMarketCap
        if self.coinmarketcap_key:
            return self._get_crypto_coinmarketcap(symbol)
        
        # Fallback - mock data
        return self._get_crypto_mock(symbol)
    
    def _get_crypto_coinmarketcap(self, symbol: str) -> Optional[CryptoPrice]:
        """Get crypto via CoinMarketCap API."""
        try:
            import requests
            
            url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"
            headers = {
                "X-CMC_PRO_API_KEY": self.coinmarketcap_key
            }
            params = {"symbol": symbol.upper()}
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                crypto_data = data["data"][symbol.upper()]
                
                price = CryptoPrice(
                    symbol=crypto_data["symbol"],
                    name=crypto_data["name"],
                    price_usd=crypto_data["quote"]["USD"]["price"],
                    change_24h=crypto_data["quote"]["USD"]["percent_change_24h"],
                    market_cap=crypto_data["quote"]["USD"]["market_cap"]
                )
                
                self._set_cache(f"crypto_{symbol}", price)
                return price
            
        except Exception as e:
            print(f"Crypto API failed: {e}")
        
        return self._get_crypto_mock(symbol)
    
    def _get_crypto_mock(self, symbol: str) -> Optional[CryptoPrice]:
        """Mock crypto data."""
        mock_prices = {
            "bitcoin": {"name": "Bitcoin", "price": 67500.0, "change": 2.5},
            "ethereum": {"name": "Ethereum", "price": 3450.0, "change": -1.2},
            "solana": {"name": "Solana", "price": 145.0, "change": 5.8},
        }
        
        symbol_lower = symbol.lower()
        if symbol_lower in mock_prices:
            data = mock_prices[symbol_lower]
            return CryptoPrice(
                symbol=symbol.upper(),
                name=data["name"],
                price_usd=data["price"],
                change_24h=data["change"],
                market_cap=0
            )
        
        return None
    
    def get_news(self, category: str = "technology", count: int = 5) -> List[NewsItem]:
        """
        Get news articles.
        
        Args:
            category: News category
            count: Number of articles
            
        Returns:
            List of news items
        """
        cache_key = f"news_{category}"
        cached = self._get_cached(cache_key, ttl_minutes=30)  # 30 min cache for news
        if cached:
            return cached
        
        # Try NewsAPI
        if self.newsapi_key:
            return self._get_news_newsapi(category, count)
        
        # Fallback - mock data
        return self._get_news_mock(category, count)
    
    def _get_news_newsapi(self, category: str, count: int) -> List[NewsItem]:
        """Get news via NewsAPI."""
        try:
            import requests
            
            url = "https://newsapi.org/v2/top-headlines"
            params = {
                "category": category,
                "pageSize": count,
                "apiKey": self.newsapi_key,
                "country": "us"
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                news = []
                
                for article in data.get("articles", []):
                    news.append(NewsItem(
                        title=article["title"],
                        description=article["description"] or "",
                        source=article["source"]["name"],
                        url=article["url"],
                        published_at=article["publishedAt"]
                    ))
                
                self._set_cache(f"news_{category}", news)
                return news
            
        except Exception as e:
            print(f"News API failed: {e}")
        
        return self._get_news_mock(category, count)
    
    def _get_news_mock(self, category: str, count: int) -> List[NewsItem]:
        """Mock news data."""
        mock_news = {
            "technology": [
                NewsItem(
                    title="AI Models Continue to Improve",
                    description="Latest developments in artificial intelligence show promising results...",
                    source="Tech News",
                    url="https://example.com/ai-news"
                ),
                NewsItem(
                    title="New Python Framework Released",
                    description="A new web framework promises better performance and easier syntax...",
                    source="Dev Weekly",
                    url="https://example.com/python-news"
                ),
            ],
            "general": [
                NewsItem(
                    title="Tech Industry Updates",
                    description="Major developments continue across the technology sector...",
                    source="News Daily",
                    url="https://example.com/news"
                ),
            ]
        }
        
        return mock_news.get(category, mock_news["general"])[:count]
    
    def get_time_info(self, timezone: str = "Europe/Moscow") -> Dict[str, Any]:
        """Get current time information."""
        now = datetime.now()
        
        return {
            "datetime": now.isoformat(),
            "timestamp": int(now.timestamp()),
            "timezone": timezone,
            "hour": now.hour,
            "minute": now.minute,
            "day_of_week": now.strftime("%A"),
            "is_business_hours": 9 <= now.hour <= 18,
            "is_weekend": now.weekday() >= 5
        }
    
    def format_summary(self) -> str:
        """Format all API data as summary."""
        lines = ["📊 API Integration Summary", "─" * 40]
        
        # Weather
        weather = self.get_weather("Moscow")
        if weather:
            lines.append(weather.format())
        
        # Crypto
        btc = self.get_crypto_price("bitcoin")
        if btc:
            lines.append("")
            lines.append(btc.format())
        
        # Time
        time_info = self.get_time_info()
        lines.append("")
        lines.append(f"🕐 Time: {time_info['datetime']}")
        lines.append(f"   Day: {time_info['day_of_week']}")
        lines.append(f"   Business hours: {'Yes' if time_info['is_business_hours'] else 'No'}")
        
        lines.append("─" * 40)
        
        return "\n".join(lines)


# =============================================================================
# Singleton accessor
# =============================================================================

_api_instance: Optional[APIClient] = None


def get_api_client() -> APIClient:
    """Get or create the global API Client instance."""
    global _api_instance
    if _api_instance is None:
        _api_instance = APIClient()
    return _api_instance