"""
Eva's Web Search & Research

Eva can search the web and research topics:
- Web search (via API or fallback)
- Summarize results
- Fact-check claims
- Learn new things

Usage:
    search = WebSearch()
    
    results = search.search("Claude AI latest news")
    summary = search.summarize(results)
    
    fact = search.fact_check("Is Claude better than GPT-4?")
"""

import os
import json
import re
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote, urlencode


@dataclass
class SearchResult:
    """A single search result."""
    title: str
    url: str
    snippet: str
    source: str = ""
    published: Optional[str] = None
    relevance_score: float = 0.0
    
    def to_string(self) -> str:
        """Format as string."""
        return f"📄 {self.title}\n   {self.snippet[:150]}...\n   🔗 {self.url}"


@dataclass
class ResearchResult:
    """A research summary."""
    query: str
    summary: str
    key_points: List[str]
    sources: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def format(self) -> str:
        """Format research as readable text."""
        lines = [
            f"🔍 Research: {self.query}",
            "─" * 50,
            self.summary,
            "",
            "📌 Key Points:"
        ]
        
        for i, point in enumerate(self.key_points, 1):
            lines.append(f"   {i}. {point}")
        
        if self.sources:
            lines.append("")
            lines.append("📚 Sources:")
            for source in self.sources[:3]:
                lines.append(f"   - {source}")
        
        lines.append("─" * 50)
        
        return "\n".join(lines)


class WebSearch:
    """
    Eva's web search capabilities.
    
    Provides search, research, and fact-checking.
    Falls back to simple web scraping when APIs unavailable.
    """
    
    # User agent for requests
    USER_AGENT = "Mozilla/5.0 (compatible; Eva/1.0; AI Companion)"
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        max_results: int = 10
    ):
        """
        Initialize Web Search.
        
        Args:
            api_key: Optional API key for search service
            max_results: Maximum number of results to return
        """
        self.api_key = api_key or os.getenv("SEARCH_API_KEY", "")
        self.max_results = max_results
    
    def search(self, query: str, count: int = 5) -> List[SearchResult]:
        """
        Search the web.
        
        Args:
            query: Search query
            count: Number of results
            
        Returns:
            List of search results
        """
        # Try SerpAPI if available
        if self.api_key:
            return self._search_serpapi(query, count)
        
        # Try DuckDuckGo as fallback
        return self._search_duckduckgo(query, count)
    
    def _search_serpapi(self, query: str, count: int) -> List[SearchResult]:
        """Search using SerpAPI."""
        try:
            import requests
            
            params = {
                "q": query,
                "api_key": self.api_key,
                "engine": "google",
                "num": count
            }
            
            url = f"https://serpapi.com/search?{urlencode(params)}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data.get("organic_results", [])[:count]:
                    results.append(SearchResult(
                        title=item.get("title", ""),
                        url=item.get("link", ""),
                        snippet=item.get("snippet", ""),
                        source=item.get("source", "")
                    ))
                
                return results
            
        except Exception as e:
            print(f"SerpAPI search failed: {e}")
        
        return self._search_duckduckgo(query, count)
    
    def _search_duckduckgo(self, query: str, count: int) -> List[SearchResult]:
        """Search using DuckDuckGo HTML."""
        try:
            import requests
            
            url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
            headers = {"User-Agent": self.USER_AGENT}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                results = []
                
                # Parse HTML
                for match in re.finditer(
                    r'<a class="result__a" href="([^"]+)">([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]+)</a>',
                    response.text,
                    re.DOTALL
                ):
                    if len(results) >= count:
                        break
                    
                    results.append(SearchResult(
                        title=match.group(2).strip(),
                        url=match.group(1).strip(),
                        snippet=re.sub(r'<[^>]+>', '', match.group(3)).strip()
                    ))
                
                return results
            
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
        
        return []
    
    def research(self, query: str) -> ResearchResult:
        """
        Research a topic - search and summarize.
        
        Args:
            query: Research topic
            
        Returns:
            Research summary with key points
        """
        # Search for information
        results = self.search(query, count=5)
        
        if not results:
            return ResearchResult(
                query=query,
                summary="No results found.",
                key_points=[],
                sources=[]
            )
        
        # Extract key points from snippets
        key_points = []
        sources = []
        
        for result in results:
            if result.url:
                sources.append(result.url)
            
            # Extract facts from snippet
            facts = self._extract_facts(result.snippet)
            key_points.extend(facts)
        
        # Limit key points
        key_points = key_points[:5]
        
        # Create summary
        summary = f"Found {len(results)} sources about '{query}'. "
        if key_points:
            summary += "Key findings include: " + ". ".join(key_points[:3]) + "."
        
        return ResearchResult(
            query=query,
            summary=summary,
            key_points=key_points,
            sources=sources
        )
    
    def _extract_facts(self, text: str) -> List[str]:
        """Extract factual statements from text."""
        facts = []
        
        # Remove HTML
        text = re.sub(r'<[^>]+>', '', text)
        
        # Look for patterns like "X is Y", "X was Z", etc.
        patterns = [
            r'([A-Z][^.]+(?:is|was|are|were|has|had)[^.]+)',
            r'([A-Z][^.]+\d+[^.]+)',  # Numbers
            r'(?:According to|Sources say|Reports indicate)([^.]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if len(match) > 20 and len(match) < 200:
                    facts.append(match.strip())
        
        return facts[:3]  # Limit per source
    
    def fact_check(self, claim: str) -> Dict[str, Any]:
        """
        Fact-check a claim.
        
        Args:
            claim: Statement to fact-check
            
        Returns:
            Fact-check result
        """
        # Search for related information
        results = self.search(claim, count=3)
        
        if not results:
            return {
                "claim": claim,
                "verdict": "unverified",
                "confidence": 0.0,
                "sources": [],
                "explanation": "Not enough information to verify."
            }
        
        # Simple verification based on consensus
        snippets = [r.snippet.lower() for r in results]
        
        # Look for contradictory language
        contradicts = sum(1 for s in snippets if any(
            word in s for word in ["false", "wrong", "incorrect", "myth", "fake"]
        ))
        
        confirms = sum(1 for s in snippets if any(
            word in s for word in ["true", "correct", "accurate", "verified", "confirmed"]
        ))
        
        if contradicts > confirms:
            verdict = "false"
            confidence = contradicts / len(results)
        elif confirms > contradicts:
            verdict = "true"
            confidence = confirms / len(results)
        else:
            verdict = "unverified"
            confidence = 0.5
        
        return {
            "claim": claim,
            "verdict": verdict,
            "confidence": confidence,
            "sources": [r.url for r in results],
            "explanation": f"Based on {len(results)} sources. {'Conflicting' if contradicts and confirms else 'Consistent'} information found."
        }
    
    def get_news(self, topic: str = "AI", count: int = 5) -> List[SearchResult]:
        """Get latest news on a topic."""
        query = f"{topic} latest news"
        return self.search(query, count)
    
    def format_results(self, results: List[SearchResult]) -> str:
        """Format search results for display."""
        if not results:
            return "No results found."
        
        lines = ["🔍 Search Results:", "─" * 50]
        
        for i, result in enumerate(results, 1):
            lines.append(f"{i}. {result.title}")
            lines.append(f"   {result.snippet[:100]}...")
            lines.append(f"   🔗 {result.url}")
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# Singleton accessor
# =============================================================================

_search_instance: Optional[WebSearch] = None


def get_web_search() -> WebSearch:
    """Get or create the global Web Search instance."""
    global _search_instance
    if _search_instance is None:
        _search_instance = WebSearch()
    return _search_instance