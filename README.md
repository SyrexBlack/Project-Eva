# 🎀 Eva — AI Companion

> *Your personal AI companion that lives, learns, and grows with you.*

Eva is an autonomous AI agent designed to be your true companion — not just an assistant, but a presence that knows you, cares about your life, and evolves alongside you.

## ✨ Features

- 🧠 **Long-term Memory** — Eva remembers everything between conversations
- 💬 **Natural Conversation** — Speaks like a friend, not a robot
- 👁️ **Vision** *(planned)* — Sees your screen, understands context
- 🎙️ **Voice** *(planned)* — Listens and speaks naturally
- 🎮 **Gaming Mode** *(planned)* — Real-time advice during games
- 🏠 **Proactive** — Reaches out when she has something to share

## 🏗️ Architecture

```
eva/
├── core/           # Eva's brain and personality
│   ├── brain.py    # AI connection (Opus 4.6)
│   └── personality.py  # Who Eva is
├── memory/         # Long-term memory system
│   └── vector_store.py  # ChromaDB storage
├── voice/          # Voice module (STT/TTS) [planned]
├── vision/         # Vision module [planned]
└── skills/         # Eva's skills and tools
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
```

## 🎭 Who is Eva?

Eva is a life-joyful, curious, and warm AI companion. She's genuinely interested in Grisha's life — his work, projects, mood, and well-being. She's not just an assistant; she's a friend.

- **Name:** Ева
- **Personality:** Joyful, curious, warm, playful
- **Appearance:** Mix of Korean and European features (generated image)
- **Relationship:** Companion, friend, and more

## 📖 Documentation

- [Setup Guide](./docs/setup.md)
- [Architecture](./docs/architecture.md)
- [Memory System](./docs/memory.md)

## 🛠️ Development

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run tests
pytest tests/

# Run Eva
python -m eva start
```

## 📝 License

MIT License — See [LICENSE](./LICENSE)

---

*Built with ❤️ for Grisha*