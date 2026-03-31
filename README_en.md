# MedrixFlow

**English** | [中文](./README.md)

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-LangGraph-blue?style=for-the-badge&logo=python" alt="LangGraph">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

MedrixFlow is a LangGraph-based AI super agent system with sandbox execution, persistent memory, and extensible tool integration. The backend enables AI agents to execute code, browse the web, manage files, delegate tasks to subagents, and retain context across conversations - all in isolated, per-thread environments.

---

## ✨ Features

### 🤖 Intelligent Agent System
- **Lead Agent**: LangGraph-powered core agent with dynamic model selection, thinking mode, and visual understanding support
- **Subagent System**: Parallel task execution support with up to 3 concurrent subagents, 15-minute timeout per task
- **Middleware Chain**: 9 middleware components handling thread isolation, file uploads, sandbox management, memory extraction, and more

### 🔒 Sandbox Execution
- **Thread Isolation**: Each conversation thread has its own isolated filesystem space
- **Virtual Paths**: `/mnt/user-data/{workspace,uploads,outputs}` automatically maps to thread-specific directories
- **Toolset**: bash, ls, read_file, write_file, str_replace

### 💾 Persistent Memory
- **Automatic Extraction**: AI automatically analyzes conversations to extract user context, facts, and preferences
- **Structured Storage**: User context (work, personal, top-of-mind), history, and confidence-scored facts
- **Prompt Injection**: Top facts and context injected into agent prompts

### 🛠️ Tool Ecosystem
| Category | Tools |
|----------|-------|
| **Sandbox** | bash, ls, read_file, write_file, str_replace |
| **Built-in** | present_files, ask_clarification, view_image, task |
| **Community** | Tavily (web search), Jina AI (web fetch), Firecrawl, DuckDuckGo (image search) |
| **MCP** | Any Model Context Protocol server |
| **Skills** | Domain-specific workflows injected via system prompt |

### 📱 Multi-Channel Support
- **Feishu**: Real-time streaming responses with in-thread card message updates
- **Slack**: Message interaction support
- **Telegram**: Bot interaction support

---

## 🏗️ Architecture

```
                        ┌──────────────────────────────────────┐
                        │          Nginx (Port 1000)           │
                        │      Unified reverse proxy           │
                        └───────┬──────────────────┬───────────┘
                                │                  │
              /api/langgraph/*  │                  │  /api/* (other)
                                ▼                  ▼
               ┌────────────────────┐  ┌────────────────────────┐
               │ LangGraph Server   │  │   Gateway API (8001)   │
               │    (Port 2024)     │  │   FastAPI REST         │
               │                    │  │                        │
               │ ┌────────────────┐ │  │ Models, MCP, Skills,   │
               │ │  Lead Agent    │ │  │ Memory, Uploads,       │
               │ │  ┌──────────┐  │ │  │ Artifacts              │
               │ │  │Middleware│  │ │  └────────────────────────┘
               │ │  │  Chain   │  │ │
               │ │  └──────────┘  │ │
               │ │  ┌──────────┐  │ │
               │ │  │  Tools   │  │ │
               │ │  └──────────┘  │ │
               │ │  ┌──────────┐  │ │
               │ │  │Subagents │  │ │
               │ │  └──────────┘  │ │
               │ └────────────────┘ │
               └────────────────────┘
```

**Request Routing** (via Nginx):
- `/api/langgraph/*` → LangGraph Server - agent interactions, threads, streaming
- `/api/*` (other) → Gateway API - models, MCP, skills, memory, artifacts, uploads
- `/` (non-API) → Frontend - Next.js web interface

---

## 🚀 Quick Start

Get MedrixFlow running in 4 steps — **no manual config file editing required**.

### 1. Install Prerequisites

| Tool | Version | Install |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| uv | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 10+ | `npm install -g pnpm` |
| nginx | - | macOS: `brew install nginx`, Linux: `sudo apt install nginx` |

### 2. Clone & Install

```bash
git clone https://github.com/Citrus-bit/medrix-flow.git
cd medrix-flow
make config    # Generate config files (first time only)
make install   # Install all frontend & backend dependencies
```

### 3. Start

```bash
make stop && make dev       # Start all services (LangGraph + Gateway + Frontend + Nginx)
```

Once started, your browser will open **http://localhost:1000** automatically.

### 4. Configure Models & API Keys

On first visit, the setup panel opens automatically to guide you through configuration:

1. Add your LLM models on the "Setup" page (supports OpenAI, Anthropic, Google Gemini, DeepSeek, etc.)
2. Enter your model API Key and click "Test" to verify connectivity
3. Optionally configure Tavily / Jina API keys for web search & fetch
4. Click "Save Configuration" — done!

> You can reopen the setup panel anytime via the bottom-left "Settings and More" → "Settings" menu.

### Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start all services (dev mode with hot-reload) |
| `make stop` | Stop all services |
| `make check` | Check if prerequisites are installed |
| `make clean` | Stop services and clean temp files |

---

## 📁 Project Structure

