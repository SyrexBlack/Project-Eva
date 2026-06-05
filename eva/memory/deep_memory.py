"""
Eva's Deep Memory System

Многоуровневая память для AI-компаньона:
- Short-term: буфер текущей сессии
- Long-term: ChromaDB с автоматическим summarization
- Knowledge graph: связи между сущностями

Как это работает:
1. Каждое взаимодействие сохраняется в short-term
2. Периодически short-term сжимается и переносится в long-term
3. ChromaDB индексирует для быстрого поиска
4. Knowledge graph отслеживает связи (Гриша → Полина, работа → проекты и т.д.)
"""

import os
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

from dotenv import load_dotenv

load_dotenv()


class MemoryType(Enum):
    """Типы воспоминаний."""
    CONVERSATION = "conversation"
    FACT = "fact"
    EVENT = "event"
    PROJECT = "project"
    RELATIONSHIP = "relationship"
    PREFERENCE = "preference"
    LEARNED = "learned"


@dataclass
class MemoryEntry:
    """Единица памяти."""
    id: str
    content: str
    memory_type: MemoryType
    timestamp: datetime
    importance: float  # 0.0 - 1.0
    embeddings: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Для knowledge graph
    entities: List[str] = field(default_factory=list)  # Упомянутые сущности
    relations: Dict[str, str] = field(default_factory=dict)  # Связи


@dataclass
class Entity:
    """Сущность в knowledge graph."""
    name: str
    entity_type: str  # person, project, location, concept
    description: str
    first_seen: datetime
    last_seen: datetime
    importance: float
    attributes: Dict[str, Any] = field(default_factory=dict)


class ShortTermMemory:
    """
    Буфер памяти текущей сессии.
    
    Хранит последние N взаимодействий в RAM.
    Периодически сжимается и переносится в long-term.
    """
    
    def __init__(self, max_size: int = 100):
        """
        Args:
            max_size: Максимальное количество записей
        """
        self.max_size = max_size
        self.buffer: deque[MemoryEntry] = deque(maxlen=max_size)
        self.session_start = datetime.now()
    
    def add(self, entry: MemoryEntry):
        """Добавить запись в буфер."""
        self.buffer.append(entry)
    
    def get_recent(self, count: int = 10) -> List[MemoryEntry]:
        """Получить последние N записей."""
        return list(self.buffer)[-count:]
    
    def get_context(self, query: str, count: int = 5) -> str:
        """Получить контекст для запроса (последние записи)."""
        recent = self.get_recent(count)
        if not recent:
            return ""
        
        parts = []
        for entry in recent:
            time_str = entry.timestamp.strftime("%H:%M")
            parts.append(f"[{time_str}] {entry.content}")
        
        return "\n".join(parts)
    
    def clear(self):
        """Очистить буфер."""
        self.buffer.clear()
    
    def size(self) -> int:
        """Размер буфера."""
        return len(self.buffer)
    
    def to_list(self) -> List[Dict]:
        """Конвертировать в список для сериализации."""
        return [
            {
                "id": e.id,
                "content": e.content,
                "type": e.memory_type.value,
                "timestamp": e.timestamp.isoformat(),
                "importance": e.importance
            }
            for e in self.buffer
        ]


