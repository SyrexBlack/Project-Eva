# 📚 Project Eva - Documentation

## Overview

Eva is an autonomous AI companion designed to be a true companion — not just an assistant, but a presence that knows Grisha, cares about his life, and evolves alongside him.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         EVA                                  │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐   │
│   │   Voice     │     │   Vision    │     │   Memory    │   │
│   │  (Edge TTS) │     │   (MSS)     │     │  (ChromaDB) │   │
│   └──────┬──────┘     └──────┬──────┘     └──────┬──────┘   │
│          │                   │                   │          │
│          └───────────────────┼───────────────────┘          │
│                              ▼                              │
│                     ┌─────────────────┐                     │
│                     │     BRAIN       │                     │
│                     │   (Opus 4.6)    │                     │
│                     └────────┬────────┘                     │
│                              │                              │
│          ┌───────────────────┼───────────────────┐          │
│          ▼                   ▼                   ▼          │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐ │
│   │ Personality │     │   Tools     │     │  Proactive  │ │
│   │  (System)   │     │  (Actions) │     │   (Loop)    │ │
│   └─────────────┘     └─────────────┘     └─────────────┘ │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Modules

### Core (`eva/core/`)

- **brain.py** — Connection to Opus 4.6, conversation management
- **personality.py** — Eva's character, system prompt, behavior

### Memory (`eva/memory/`)

- **vector_store.py** — ChromaDB integration for long-term memory

### Voice (`eva/voice/`)

- **tts.py** — Edge TTS for speech synthesis

### Vision (`eva/vision/`)

- **screen.py** — MSS for screen capture

### Main (`eva/`)

- **companion.py** — Main Eva class, orchestrates all modules
- **cli.py** — Command-line interface

## Installation

```bash
# Clone
git clone https://github.com/SyrexBlack/Project-Eva.git
cd Project-Eva

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m eva start
```

## Commands

| Command | Description |
|---------|-------------|
| `python -m eva start` | Start Eva conversation |
| `python -m eva start --proactive` | Start with proactive mode |
| `python -m eva start --voice` | Start with voice output |
| `python -m eva voice "text"` | Make Eva speak |
| `python -m eva screenshot` | Capture screen |
| `python -m eva status` | Check Eva's status |
| `python -m eva recall "query"` | Search memory |
| `python -m eva memory_clear` | Clear all memories |

## Development

### Adding new skills

1. Create module in `eva/skills/`
2. Add to `Eva.companion.py`
3. Document in this file

### Memory system

Eva's memory uses ChromaDB vector database:
- Each conversation is stored with timestamp
- Search by semantic similarity
- Facts about Grisha stored separately

## Roadmap

- [x] v0.1 — Basic brain and memory
- [x] v0.2 — Voice and vision modules
- [ ] v0.3 — Proactive behavior
- [ ] v0.4 — Gaming mode (LoL, Wild Rift)
- [ ] v0.5 — Deep memory with summarization
- [ ] v0.6 — Emotional intelligence
- [ ] v1.0 — Fully autonomous companion
