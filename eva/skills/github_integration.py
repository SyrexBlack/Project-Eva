"""
Eva's GitHub Integration

Мониторинг репозиториев и активности на GitHub.
Гриша всегда будет в курсе своих проектов!

Возможности:
- Мониторинг репозиториев (stars, commits, issues)
- Отслеживание новых коммитов
- Проверка CI/CD статуса
- Интеграция с Projects и Issues

.env:
GITHUB_TOKEN=your_token_here
GITHUB_USERNAME=your_username
"""

import os
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class ActivityType(Enum):
    """Типы активности."""
    PUSH = "push"
    PULL_REQUEST = "pull_request"
    ISSUE = "issue"
    STAR = "star"
    FORK = "fork"
    RELEASE = "release"


@dataclass
class Repository:
    """Репозиторий."""
    name: str
    full_name: str
    description: str
    url: str
    stars: int
    forks: int
    language: str
    updated_at: datetime
    default_branch: str = "main"
    is_private: bool = False
    
    def format_summary(self) -> str:
        """Форматировать как краткую сводку."""
        lang_emoji = {
            "Python": "🐍",
            "JavaScript": "📜",
            "TypeScript": "🔷",
            "Rust": "🦀",
            "Go": "🐹",
        }.get(self.language, "📁")
        
        return (
            f"{lang_emoji} *{self.name}*\n"
            f"   ⭐ {self.stars} | 🍴 {self.forks}\n"
            f"   {self.description[:50]}..." if self.description else ""
        )


@dataclass
class Commit:
    """Коммит."""
    sha: str
    message: str
    author: str
    timestamp: datetime
    url: str
    
    def format_short(self) -> str:
        """Краткий формат."""
        short_sha = self.sha[:7]
        msg = self.message.split('\n')[0][:50]
        return f"`{short_sha}` {msg} — {self.author}"


@dataclass
class Activity:
    """Активность на GitHub."""
    activity_type: ActivityType
    repo_name: str
    description: str
    timestamp: datetime
    url: str = ""


