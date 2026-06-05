# Project Eva — Roadmap

> Autonomous AI Companion. Version 1.0 ✅ READY FOR RELEASE

---

## Эпик 1: Gaming Mode (v0.3) ✅ ЗАВЕРШЕНО
**Цель:** Ева видит экран и даёт советы во время игры

### Таск 1.1 — Game Detector
- [x] `vision/game_detector.py` — определяет запущенную игру
- [x] Поддержка: LoL, Wild Rift, Dota 2, CS2, Valorant, Minecraft
- [ ] Тестирование на реальной машине с X-сервером

### Таск 1.2 — Screen Analyzer
- [x] `vision/game_analyzer.py` — анализ игрового экрана (AI vision)
- [x] Определение игровой ситуации

### Таск 1.3 — Gaming Advisor
- [x] AI-советник для игр
- [x] Голосовые подсказки в реальном времени

### Таск 1.4 — Companion Integration ✅
- [x] Интеграция gaming mode в `companion.py`
- [x] Команды: `gaming start/stop/check/analyze/stats`
- [x] Фоновая работа (не мешает игре)

---

## Эпик 2: Voice Interface (v0.4) ✅ ЗАВЕРШЕНО
**Цель:** Ева слушает и говорит, не только читает

### Таск 2.1 — STT (Speech-to-Text) ✅
- [x] `voice/stt.py` — Whisper для распознавания голоса
- [x] Push-to-talk (держи пробел — говоришь)
- [x] Автоматическое распознавание с VAD
- [x] Поддержка: openai-whisper и faster-whisper

### Таск 2.2 — Voice Pipeline ✅
- [x] Сквозной voice: listen → think → speak → play
- [x] Интеграция в companion.py

### Таск 2.3 — Voice Activation ✅
- [x] Push-to-talk кнопка
- [x] CLI команда: `eva stt`

---

## Эпик 3: Deep Memory (v0.5) ✅ ЗАВЕРШЕНО
**Цель:** Ева учится и запоминает между сессиями

### Таск 3.1 — Memory Architecture ✅
- [x] `memory/short_term.py` — буфер текущей сессии
- [x] `memory/long_term.py` — ChromaDB для долгой памяти
- [x] `memory/deep_memory.py` — объединённый интерфейс

### Таск 3.2 — Knowledge Graph ✅
- [x] Сущности: люди, проекты, интересы
- [x] Связи между сущностями
- [x] Автоматическое извлечение из текста

### Таск 3.3 — Context Window Management ✅
- [x] Автоматическое сжатие старых воспоминаний
- [x] Приоритизация памяти

---

## Эпик 4: Proactive AI (v0.6) ✅ ЗАВЕРШЕНО
**Цель:** Ева действует сама, не ждёт команд

### Таск 4.1 — Interest Engine ✅
- [x] Мониторит интересы (AI, gaming, crypto, work)
- [x] Периодическая проверка
- [x] Приоритизация тем

### Таск 4.2 — Task Automation ✅
- [x] Создание и отслеживание задач
- [x] Напоминания с отложкой
- [x] Автоматическое определение задач из текста

### Таск 4.3 — Proactive Scheduler ✅
- [x] Утренняя сводка (9-11 AM)
- [x] Вечерний wrap-up (8-10 PM)
- [x] Напоминания о задачах (каждые 30 мин)
- [x] CLI команды: `eva proactive start/interests/tasks/add`

---

## Эпик 5: System Integration (v0.7) ✅ ЗАВЕРШЕНО
**Цель:** Ева глубоко интегрирована в систему

### Таск 5.1 — System Monitor ✅
- [x] Мониторинг CPU, RAM, температуры
- [x] Уведомления при высокой нагрузке
- [x] Top processes

### Таск 5.2 — Network Monitor ✅
- [x] Ping checks и latency
- [x] Port availability
- [x] Service health (Internet, DNS, API)

### Таск 5.3 — CLI Commands ✅
- [x] `eva system health` — системный отчёт
- [x] `eva system processes` — топ процессов
- [x] `eva system network` — сетевой статус

---

## Эпик 6: Emotional Intelligence (v0.8) ✅ ЗАВЕРШЕНО
**Цель:** Ева понимает настроение и адаптируется

### Таск 6.1 — Mood Detection ✅
- [x] Анализ текста на настроение (русский)
- [x] Распознавание усталости, стресса
- [x] Отслеживание тренда настроения

### Таск 6.2 — Tone Adaptation ✅
- [x] Адаптация тона под настроение
- [x] Настройка энергии и теплоты
- [x] Знание когда дать пространство

### Таск 6.3 — Personal Connection ✅
- [x] Важные даты (дни рождения и т.д.)
- [x] Проверка дат при общении
- [x] История настроения

---

## Эпик 7: Web & Research (v0.9) ✅ ЗАВЕРШЕНО
**Цель:** Ева ищет информацию и учится

### Таск 7.1 — Web Search ✅
- [x] Поиск в интернете (DuckDuckGo fallback)
- [x] Резюмирование результатов
- [x] Fact-checking

### Таск 7.2 — API Integration ✅
- [x] Weather (OpenWeatherMap)
- [x] Crypto prices (CoinMarketCap)
- [x] News (NewsAPI)
- [x] Time/Calendar info

### Таск 7.3 — Learning Loop ✅
- [x] Research на любую тему
- [x] Извлечение ключевых фактов
- [x] Кэширование результатов

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
| STT (Whisper) | `voice/stt.py` | ✅ Готово |
| Deep Memory (ChromaDB) | `memory/deep_memory.py` | ✅ Готово |