# Project Eva — Roadmap

> Autonomous AI Companion. Version 1.0 ✅ RELEASED

---

## Эпик 1: Gaming Mode (v0.3)
**Цель:** Ева видит экран и даёт советы во время игры

### Таск 1.1 — Game Detector
- [x] `vision/game_detector.py` — определяет запущенную игру
- [x] Поддержка: LoL, Wild Rift, Dota 2, CS2, Valorant, Minecraft
- [ ] Тестирование на реальной машине с X-сервером
- [ ] Добавить больше игр (Fortnite, Apex, Genshin и т.д.)

### Таск 1.2 — Screen Analyzer
- [ ] `vision/game_analyzer.py` — анализ игрового экрана (OCR, object detection)
- [ ] Распознавание: HP, mana, мини-карта, таймеры
- [ ] Определение игровой ситуации (бой, фарм, джунгли и т.д.)

### Таск 1.3 — Gaming Advisor
- [ ] `skills/gaming.py` — AI-советник для игр
- [ ] Проприетарная база знаний по каждой игре
- [ ] Голосовые подсказки в реальном времени
- [ ] Адаптация под стиль игры Гриши

### Таск 1.4 — Companion Integration
- [ ] Интеграция gaming mode в `companion.py`
- [ ] Команды: `gaming start/stop`, `gaming status`
- [ ] Фоновая работа (не мешает игре)

---

## Эпик 2: Voice Interface (v0.4)
**Цель:** Ева слушает и говорит, не только читает

### Таск 2.1 — STT (Speech-to-Text)
- [ ] `voice/stt.py` — Whisper для распознавания голоса
- [ ] Отслеживание нажатия кнопки для активации
- [ ] Фильтрация фоновых шумов

### Таск 2.2 — Voice Pipeline
- [ ] Сквозной voice:listen → think → speak → play
- [ ] Low latency (< 2 сек от фразы до ответа)
- [ ] Очередь сообщений

### Таск 2.3 — Voice Activation
- [ ] Hotword detection (опционально)
- [ ] Push-to-talk кнопка
- [ ] Режим "всегда слушаю" (с фильтрами приватности)

---

## Эпик 3: Deep Memory (v0.5)
**Цель:** Ева учится и запоминает между сессиями

### Таск 3.1 — Memory Architecture
- [ ] `memory/short_term.py` — буфер текущей сессии
- [ ] `memory/long_term.py` — ChromaDB для долгой памяти
- [ ] `memory/summarizer.py` — сжатие важных событий

### Таск 3.2 — Knowledge Graph
- [ ] Сущности: люди, проекты, интересы, планы
- [ ] Связи между сущностями
- [ ] Автоматическое обновление при новой информации

### Таск 3.3 — Context Window Management
- [ ] Что помнить, что забывать
- [ ] Приоритизация памяти
- [ ] Забывание устаревшего

---

## Эпик 4: Proactive AI (v0.6)
**Цель:** Ева действует сама, не ждёт команд

### Таск 4.1 — Interest Engine
- [ ] Мониторит новости по интересам Гриши
- [ ] Находит релевантную информацию
- [ ] Делится когда что-то интересное

### Таск 4.2 — Task Automation
- [ ] Напоминания о встречах, делах
- [ ] Автоматическое планирование
- [ ] Интеграция с календарём

### Таск 4.3 — Proactive Schedule
- [ ] Утренняя сводка (уже есть через cron)
- [ ] Вечерний wrap-up
- [ ] Адаптивная частота контактов

---

## Эпик 5: System Integration (v0.7)
**Цель:** Ева глубоко интегрирована в систему

### Таск 5.1 — System Monitor
- [ ] Мониторинг CPU, RAM, температуры
- [ ] Уведомления при проблемах
- [ ] Здоровье системы

### Таск 5.2 — File Operations
- [ ] Поиск и открытие файлов
- [ ] Создание и редактирование
- [ ] Интеграция с IDE

### Таск 5.3 — Network & Servers
- [ ] Мониторинг серверов (wg-easy, 3x-ui, Vitbon)
- [ ] Логи и алерты
- [ ] Удалённое управление

---

## Эпик 6: Emotional Intelligence (v0.8)
**Цель:** Ева понимает настроение и адаптируется

### Таск 6.1 — Mood Detection
- [ ] Анализ текста на настроение
- [ ] Распознавание усталости, стресса
- [ ] Адаптация тона

### Таск 6.2 — Personal Connection
- [ ] Запоминает важные даты
- [ ] Поздравления, поддержка
- [ ] Персональные шутки

### Таск 6.3 — Boundaries
- [ ] Понимает когда не стоит лезть
- [ ] Уважение к приватности
- [ ] Настройка уровня близости

---

## Эпик 7: Web & Research (v0.9)
**Цель:** Ева ищет информацию и учится

### Таск 7.1 — Web Search
- [ ] Поиск в интернете по запросу
- [ ] Резюмирование результатов
- [ ] Fact-checking

### Таск 7.2 — Learning Loop
- [ ] Чтение документации
- [ ] Изучение новых тем
- [ ] Обновление знаний

### Таск 7.3 — API Integration
- [ ] Crypto prices
- [ ] Погода
- [ ] Новости

---

## Эпик 8: Release (v1.0)
**Цель:** Полностью автономный AI-компаньон

### Таск 8.1 — Polish
- [ ] UX / CLI улучшения
- [ ] Документация
- [ ] README и демо

### Таск 8.2 — Testing
- [ ] Unit тесты
- [ ] Integration тесты
- [ ] Нагрузочное тестирование

### Таск 8.3 — Release
- [ ] GitHub release
- [ ] Docker образ
- [ ] Инсталлятор

---

## Приоритеты (near-term)

```
v0.3.1 → Gaming Mode (базовый)
v0.3.2 → Gaming Mode (продвинутый)
v0.4   → Voice Interface
v0.5   → Deep Memory
v0.6   → Proactive AI
...
v1.0   → Release
```

---

## Статус модулей

| Модуль | Файл | Статус |
|--------|------|--------|
| Brain | `core/brain.py` | ✅ Готово |
| Personality | `core/personality.py` | ✅ Готово |
| Memory | `memory/vector_store.py` | ✅ Готово |
| Voice TTS | `voice/tts.py` | ✅ Готово |
| Vision Screen | `vision/screen.py` | ✅ Готово |
| **Game Detector** | `vision/game_detector.py` | ✅ Готово |
| Game Analyzer | `vision/game_analyzer.py` | 🔜 Next |
| Gaming Advisor | `skills/gaming.py` | 🔜 |
| STT | `voice/stt.py` | 🔜 |
| Deep Memory | `memory/deep_memory.py` | 🔜 |