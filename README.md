# 🌿 MR.GREEN — Autonomous Personal AI Agent

> *"More than just code — an intelligent assistant and everyday companion."*

Welcome to **MR.GREEN**, a private, self-hosted, autonomous AI agent platform running on my own cloud VPS.

Designed as an extensible AI-agent system from the ground up, MR.GREEN understands natural dialogue, stores semantic context in vector memory, evaluates multi-step plans, executes sandboxed tools with least-privilege security, and features continuous deployment via GitHub Actions.

---

## 🏗️ Architecture & Features

### Core Stack
- **Backend Framework:** Python 3.12+, FastAPI, SQLAlchemy 2.0 (AsyncIO)
- **Database:** PostgreSQL 16 + `pgvector` (semantic long-term memory)
- **Local AI Engine:** Ollama (`qwen2.5:3b`) native execution
- **CI/CD Pipeline:** Automated GitHub Actions SSH deployment to Ubuntu VPS

### 🛠️ Universal Tool Engine (Milestone 2)
MR.GREEN incorporates an enterprise-grade Tool Registry and Sandboxed Executor:

| Tool | Category | Risk Level | Description |
| :--- | :--- | :--- | :--- |
| **`calculator`** | Math | `low` | Safe AST-based mathematical evaluation (No `eval()`). |
| **`time`** | System | `low` | Current UTC, server, and timezone information. |
| **`file_read`** | Filesystem | `low` | Reads workspace files with path traversal safeguards. |
| **`file_write`** | Filesystem | `medium` | Writes or appends files strictly inside the approved workspace. |
| **`web_fetch`** | Network | `medium` | Fetches public webpages with SSRF protection against private IPs. |
| **`shell`** | Shell | `critical` | Sandboxed command execution (**disabled by default**, approval gated). |

### 🔒 Security & Approval System
- **Deny by Default:** Tools receive only the permissions explicitly granted in their manifest.
- **SSRF Protection:** Blocks local loopback (`127.0.0.1`), private subnets, and cloud metadata (`169.254.169.254`).
- **Path Traversal Guards:** Prevents `../` escaping and blocks access to `/root`, `/etc`, and `.env`.
- **Human Approval Gating:** High and critical risk operations halt execution until approved via `/api/approvals`.

---

## 🚀 Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Ollama (running locally with `qwen2.5:3b`)

### 2. Running Locally
```bash
# Clone the repository
git clone https://github.com/Rtr-k-gowtham/mrgreen.git
cd mrgreen

# Start PostgreSQL with pgvector
docker compose up -d postgres

# Setup backend
cd backend
pip install -r requirements.txt
cp .env.example .env

# Run FastAPI server
uvicorn app.main:app --reload
```

---

## 📡 API Reference

| Endpoint | Method | Description |
| :--- | :--- | :--- |
| `/health` | `GET` | System health check (API, Database, Ollama status) |
| `/api/chat` | `POST` | Chat with MR.GREEN (auto-plans tool calls when needed) |
| `/api/tools` | `GET` | List all registered tools and their schemas |
| `/api/tools/{name}` | `GET` | Get tool metadata and parameter schema |
| `/api/tools/{name}/execute` | `POST` | Execute a tool directly with input payload |
| `/api/tools/{name}/enable` | `POST` | Enable a disabled tool |
| `/api/tools/{name}/disable` | `POST` | Disable a registered tool |
| `/api/tool-calls` | `GET` | View audit log of executed tools |
| `/api/agent/runs` | `GET` | List agent execution runs |
| `/api/agent/runs/{id}` | `GET` | Inspect full trace of plan, tool steps, and response |
| `/api/approvals` | `GET` | List pending approval requests |
| `/api/approvals/{id}/approve` | `POST` | Approve gated tool execution |
| `/api/approvals/{id}/reject` | `POST` | Reject gated tool execution |

---

## 🗺️ Roadmap

- [x] **Milestone 1:** Production Foundation (FastAPI, Ollama, pgvector, GitHub Actions CI/CD)
- [x] **Milestone 2:** Universal Tool Engine, Tool Registry, Executor & Security Sandbox
- [ ] **Milestone 3:** Capability Factory (Self-extending code generation and sandbox testing)
- [ ] **Milestone 4:** Frontend UI (React + Vite real-time agent dashboard)
- [ ] **Milestone 5:** Voice Interaction & Multi-Agent Collaboration

---
*Created with passion by Gowtham for MR.GREEN.*
