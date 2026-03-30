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
                        │          Nginx (Port 2026)           │
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

### Prerequisites

**Backend:**
- Python 3.12+
- [uv](https://docs.astral.sh/uv/) package manager
- API keys for your chosen LLM provider

**Frontend:**
- Node.js 22+
- pnpm 10.26.2+

### Installation

```bash
# 1. Clone the project
git clone https://github.com/your-username/medrix-flow.git
cd medrix-flow

# 2. Copy configuration files
cp config.example.yaml config.yaml

# 3. Install backend dependencies
cd backend
make install

# 4. Install frontend dependencies (new terminal)
cd ../frontend
pnpm install

# 5. Copy frontend environment variables
cp .env.example .env
```

### Configuration

Edit `config.yaml` in the project root:

```yaml
models:
  - name: gpt-4o
    display_name: GPT-4o
    use: langchain_openai:ChatOpenAI
    model: gpt-4o
    api_key: $OPENAI_API_KEY
    supports_thinking: false
    supports_vision: true

  - name: claude-sonnet-4
    display_name: Claude Sonnet 4
    use: langchain_anthropic:ChatAnthropic
    model: claude-sonnet-4-20250514
    api_key: $ANTHROPIC_API_KEY
    supports_thinking: true
    supports_vision: true
```

Set your API keys:

```bash
# Add to ~/.bashrc or ~/.zshrc
export OPENAI_API_KEY="your-api-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key-here"

# Then reload
source ~/.bashrc  # or source ~/.zshrc
```

### Running

**Full Application** (from project root):

```bash
make dev  # Starts LangGraph + Gateway + Frontend + Nginx
```

Access at: http://localhost:2026

**Running components separately:**

```bash
# Backend - LangGraph Server (terminal 1)
cd backend
make dev

# Backend - Gateway API (terminal 2)
cd backend
make gateway

# Frontend (terminal 3)
cd frontend
pnpm dev
```

Direct access:
- Main app: http://localhost:2026
- LangGraph: http://localhost:2024
- Gateway: http://localhost:8001
- Frontend: http://localhost:3000

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

### Main Configuration (`config.yaml`)

Place in project root. Config values starting with `$` resolve as environment variables.

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

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](./CONTRIBUTING.md) to learn how to contribute.

---

## 📄 License

MIT License - See the [LICENSE](./LICENSE) file for more details.

---

## 🌟 Acknowledgments

- [LangGraph](https://langchain-ai.github.io/langgraph/) - Powerful graph state machine framework
- [LangChain](https://www.langchain.com/) - LLM application development framework
- [Next.js](https://nextjs.org/) - React meta-framework
- All open-source library contributors