class LongTermMemory:
    """
    Долгосрочная память через ChromaDB.
    
    Автоматически индексирует и сжимает старые воспоминания.
    """
    
    def __init__(
        self,
        persist_path: str = "./data/chroma_db",
        summarization_threshold: int = 50
    ):
        """
        Args:
            persist_path: Путь для ChromaDB
            summarization_threshold: Сколько записей перед summarization
        """
        self.persist_path = persist_path
        self.summarization_threshold = summarization_threshold
        
        self._client = None
        self._collection = None
        self._pending_summaries: List[MemoryEntry] = []
    
    def _get_client(self):
        """Lazy load ChromaDB."""
        if self._client is None:
            import chromadb
            os.makedirs(self.persist_path, exist_ok=True)
            self._client = chromadb.PersistentClient(path=self.persist_path)
            self._collection = self._client.get_or_create_collection(
                name="eva_memories",
                metadata={"description": "Eva's long-term memories"}
            )
        return self._client
    
    def _get_collection(self):
        """Get or create collection."""
        self._get_client()
        return self._collection
    
    def add(self, entry: MemoryEntry):
        """Добавить воспоминание в долгосрочную память."""
        collection = self._get_collection()
        
        collection.add(
            ids=[entry.id],
            documents=[entry.content],
            metadatas=[{
                "type": entry.memory_type.value,
                "timestamp": entry.timestamp.isoformat(),
                "importance": entry.importance,
                "entities": ",".join(entry.entities)
            }]
        )
        
        # Проверяем необходимость summarization
        self._pending_summaries.append(entry)
        
        if len(self._pending_summaries) >= self.summarization_threshold:
            self._run_summarization()
    
    def search(self, query: str, count: int = 5) -> List[MemoryEntry]:
        """Поиск воспоминаний по запросу."""
        collection = self._get_collection()
        
        results = collection.query(
            query_texts=[query],
            n_results=count
        )
        
        entries = []
        if results["ids"]:
            for i, mem_id in enumerate(results["ids"][0]):
                metadata = results["metadatas"][0][i]
                entries.append(MemoryEntry(
                    id=mem_id,
                    content=results["documents"][0][i],
                    memory_type=MemoryType(metadata["type"]),
                    timestamp=datetime.fromisoformat(metadata["timestamp"]),
                    importance=metadata["importance"],
                    entities=metadata.get("entities", "").split(",") if metadata.get("entities") else []
                ))
        
        return entries
    
    def get_context_for(self, query: str, count: int = 5) -> str:
        """Получить контекст для AI — реlevантные воспоминания."""
        results = self.search(query, count)
        
        if not results:
            return ""
        
        parts = []
        for entry in results:
            time_str = entry.timestamp.strftime("%Y-%m-%d %H:%M")
            parts.append(f"[{time_str}] {entry.content}")
        
        return "\n---\n".join(parts)
    
    def _run_summarization(self):
        """Сжать группу старых воспоминаний в одно резюме."""
        if len(self._pending_summaries) < self.summarization_threshold:
            return
        
        # Берём старые записи
        old_entries = self._pending_summaries[:self.summarization_threshold // 2]
        self._pending_summaries = self._pending_summaries[self.summarization_threshold // 2:]
        
        # Создаём резюме
        summary_content = self._create_summary(old_entries)
        
        # Удаляем старые из ChromaDB
        collection = self._get_collection()
        old_ids = [e.id for e in old_entries]
        
        try:
            collection.delete(ids=old_ids)
        except Exception:
            pass  # Может уже удалено
        
        # Добавляем резюме
        summary_entry = MemoryEntry(
            id=f"summary_{int(time.time())}",
            content=summary_content,
            memory_type=MemoryType.LEARNED,
            timestamp=datetime.now(),
            importance=0.7,
            metadata={"is_summary": True}
        )
        self.add(summary_entry)
    
    def _create_summary(self, entries: List[MemoryEntry]) -> str:
        """Создать резюме из записей."""
        # Простое резюме — склеиваем самые важные
        sorted_entries = sorted(entries, key=lambda e: e.importance, reverse=True)
        
        content_parts = [e.content for e in sorted_entries[:10]]
        combined = "\n".join(content_parts)
        
        return f"[Сводка за период {entries[0].timestamp.strftime('%Y-%m-%d')}]: {combined[:500]}..."
    
    def count(self) -> int:
        """Количество воспоминаний в долгосрочной памяти."""
        collection = self._get_collection()
        return collection.count()
    
    def get_stats(self) -> dict:
        """Статистика памяти."""
        return {
            "total_memories": self.count(),
            "pending_summaries": len(self._pending_summaries),
            "last_update": datetime.now().isoformat()
        }


class KnowledgeGraph:
    """
    Граф знаний — связи между сущностями.
    
    Гриша → Полина (married)
    Гриша → ТетраСофт (works_at)
    ТетраСофт → монтажно-сервисный (department)
    """
    
    def __init__(self):
        self.entities: Dict[str, Entity] = {}
        self.relations: Dict[str, List[Tuple[str, str]]] = {}  # entity → [(related, relation)]
    
    def add_entity(self, name: str, entity_type: str, description: str = "", importance: float = 0.5):
        """Добавить сущность."""
        now = datetime.now()
        
        if name in self.entities:
            entity = self.entities[name]
            entity.last_seen = now
            entity.importance = max(entity.importance, importance)
            if description:
                entity.description = description
        else:
            self.entities[name] = Entity(
                name=name,
                entity_type=entity_type,
                description=description,
                first_seen=now,
                last_seen=now,
                importance=importance
            )
        
        # Добавляем в relations index
        if name not in self.relations:
            self.relations[name] = []
    
    def add_relation(self, entity1: str, relation: str, entity2: str):
        """Добавить связь между сущностями."""
        # Добавляем обе сущности если их нет
        self.add_entity(entity1, "unknown")
        self.add_entity(entity2, "unknown")
        
        # Добавляем связь
        self.relations[entity1].append((entity2, relation))
        self.relations[entity2].append((entity1, _inverse_relation(relation)))
    
    def get_entity(self, name: str) -> Optional[Entity]:
        """Получить сущность."""
        return self.entities.get(name)
    
    def get_related(self, entity: str, relation: Optional[str] = None) -> List[str]:
        """Получить связанные сущности."""
        if entity not in self.relations:
            return []
        
        if relation:
            return [
                e for e, r in self.relations[entity]
                if r == relation
            ]
        
        return [e for e, r in self.relations[entity]]
    
    def get_path(self, from_entity: str, to_entity: str, max_depth: int = 3) -> Optional[List[str]]:
        """Найти путь между сущностями (BFS)."""
        if from_entity == to_entity:
            return [from_entity]
        
        visited = {from_entity}
        queue = [(from_entity, [from_entity])]
        
        while queue:
            current, path = queue.pop(0)
            
            if len(path) > max_depth:
                continue
            
            for related, _ in self.relations.get(current, []):
                if related == to_entity:
                    return path + [to_entity]
                
                if related not in visited:
                    visited.add(related)
                    queue.append((related, path + [related]))
        
        return None
    
    def extract_entities(self, text: str) -> List[str]:
        """Извлечь сущности из текста (простой regex)."""
        import re
        
        # Ищем capitalized words
        entities = re.findall(r'\b[A-ZА-ЯЁ][a-zа-яё]+(?:\s+[A-ZА-ЯЁ][a-zа-яё]+)*\b', text)
        
        # Убираем дубликаты и короткие
        seen = set()
        unique = []
        for e in entities:
            if len(e) > 2 and e not in seen:
                seen.add(e)
                unique.append(e)
        
        return unique


def _inverse_relation(relation: str) -> str:
    """Получить обратную связь."""
    inverses = {
        "married_to": "married_to",
        "works_at": "employs",
        "lives_in": "location_of",
        "interested_in": "interests_of",
        "owns": "owned_by",
        "friend_of": "friend_of",
        "knows": "known_by"
    }
    return inverses.get(relation, relation)


# =============================================================================
# Deep Memory Manager
# =============================================================================

class DeepMemory:
    """
    Главный интерфейс к памяти.
    
    Объединяет short-term, long-term и knowledge graph.
    """
    
    def __init__(
        self,
        chroma_path: str = "./data/chroma_db",
        short_term_size: int = 100
    ):
        self.short_term = ShortTermMemory(max_size=short_term_size)
        self.long_term = LongTermMemory(persist_path=chroma_path)
        self.knowledge = KnowledgeGraph()
        
        self._entity_patterns = self._init_entity_patterns()
    
    def _init_entity_patterns(self) -> Dict[str, str]:
        """Инициализировать паттерны для извлечения сущностей."""
        return {
            "person": r'\b(?:Гриша|Ева|полина|Михаил|Егор|Кирилл)\b',
            "project": r'\b(?:VitbonGPT|Konoha|OpenClaw|Project-Eva)\b',
            "company": r'\b(?:ТетраСофт)\b',
        }
    
    def remember(
        self,
        content: str,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        importance: float = 0.5,
        metadata: Optional[Dict] = None
    ):
        """
        Запомнить информацию.
        
        Args:
            content: Что запомнить
            memory_type: Тип памяти
            importance: Важность (0.0 - 1.0)
            metadata: Дополнительные данные
        """
        import uuid
        
        entry = MemoryEntry(
            id=str(uuid.uuid4()),
            content=content,
            memory_type=memory_type,
            timestamp=datetime.now(),
            importance=importance,
            metadata=metadata or {},
            entities=self.knowledge.extract_entities(content)
        )
        
        # Добавляем в short-term
        self.short_term.add(entry)
        
        # Извлекаем и добавляем сущности в knowledge graph
        for entity_name in entry.entities:
            self.knowledge.add_entity(entity_name, "unknown", importance=importance)
        
        # Каждые N записей переносим в long-term
        if self.short_term.size() >= 10:
            self._flush_to_long_term()
    
    def _flush_to_long_term(self):
        """Перенести старые записи из short-term в long-term."""
        if self.short_term.size() < 10:
            return
        
        # Берём старые записи
        entries = self.short_term.get_recent(5)
        
        for entry in entries:
            self.long_term.add(entry)
        
        # Очищаем буфер (оставляем последние 5)
        # Simple approach: just keep last entries
        pass
    
    def get_context(self, query: str) -> str:
        """
        Получить контекст для запроса.
        
        Комбинирует short-term и long-term память.
        """
        parts = []
        
        # Short-term контекст
        short_context = self.short_term.get_context(query)
        if short_context:
            parts.append(f"[Недавние события]\n{short_context}")
        
        # Long-term контекст
        long_context = self.long_term.get_context_for(query)
        if long_context:
            parts.append(f"[Из памяти]\n{long_context}")
        
        return "\n\n".join(parts) if parts else ""
    
    def get_about(self, entity: str) -> Optional[str]:
        """Получить информацию о сущности."""
        entity_obj = self.knowledge.get_entity(entity)
        if not entity_obj:
            return None
        
        related = self.knowledge.get_related(entity)
        relations_str = ", ".join([f"{e} ({r})" for e, r in related]) if related else "nothing known"
        
        return f"{entity}: {entity_obj.description or 'No description'}\nRelated: {relations_str}"
    
    def learn_relation(self, entity1: str, relation: str, entity2: str):
        """Запомнить связь между сущностями."""
        self.knowledge.add_relation(entity1, relation, entity2)
        self.remember(
            f"{entity1} {relation} {entity2}",
            memory_type=MemoryType.RELATIONSHIP,
            importance=0.8
        )
    
    def get_stats(self) -> dict:
        """Статистика памяти."""
        return {
            "short_term_size": self.short_term.size(),
            "long_term_count": self.long_term.count(),
            "entities": len(self.knowledge.entities),
            "relations": sum(len(r) for r in self.knowledge.relations.values())
        }


# =============================================================================
# Global instance
# =============================================================================

_deep_memory: Optional[DeepMemory] = None


def get_deep_memory() -> DeepMemory:
    """Get or create global deep memory instance."""
    global _deep_memory
    if _deep_memory is None:
        _deep_memory = DeepMemory()
    return _deep_memory


# Тест
if __name__ == "__main__":
    print("=== Deep Memory Test ===\n")
    
    memory = DeepMemory()
    
    # Добавляем воспоминания
    memory.remember("Гриша работает в ТетраСофт", MemoryType.FACT, importance=0.8)
    memory.remember("Ева анализирует экран игры", MemoryType.CONVERSATION, importance=0.6)
    memory.remember("Полина — жена Гриши", MemoryType.FACT, importance=0.9)
    
    # Запоминаем связь
    memory.learn_relation("Гриша", "married_to", "Полина")
    memory.learn_relation("Гриша", "works_at", "ТетраСофт")
    
    print("✅ Added memories")
    print(f"📊 Stats: {memory.get_stats()}")
    print()
    
    # Запрос
    context = memory.get_context("Гриша")
    print(f"Context for 'Гриша':\n{context}")
    print()
    
    # Информация о сущности
    about = memory.get_about("Гриша")
    print(f"About 'Гриша':\n{about}")