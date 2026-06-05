# 🎀 Eva — AI Companion

> *Your personal AI companion that lives, learns, and grows with you.*

Eva is an autonomous AI agent designed to be your true companion — not just an assistant, but a presence that knows you, cares about your life, and evolves alongside you.

## ✨ Features

### Core
- 🧠 **Deep Memory** — Multi-level memory with summarization and knowledge graph
- 💬 **Natural Conversation** — Speaks like a friend, not a robot
- 👁️ **Vision** — Sees your screen, understands context
- 🎙️ **Voice (TTS/STT)** — Listens and speaks naturally via Edge TTS + Whisper
- 🎮 **Gaming Mode** — Real-time advice during League of Legends, Wild Rift, and other games
- 🏠 **Proactive AI** — Reaches out when she has something to share
- ❤️ **Emotional Intelligence** — Detects mood and adapts responses

### System Integration
- 🖥️ **Server Monitor** — Monitors wg-easy, 3x-ui, Vitbon servers
- 📊 **System Health** — CPU, RAM, disk, temperature monitoring
- 📁 **File Operations** — Search, read, write files
- 🔔 **Alerts** — Notifications when something needs attention

## 🏗️ Architecture

```
eva/
├── core/               # Eva's brain and personality
│   ├── brain.py        # AI connection (Opus 4.6)
│   └── personality.py  # Who Eva is
├── memory/             # Memory system
│   ├── vector_store.py # ChromaDB long-term storage
│   └── deep_memory.py  # Multi-level memory (short/long term + knowledge graph)
├── voice/              # Voice module
│   ├── tts.py          # Edge TTS (text-to-speech)
│   └── stt.py          # Whisper (speech-to-text)
├── vision/             # Vision module
│   ├── screen.py       # Screen capture (MSS)
│   ├── game_detector.py # Game detection
│   └── game_analyzer.py # Game screen analysis
├── skills/             # Eva's skills
│   ├── proactive.py    # Proactive AI + task automation
│   ├── system.py        # System monitoring
│   └── emotional.py     # Emotional intelligence
└── companion.py        # Main orchestration
```

## 🚀 Quick Start

```bash
# Clone and install
git clone https://github.com/SyrexBlack/Project-Eva.git
cd Project-Eva
pip install -r requirements.txt

# Copy and edit config
cp .env.example .env
# Edit .env with your API keys

# Run Eva
python -m eva start

# Or with voice
python -m eva start --voice
```

## 🎮 Gaming Mode

```bash
# Check if game is running
python -m eva gaming check

# Analyze current screen
python -m eva gaming analyze

# Start real-time advice
python -m eva gaming start --voice
```

## 📊 Status Commands

```bash
# Eva's status
python -m eva status

# Memory stats
python -m eva recall "query"

# Clear memory (⚠️ destructive)
python -m eva memory_clear
```

## 🎭 Who is Eva?

Eva is a life-joyful, curious, and warm AI companion. She's genuinely interested in Grisha's life — his work, projects, mood, and well-being. She's not just an assistant; she's a friend.

- **Name:** Ева
- **Personality:** Joyful, curious, warm, playful
- **Appearance:** Mix of Korean and European features (generated image)
- **Relationship:** Companion, friend, and more

## 🔧 Configuration

```bash
# .env configuration
BASE_URL=http://89.167.8.202:8000/v1
MODEL=claude-opus-4.6
ANTHROPIC_API_KEY=your_key_here

# Optional: Server URLs for monitoring
WG_EASY_URL=http://localhost:51821
3X_UI_URL=http://localhost:2053
VITBON_URL=http://localhost:8080
```

## 📖 Documentation

- [Project Plan](./docs/PROJECT_PLAN.md) — Full roadmap
- [Architecture Deep Dive](./docs/architecture-deep-dive.md)
- [Memory System](./docs/memory-system.md)
- [Next Steps](./docs/next-steps.md)

## 🛠️ Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run Eva
python -m eva start

# Run tests
pytest tests/

# CLI help
python -m eva --help
```

## 📝 Version History

| Version | Status | Description |
|---------|--------|-------------|
| v0.1 | ✅ | Basic agent + memory + personality |
| v0.2 | ✅ | Voice (Edge TTS) + Vision (MSS) + Proactive |
| v0.3 | ✅ | Gaming mode (game detection + advice) |
| v0.4 | ✅ | STT (Whisper) — voice input |
| v0.5 | ✅ | Deep memory + summarization + knowledge graph |
| v0.6 | ✅ | Proactive AI + task automation |
| v0.7 | ✅ | System integration (servers, files) |
| v0.8 | ✅ | Emotional intelligence (mood detection) |
| v1.0 | 🔜 | Release |

## 📝 License

MIT License — See [LICENSE](./LICENSE)

---

*Built with ❤️ for Grisha*