class GitHubClient:
    """
    Eva's GitHub Client.
    
    Использование:
        github = GitHubClient()
        
        # Получить репозитории
        repos = github.get_repos()
        
        # Получить коммиты
        commits = github.get_recent_commits("repo-name")
        
        # Проверить активность
        activity = github.get_activity(days=7)
    """
    
    def __init__(self, token: Optional[str] = None, username: Optional[str] = None):
        """
        Инициализировать клиент.
        
        Args:
            token: GitHub token (или GITHUB_TOKEN)
            username: Username (или GITHUB_USERNAME)
        """
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        self.username = username or os.getenv("GITHUB_USERNAME", "")
        self._cache: Dict[str, Any] = {}
        self._cache_time: Dict[str, datetime] = {}
    
    def _get_headers(self) -> Dict[str, str]:
        """Получить заголовки для API."""
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Eva-AI-Companion"
        }
        if self.token:
            headers["Authorization"] = f"token {self.token}"
        return headers
    
    def _get_cached(self, key: str, ttl_minutes: int = 5) -> Optional[Any]:
        """Получить из кэша."""
        if key in self._cache:
            if key in self._cache_time:
                if datetime.now() - self._cache_time[key] < timedelta(minutes=ttl_minutes):
                    return self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """Сохранить в кэш."""
        self._cache[key] = data
        self._cache_time[key] = datetime.now()
    
    def get_repos(self, per_page: int = 30) -> List[Repository]:
        """
        Получить все репозитории пользователя.
        
        Args:
            per_page: Количество на странице
            
        Returns:
            Список репозиториев
        """
        cache_key = f"repos_{self.username}"
        cached = self._get_cached(cache_key, ttl_minutes=15)
        if cached:
            return cached
        
        if not self.username:
            return []
        
        try:
            import requests
            
            url = f"https://api.github.com/users/{self.username}/repos"
            params = {"per_page": per_page, "sort": "updated"}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            
            if response.status_code == 200:
                repos = []
                for data in response.json():
                    repos.append(Repository(
                        name=data["name"],
                        full_name=data["full_name"],
                        description=data.get("description", ""),
                        url=data["html_url"],
                        stars=data["stargazers_count"],
                        forks=data["forks_count"],
                        language=data.get("language", "Unknown"),
                        updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                        default_branch=data.get("default_branch", "main"),
                        is_private=data.get("private", False)
                    ))
                
                self._set_cache(cache_key, repos)
                return repos
        
        except Exception as e:
            print(f"GitHub API error: {e}")
        
        return []
    
    def get_repo(self, repo_name: str) -> Optional[Repository]:
        """Получить конкретный репозиторий."""
        if not self.username:
            return None
        
        cache_key = f"repo_{self.username}/{repo_name}"
        cached = self._get_cached(cache_key, ttl_minutes=10)
        if cached:
            return cached
        
        try:
            import requests
            
            url = f"https://api.github.com/repos/{self.username}/{repo_name}"
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                repo = Repository(
                    name=data["name"],
                    full_name=data["full_name"],
                    description=data.get("description", ""),
                    url=data["html_url"],
                    stars=data["stargazers_count"],
                    forks=data["forks_count"],
                    language=data.get("language", "Unknown"),
                    updated_at=datetime.fromisoformat(data["updated_at"].replace("Z", "+00:00")),
                    default_branch=data.get("default_branch", "main"),
                    is_private=data.get("private", False)
                )
                self._set_cache(cache_key, repo)
                return repo
        
        except Exception:
            pass
        
        return None
    
    def get_recent_commits(
        self,
        repo_name: str,
        branch: str = "main",
        per_page: int = 10
    ) -> List[Commit]:
        """Получить недавние коммиты."""
        if not self.username:
            return []
        
        try:
            import requests
            
            url = f"https://api.github.com/repos/{self.username}/{repo_name}/commits"
            params = {"sha": branch, "per_page": per_page}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            
            if response.status_code == 200:
                commits = []
                for data in response.json():
                    commits.append(Commit(
                        sha=data["sha"],
                        message=data["commit"]["message"],
                        author=data["commit"]["author"]["name"],
                        timestamp=datetime.fromisoformat(
                            data["commit"]["author"]["date"].replace("Z", "+00:00")
                        ),
                        url=data["html_url"]
                    ))
                return commits
        
        except Exception:
            pass
        
        return []
    
    def get_activity(self, days: int = 7) -> List[Activity]:
        """
        Получить активность за период.
        
        Args:
            days: Количество дней
            
        Returns:
            Список активностей
        """
        if not self.username:
            return []
        
        try:
            import requests
            
            # Используем events API
            url = f"https://api.github.com/users/{self.username}/events"
            params = {"per_page": 100}
            
            response = requests.get(url, headers=self._get_headers(), params=params, timeout=10)
            
            if response.status_code == 200:
                activities = []
                cutoff = datetime.now() - timedelta(days=days)
                
                for data in response.json():
                    created_at = datetime.fromisoformat(data["created_at"].replace("Z", "+00:00"))
                    
                    if created_at < cutoff:
                        continue
                    
                    activity_type = ActivityType.PUSH
                    description = ""
                    
                    if data["type"] == "PushEvent":
                        activity_type = ActivityType.PUSH
                        commits = data["payload"].get("commits", [])
                        count = len(commits)
                        description = f"Pushed {count} commit(s)"
                    elif data["type"] == "PullRequestEvent":
                        activity_type = ActivityType.PULL_REQUEST
                        pr = data["payload"].get("pull_request", {})
                        description = f"{pr.get('action', '')} PR: {pr.get('title', '')}"
                    elif data["type"] == "IssuesEvent":
                        activity_type = ActivityType.ISSUE
                        issue = data["payload"].get("issue", {})
                        description = f"{data['payload'].get('action', '')} issue: {issue.get('title', '')}"
                    elif data["type"] == "WatchEvent":
                        activity_type = ActivityType.STAR
                        description = "Starred repository"
                    elif data["type"] == "ForkEvent":
                        activity_type = ActivityType.FORK
                        description = f"Forked to {data['payload'].get('forkee', {}).get('full_name', '')}"
                    elif data["type"] == "ReleaseEvent":
                        activity_type = ActivityType.RELEASE
                        release = data["payload"].get("release", {})
                        description = f"Released {release.get('tag_name', '')}"
                    
                    activities.append(Activity(
                        activity_type=activity_type,
                        repo_name=data["repo"]["name"],
                        description=description,
                        timestamp=created_at,
                        url=data.get("repo", {}).get("url", "")
                    ))
                
                return activities
        
        except Exception:
            pass
        
        return []
    
    def get_status_summary(self) -> str:
        """Получить сводку статуса."""
        repos = self.get_repos()
        
        if not repos:
            return "⚠️ No repositories found or GitHub not configured"
        
        total_stars = sum(r.stars for r in repos)
        total_forks = sum(r.forks for r in repos)
        recent = [r for r in repos if datetime.now() - r.updated_at < timedelta(days=7)]
        
        lines = [
            f"📊 *GitHub: {self.username}*",
            f"   Repos: {len(repos)} | ⭐ {total_stars} | 🍴 {total_forks}",
        ]
        
        if recent:
            lines.append(f"\n   🆕 Updated recently ({len(recent)}):")
            for r in recent[:3]:
                days_ago = (datetime.now() - r.updated_at).days
                lines.append(f"   • {r.name} ({days_ago}d ago)")
        
        return "\n".join(lines)


