# MR.GREEN — Autonomous Personal AI Agent

> *"More than just code — an intelligent assistant and everyday companion."*

Welcome to **MR.GREEN**, a private, self-hosted, autonomous AI assistant running on my own VPS.

Designed as an extensible AI-agent platform from the beginning, MR.GREEN is built to understand natural conversation, learn from interaction, execute tools, and eventually write and deploy its own capabilities.

---

## 🏗️ Architecture (Milestone 1)

This repository contains the foundational structure for MR.GREEN.

### Tech Stack
- **Backend:** Python 3.13+, FastAPI, SQLAlchemy
- **Database:** PostgreSQL + pgvector (for semantic memory)
- **AI Engine:** Ollama (qwen2.5:3b) local execution

### Core Components
- **Agent System:** Core loop (Understand → Plan → Execute → Observe → Verify)
- **AI Abstraction:** Provider-agnostic interface (currently using OllamaProvider)
- **Memory Manager:** AI-powered memory extraction (preferences, facts, workflows) with short-term (context) and long-term (pgvector) storage.
- **Tool Registry:** Extensible self-describing tool interface
- **Capability Stubs:** Placeholders for the future self-extending capability factory, sandbox, and validator.

---

## 🚀 Getting Started (Development)

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.13+
- Ollama (running locally with `qwen2.5:3b` installed)

### 2. Setup

```bash
# Clone the repository
git clone https://github.com/Rtr-k-gowtham/mrgreen.git
cd mrgreen

# Start the PostgreSQL database
docker-compose up -d

# Set up Python environment
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# (Edit .env if needed, though defaults work for local dev)

# Run the API server
uvicorn app.main:app --reload
```

### 3. Usage

Check API Health:
```bash
curl http://localhost:8000/health
```

Chat with MR.GREEN:
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello MR.GREEN, I prefer concise answers."}'
```

---

## 🔒 Security Model

Security is mandatory. MR.GREEN operates under strict boundaries:
- **No root access:** Dedicated user environment
- **Tool Permissions:** Explicit approval required for dangerous operations
- **Sandbox Execution:** (Planned) All newly generated code will run in isolated sandboxes before deployment.

---

## 🗺️ Roadmap

- [x] **Milestone 1:** Foundation (FastAPI, Ollama integration, Basic Memory, Agent Loop)
- [ ] **Milestone 2:** Built-in Tools (Filesystem, Web Search, Shell Execution)
- [ ] **Milestone 3:** Capability Factory (Self-extending code generation and testing)
- [ ] **Milestone 4:** Frontend UI (React + Vite)
- [ ] **Milestone 5:** Voice Interaction

---
*Created with passion by Gowtham for MR.GREEN.*