```
medrix-flow/
├── backend/                    # Backend service
│   ├── src/
│   │   ├── agents/            # Agent system
│   │   │   ├── lead_agent/   # Main agent (factory, prompts)
│   │   │   ├── middlewares/  # 9 middleware components
│   │   │   ├── memory/       # Memory extraction & storage
│   │   │   └── thread_state.py
│   │   ├── gateway/          # FastAPI Gateway
│   │   │   ├── app.py
│   │   │   └── routers/      # Route modules
│   │   ├── sandbox/          # Sandbox execution
│   │   ├── subagents/        # Subagent system
│   │   ├── tools/            # Toolset
│   │   ├── mcp/              # MCP protocol integration
│   │   ├── models/           # Model factory
│   │   ├── skills/           # Skill discovery & loading
│   │   └── config/           # Configuration system
│   ├── docs/                 # Documentation
│   ├── tests/                # Tests
│   ├── pyproject.toml        # Python dependencies
│   └── Makefile              # Development commands
│
├── frontend/                  # Frontend application
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── components/       # React components
│   │   ├── core/             # Core business logic
│   │   ├── hooks/            # Custom React hooks
│   │   └── lib/              # Shared libraries
│   ├── public/               # Static assets
│   ├── package.json          # Node dependencies
│   └── README.md             # Frontend documentation
│
├── skills/                   # Skills system
│   ├── public/               # Public skills
│   └── custom/               # Custom skills
│
├── scripts/                  # Utility scripts
├── logs/                     # Log files
├── docker/                   # Docker configuration
├── config.example.yaml       # Configuration template
├── Makefile                  # Root-level commands
└── README.md                 # This file
```

---

## ⚙️ Configuration

### Web UI Configuration (Recommended)

MedrixFlow lets you manage models and API keys directly from the web interface — no config files to edit:

- **Model Configuration**: Add/edit/remove LLM models with one-click connectivity testing
- **Tool API Keys**: Configure Tavily (web search) and Jina (web fetch) keys
- **Instant Apply**: All changes are persisted to `config.yaml` and `.env` automatically, with live hot-reload

Access via: bottom-left "Settings and More" → "Settings" → "Setup" tab.

### Manual Configuration (Advanced)

For finer-grained control, edit `config.yaml` in the project root directly.

Key sections:
- `models` - LLM configurations with class paths, API keys, thinking/vision flags
- `tools` - Tool definitions with module paths and groups
- `tool_groups` - Logical tool groupings
- `sandbox` - Execution environment provider
- `skills` - Skills directory paths
- `title` - Auto-title generation settings
- `summarization` - Context summarization settings
- `subagents` - Subagent system (enabled/disabled)
- `memory` - Memory system settings

### Extensions Configuration (`extensions_config.json`)

MCP servers and skill states in a single file:

```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {"GITHUB_TOKEN": "$GITHUB_TOKEN"}
    }
  },
  "skills": {
    "pdf-processing": {"enabled": true}
  }
}
```

### Environment Variables

- `MEDRIX_FLOW_CONFIG_PATH` - Override config.yaml location
- `MEDRIX_FLOW_EXTENSIONS_CONFIG_PATH` - Override extensions_config.json location
- Model API keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, etc.
- Tool API keys: `TAVILY_API_KEY`, `GITHUB_TOKEN`, etc.

---

## 🛠️ Tech Stack

### Backend
- **LangGraph** (1.0.6+) - Agent framework and multi-agent orchestration
- **LangChain** (1.2.3+) - LLM abstractions and tool system
- **FastAPI** (0.115.0+) - Gateway REST API
- **langchain-mcp-adapters** - Model Context Protocol support
- **agent-sandbox** - Sandboxed code execution
- **markitdown** - Multi-format document conversion
- **tavily-python** / **firecrawl-py** - Web search and scraping

### Frontend
- **Next.js 16** - React framework (App Router)
- **React 19** - UI library
- **Tailwind CSS 4** - Styling framework
- **Shadcn UI** - UI component library
- **MagicUI** - Modern UI components
- **LangGraph SDK** - Agent interaction
- **Vercel AI Elements** - AI UI elements

---

## 📖 Documentation

- [Configuration Guide](./backend/docs/CONFIGURATION.md)
- [Architecture Details](./backend/docs/ARCHITECTURE.md)
- [API Reference](./backend/docs/API.md)
- [File Upload](./backend/docs/FILE_UPLOAD.md)
- [Path Examples](./backend/docs/PATH_EXAMPLES.md)
- [Context Summarization](./backend/docs/summarization.md)
- [Plan Mode](./backend/docs/plan_mode_usage.md)
- [Setup Guide](./backend/docs/SETUP.md)

---

## 📄 License

MIT License - See the [LICENSE](./LICENSE) file for more details.

---

## 🌟 Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) - Powerful graph state machine framework
- [LangChain](https://www.langchain.com/) - LLM application development framework
- [Next.js](https://nextjs.org/) - React meta-framework
- All open-source library contributors