# =============================================================================
# Project Monitor — для мониторинга конкретных проектов
# =============================================================================

class ProjectMonitor:
    """
    Мониторинг важных проектов.
    
    Отслеживает изменения в ключевых репозиториях.
    """
    
    def __init__(self, github_client: Optional[GitHubClient] = None):
        self.github = github_client or GitHubClient()
        self.watched_repos: List[str] = []
        self.last_check: Dict[str, datetime] = {}
    
    def watch(self, repo_name: str):
        """Добавить репозиторий в отслеживаемые."""
        if repo_name not in self.watched_repos:
            self.watched_repos.append(repo_name)
    
    def unwatch(self, repo_name: str):
        """Убрать из отслеживаемых."""
        self.watched_repos = [r for r in self.watched_repos if r != repo_name]
    
    def check_updates(self) -> Dict[str, List[Commit]]:
        """
        Проверить обновления во всех отслеживаемых репозиториях.
        
        Returns:
            Словарь {repo_name: [commits]}
        """
        updates = {}
        
        for repo_name in self.watched_repos:
            commits = self.github.get_recent_commits(repo_name)
            
            # Фильтруем новые коммиты
            if repo_name in self.last_check:
                cutoff = self.last_check[repo_name]
                new_commits = [c for c in commits if c.timestamp > cutoff]
            else:
                new_commits = commits[:3]  # Первые 3 если первый запуск
            
            if new_commits:
                updates[repo_name] = new_commits
            
            if commits:
                self.last_check[repo_name] = commits[0].timestamp
        
        return updates
    
    def format_updates(self, updates: Dict[str, List[Commit]]) -> str:
        """Форматировать обновления для отправки."""
        if not updates:
            return "✅ Нет новых обновлений в отслеживаемых проектах"
        
        lines = ["🔔 *Обновления в проектах*", ""]
        
        for repo_name, commits in updates.items():
            lines.append(f"📁 *{repo_name}*")
            for commit in commits[:3]:
                lines.append(f"   • {commit.format_short()}")
            lines.append("")
        
        return "\n".join(lines)


# =============================================================================
# Singleton accessor
# =============================================================================

_github_client: Optional[GitHubClient] = None
_project_monitor: Optional[ProjectMonitor] = None


def get_github_client() -> GitHubClient:
    """Get or create global GitHub client."""
    global _github_client
    if _github_client is None:
        _github_client = GitHubClient()
    return _github_client


def get_project_monitor() -> ProjectMonitor:
    """Get or create global project monitor."""
    global _project_monitor
    if _project_monitor is None:
        _project_monitor = ProjectMonitor(get_github_client())
    return _project_monitor


# =============================================================================
# Пример использования
# =============================================================================

if __name__ == "__main__":
    print("=== GitHub Integration ===\n")
    
    github = get_github_client()
    
    # Проверяем конфигурацию
    if not github.username:
        print("⚠️ Set GITHUB_USERNAME in .env")
        print("   Also set GITHUB_TOKEN for private repos\n")
    else:
        print(f"✅ Configured for: {github.username}")
        print(f"   {github.get_status_summary()}\n")
        
        # Добавляем проекты для мониторинга
        monitor = get_project_monitor()
        monitor.watch("Project-Eva")  # Добавь свои проекты
        
        print("📋 Use monitor.watch('repo-name') to track projects")


# =============================================================================
# TODO: Добавить интеграцию с GitHub Projects API
# =============================================================================
# - Получение задач из Projects
# - Обновление статуса задач
# - Создание issue
# - Комментирование PRs
# =============================================================================