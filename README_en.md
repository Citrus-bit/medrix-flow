# MedrixFlow

**English** | [中文](./README.md)

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-LangGraph-blue?style=for-the-badge&logo=python" alt="LangGraph">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" alt="React 19">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <b>AI Super Agent System Built on LangGraph</b><br/>
  Sandbox Execution · Persistent Memory · Multi-Agent Collaboration · Extensible Tool Ecosystem
</p>

---

MedrixFlow is a full-stack AI agent orchestration platform. The backend leverages LangGraph for multi-agent collaboration and state management, while the frontend is built with Next.js 16 to deliver a modern interactive interface. The system supports code execution, web browsing, and file management within isolated thread-level sandboxes, and retains user context across conversations through persistent memory.

## Key Features

### 1. LangGraph-Powered Multi-Agent Orchestration

Unlike simple LLM chain-of-thought calls, MedrixFlow uses a **LangGraph directed graph state machine** as its core orchestration engine:

- **Lead Agent + Subagent Hierarchical Architecture**: The lead agent handles task understanding and decomposition, delegating to up to 3 subagents that execute in parallel, each with an independent 15-minute timeout
- **16+ Layer Middleware Chain**: A strictly ordered middleware pipeline covering cross-cutting concerns including thread isolation, file upload injection, sandbox lifecycle, security auditing, context summarization, memory extraction, image vision, loop detection, tool error degradation, token usage tracking, visual quality gating, and more
- **Dynamic Model Hot-Swapping**: Switch between different LLMs within the same conversation, with runtime toggling of Thinking mode and Vision mode

### 2. Thread-Level Sandbox Isolation

Each conversation thread has a fully isolated execution environment:

- **Virtual Filesystem Mapping**: `/mnt/user-data/{workspace,uploads,outputs}` is automatically mapped to thread-specific physical directories, preventing cross-thread data leakage
- **Dual Sandbox Engine**: Supports both local direct execution (LocalSandboxProvider) and Docker container isolation (AioSandboxProvider), with the option to switch to K3s Pod-level isolation in production
- **Complete Toolchain Coverage**: bash execution, file read/write, string replacement, directory browsing — agents have full filesystem operation capabilities

### 3. LLM-Driven Persistent Memory

Unlike simple conversation history concatenation, MedrixFlow implements a structured long-term memory system:

- **Automatic Knowledge Extraction**: The LLM analyzes conversation content to automatically extract user backgrounds (profession, preferences), facts (with confidence scores), and context
- **User Correction Detection**: 11 EN/ZH regex patterns detect user corrections in real time (e.g., "actually", "that's wrong", "不对", "其实是"), triggering priority memory updates to prevent stale facts from being persisted
- **Debounced Batch Processing**: Aggregates multi-turn conversation changes through a configurable debounce mechanism (default 30s) to reduce LLM call overhead
- **Pluggable Storage Backend**: Default JSON file storage (`FileMemoryStorage`), with support for swapping in any custom storage implementation (e.g., SQLite, Redis) via the `storage_class` configuration
- **System Prompt Injection**: High-confidence facts and user context are automatically injected into the agent's prompt, enabling personalized responses across conversations

### 4. Streaming & Disconnection Recovery

A production-grade streaming experience built on the LangGraph SDK's `useStream`:

- **SSE Streaming Rendering**: Agent responses, Thinking process, and subagent task progress are all streamed in real time
- **Automatic Disconnection Recovery**: `reconnectOnMount` + `streamResumable` mechanisms ensure automatic reconnection after page refresh or network disconnection, while the backend continues running uninterrupted
- **Optimistic UI Updates**: Messages appear instantly upon sending, and thread lists are optimistically inserted, eliminating perceived network latency

### 5. Zero-Config Frontend UX

Model and API Key configuration is entirely handled through the frontend UI — no manual config file editing required:

- **First-Visit Auto-Guidance**: The configuration panel automatically pops up in a new tab, using `sessionStorage` to ensure it only triggers once per browser session
- **One-Click Connectivity Test**: Dynamically instantiates the Provider class and sends `ainvoke("Hi")` to verify model availability
- **Hot-Reload Activation**: Saved configuration is automatically written to `config.yaml` + `.env`, and takes effect immediately via `reload_app_config()` — no service restart needed

### 6. Multi-Channel Access

In addition to the web interface, MedrixFlow supports IM channel integration:

- **Feishu (Lark)**: Real-time streaming responses with in-place card message updates (stores `message_id` to patch the same card incrementally)
- **Slack**: Socket Mode WebSocket connection — no public IP required
- **Telegram**: Bot interaction with per-user independent session configuration

### 7. Visual Output Quality System

MedrixFlow includes a professional-grade visual output quality assurance system covering the full pipeline for charts, PPT, and image generation:

- **Prompt Constraint Injection**: When visual skills are active, design standards are automatically injected (60-30-10 color rule, typography hierarchy, 8pt grid spacing, accessibility contrast ratios), task-specific rules (targeted constraints for charts/PPT/images), and a mandatory workflow (clarify → spec → self-review → iterate → deliver)
- **Quality Gate Tools**: `visual_quality_check` performs structured self-assessment before delivery (5 checks each for charts, PPT, and images), returning PASS / FAIL / FIXED status; `visual_refinement_check` enables iterative refinement, scoring 1–10 across content accuracy, style match, color fidelity, and more — scores below 7 trigger automatic regeneration (up to 3 rounds)
- **Middleware Enforcement**: `VisualQualityMiddleware` detects when the agent calls `present_files` with visual output without running a quality check first, injecting a reminder
- **Dedicated Visual Subagent**: The `visual-specialist` subagent has built-in design expertise and a complete quality workflow; the Lead Agent can delegate chart, PPT, and image tasks to it
- **Memory Preference Persistence**: The memory system now supports a `visual_preference` fact category, persisting user design preferences (color schemes, fonts, brand guidelines) across conversations
- **Design Resource Library**: Built-in 12 professional color palettes (business-blue, tech-vibrant, medical-clinical, accessible-high-contrast, etc.), 5 chart scenario presets (executive-dashboard, technical-report, marketing-report, etc.), and 5 PPT scenario presets (pitch-deck, quarterly-report, product-launch, etc.) — the agent automatically matches and references them
- **Enhanced PPT Script**: `generate.py` now supports slide transitions, speaker notes, cover/contain image fitting modes, and metadata (author/keywords)

### 8. Security Auditing & Observability

Built-in security auditing and token usage tracking — no external tools required:

- **Bash Command Security Auditing**: `SandboxAuditMiddleware` performs three-tier classification on every bash tool call (block / warn / pass), working with the `allow_host_bash` config switch to automatically block high-risk commands (`rm -rf /`, `curl | sh`, etc.), warn on medium-risk operations (`chmod`, `kill`, etc.), and produce full audit logs
- **Token Usage Tracking**: `TokenUsageMiddleware` records input / output / total token counts after each LLM call, providing the data foundation for cost monitoring and quota management
- **Sandbox Security Awareness**: `security.py` provides `uses_local_sandbox_provider()` and `is_host_bash_allowed()` utility functions to dynamically determine the current sandbox security level at runtime

## Technical Challenges & Solutions

### Middleware Orchestration Order Dependencies

**Challenge**: 16+ middleware components each handle different cross-cutting concerns but have implicit dependencies on one another. For example, `SandboxMiddleware` must run after `UploadsMiddleware` (it needs the thread directory to be created), `ClarificationMiddleware` must run last (it needs to interrupt graph execution), and `SandboxAuditMiddleware` must run after `ToolErrorHandling` (it needs to intercept already-wrapped tool calls).

**Solution**: An explicit ordered middleware chain pattern where each middleware declares its execution phase, and the runtime executes them serially in a fixed order. The middleware pipeline is: ThreadData → Uploads → Sandbox → DanglingToolCall → (Guardrail) → ToolErrorHandling → (Summarization) → (TodoList) → Title → Memory → (ViewImage) → (DeferredToolFilter) → (SubagentLimit) → LoopDetection → SandboxAudit → TokenUsage → Clarification.

### Streaming State Consistency

**Challenge**: During SSE streaming, the frontend must simultaneously handle multiple stream types (messages, Thinking reasoning, subagent task events, tool calls) and recover stream state after page refresh. Safari browsers exhibit inconsistent SSE reconnection behavior.

**Solution**:
- Use `sessionStorage` to store `lg:stream:{threadId}` → `runId` mappings, enabling `reconnectOnMount` stream resumption
- Backend sets `onDisconnect: "continue"` to ensure the run continues after client disconnection
- Thread list adds `refetchOnWindowFocus`, `staleTime: 30s`, and `visibilitychange` listeners to fix Safari compatibility
- Subagent tasks trigger `useUpdateSubtask()` via `onCustomEvent` to update the SubtaskCard in real time

### Configuration Hot-Reload Consistency

**Challenge**: `config.yaml` and `.env` are modified by the frontend UI and need to take effect immediately, but the LangGraph Server, Gateway API, and frontend each maintain their own configuration caches.

**Solution**: The `AppConfig` singleton uses mtime-based file modification detection with automatic hot-reload. The Gateway API checks for file changes on every request via `get_app_config()`. The LangGraph Server monitors YAML file changes and auto-restarts in the Gateway's `--reload` mode. Environment variables are resolved through `load_dotenv` + `resolve_env_variables` with recursive `$VAR` reference substitution.

### Long Conversation Context Management

**Challenge**: Long conversations can easily exceed the model's token limit, causing request failures or context loss.

**Solution**: A configurable `SummarizationMiddleware` supporting three trigger strategies (token threshold, message count, model limit percentage). When triggered, a lightweight model generates a summary, and the most recent N messages + summary become the new context.

## Performance Optimizations

### Startup Speed Optimizations

| Optimization | Measure | Impact |
|--------|------|------|
| Parallel Service Startup | LangGraph, Gateway, and Frontend start simultaneously; only Nginx waits for all three ports to be ready | 40–60% faster startup |
| Config Upgrade Fast Skip | `config-upgrade.sh` uses bash-level `grep` to compare `config_version`, exiting immediately if versions match without starting Python | Reduces cold start by 1–2s |
| Unused Dependency Cleanup | Removed zero-reference `kubernetes` and `duckdb` packages (~130MB); removed mistakenly included `nuxt-og-image` from the Nuxt project | Smaller install size, faster CI |

### Frontend Runtime Optimizations

| Optimization | Measure | Impact |
|--------|------|------|
| Shiki Syntax Highlighting Lazy Load | Changed `codeToHtml` to `await import("shiki")` dynamic import; type imports remain static | First-screen JS reduced by ~200KB |
| CodeMirror Editor Lazy Load | 10 CodeMirror packages (7 languages + 2 themes + react-codemirror) wrapped with `next/dynamic` + `ssr: false`, internally loaded via `Promise.all()` | First-screen JS reduced by ~500KB |
| Optimistic UI Updates | Messages appear instantly on send; thread creation uses optimistic query cache insertion | Eliminates perceived network latency |
| TanStack Query Caching Strategy | `staleTime: 30s` + `refetchOnWindowFocus` + `visibilitychange` listener | Reduces unnecessary API requests |

### Stability Improvements from Bug Fixes

| Issue | Root Cause | Fix |
|------|------|------|
| `max_tokens` 400 Error | GLM-5 via Huawei ModelArts supports a maximum of 131072; the original config of 200000 caused a `BadRequest` silently swallowed by the frontend | Corrected to 131072 |
| UI Freeze When Appending During Send | `sendMessage` with `sendInFlightRef` set to `true` would directly `return` and discard the second message | Changed to first `await thread.stop()` to cancel the current run before sending a new message |
| Thread List Disappearing (Safari) | `useThreads` lacked a refetch strategy; cache expired after tab switching | Added `refetchOnWindowFocus`, `staleTime`, `visibilitychange` listener, and `onCreated` optimistic insertion |
| Thinking State Display Glitch | Optimistic thinking placeholder used a static spinner, causing a flash when switching to actual reasoning content | Replaced with Reasoning component (brain icon + shimmer animation + real-time seconds counter) |

## System Architecture

```
                     ┌─────────────────────────────────────────────┐
                     │            Nginx (Port 1000)                │
                     │        Unified Reverse Proxy Entry          │
                     └──────┬────────────────────┬─────────────────┘
                            │                    │
          /api/langgraph/*  │                    │  /api/* (other)
                            v                    v
          ┌──────────────────────┐  ┌──────────────────────────────┐
          │  LangGraph Server    │  │   Gateway API (Port 8001)    │
          │    (Port 2024)       │  │   FastAPI REST               │
          │                      │  │                              │
          │ ┌──────────────────┐ │  │  /api/models      Models     │
          │ │    Lead Agent    │ │  │  /api/mcp/config  MCP Config │
          │ │                  │ │  │  /api/skills      Skills     │
          │ │  16+ Layer       │ │  │  /api/memory      Memory     │
          │ │  Middleware Chain │ │  │  /api/setup/*     Config     │
          │ │       |          │ │  │  /api/threads/*   Threads    │
          │ │   Tool System    │ │  │                              │
          │ │       |          │ │  └──────────────────────────────┘
          │ │  Subagents(x3)   │ │
          │ └──────────────────┘ │
          └──────────────────────┘
                            │
          ┌──────────────────────┐
          │   Frontend (Port 3000)│
          │   Next.js 16         │
          │   React 19           │
          │   TailwindCSS 4      │
          │   Shadcn UI          │
          └──────────────────────┘
```

**Request Routing** (via Nginx):
- `/api/langgraph/*` → LangGraph Server: Agent interaction, thread management, SSE streaming
- `/api/*` (other) → Gateway API: Models, MCP, Skills, Memory, file uploads, artifacts
- `/` (non-API) → Frontend: Next.js web interface

### Middleware Chain Details

| # | Middleware | Responsibility |
|---|-----------|---------------|
| 1 | ThreadDataMiddleware | Creates thread-specific isolation directories (workspace/uploads/outputs) |
| 2 | UploadsMiddleware | Injects newly uploaded files into the conversation context |
| 3 | SandboxMiddleware | Acquires and manages the sandbox execution environment lifecycle |
| 4 | DanglingToolCallMiddleware | Cleans up dangling incomplete tool calls to ensure consistent history |
| 5 | GuardrailMiddleware | Pre-tool-call authorization guard (optional, config-driven) |
| 6 | ToolErrorHandlingMiddleware | Graceful error degradation for failed tool calls |
| 7 | SummarizationMiddleware | Auto-summarizes and compresses context when approaching token limits (optional) |
| 8 | TodoListMiddleware | Tracks multi-step task progress in plan mode (optional) |
| 9 | TitleMiddleware | Auto-generates conversation title after the first message exchange |
| 10 | MemoryMiddleware | Enqueues conversations for asynchronous memory extraction with correction detection |
| 11 | ViewImageMiddleware | Injects image data for vision-capable models (model-dependent) |
| 12 | DeferredToolFilterMiddleware | Defers tool loading to reduce context usage (config-driven) |
| 13 | SubagentLimitMiddleware | Controls the maximum number of concurrent subagents (config-driven) |
| 14 | LoopDetectionMiddleware | Detects and interrupts infinite agent loop calls |
| 15 | SandboxAuditMiddleware | Bash command security auditing: three-tier classification (block/warn/pass) + audit logs |
| 16 | TokenUsageMiddleware | Records input/output/total token usage per LLM call |
| 17 | ClarificationMiddleware | Intercepts clarification requests and interrupts graph execution (must be last) |
| 18 | VisualQualityMiddleware | Visual output quality gate: checks if visual_quality_check was run before presenting visual files, injects reminder if not |

### Tool Ecosystem

| Category | Tools | Description |
|----------|-------|-------------|
| Sandbox | bash, ls, read_file, write_file, str_replace | Thread-isolated filesystem operations |
| Built-in | present_files, ask_clarification, view_image, task, visual_quality_check, visual_refinement_check | File presentation, interactive clarification, image understanding, subagent delegation, visual quality gate, iterative refinement check |
| Community | Tavily, Jina AI, Firecrawl, DuckDuckGo | Web search, web scraping, image search |
| MCP | Any MCP-compatible server | Supports stdio/SSE/HTTP transport protocols |
| Skills | Domain-specific workflows | Configurable skill packs injected via System Prompt |

## Quick Start

Get MedrixFlow running in just 4 steps — **no manual config file editing required**.

### Step 1: Install Prerequisites

| Tool | Version | Installation |
|------|---------|-------------|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| uv | Latest | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 10+ | `npm install -g pnpm` |
| nginx | - | macOS: `brew install nginx` / Linux: `sudo apt install nginx` |

### Step 2: Clone & Install

```bash
git clone https://github.com/Citrus-bit/medrix-flow.git
cd medrix-flow
make config    # Auto-generate config.yaml and .env (first time only)
make install   # One-command install for all frontend and backend dependencies (backend includes dev dependency group)
```

### Step 3: Start Services

```bash
make dev       # Start all services (LangGraph + Gateway + Frontend + Nginx)
```

Once started, your browser will automatically open http://localhost:1000

> You can also use `make dev-daemon` to start in the background, or double-click `start.command` for one-click launch.

### Step 4: Configure Models & API Keys in the UI

When you first open the page, the setup panel will **automatically pop up** to guide you through configuration:

1. **Add a Model**: On the "Configuration" page, select a provider (OpenAI / Anthropic / Google Gemini / DeepSeek / OpenAI Compatible) and enter the model name
2. **Enter API Key**: Input your API Key and click the "Test" button to verify connectivity
3. **Configure Tool Keys** (optional): If you need web search capabilities, enter Tavily / Jina API Keys
4. **Save Configuration** — Done! Configuration is automatically persisted and the service hot-reloads

> You can reopen the configuration panel at any time via the bottom-left "Settings & More" → "Settings" → "Configuration" tab.

### Common Commands

| Command | Description |
|---------|-------------|
| `make dev` | Start in development mode (with hot-reload) |
| `make start` | Start in production mode (performance-optimized) |
| `make dev-daemon` | Start as background daemon |
| `make stop` | Stop all services |
| `make check` | Check if prerequisites are installed |
| `make verify` | Run CI-aligned local checks (backend lint/test + frontend lint/typecheck) |
| `make clean` | Stop services and clean up temporary files |
| `make up` | Docker production deployment |
| `make down` | Stop Docker containers |

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **LangGraph** | 1.0.6+ | Multi-agent orchestration engine, directed graph state machine |
| **LangChain** | 1.2.3+ | LLM abstraction layer, tool system, MCP adapters |
| **FastAPI** | 0.115.0+ | Gateway REST API, async high-performance |
| **Python** | 3.12+ | Backend runtime |
| **uv** | Latest | Package manager, replacing pip/poetry |
| **agent-sandbox** | - | Sandbox code execution |
| **markitdown** | - | Multi-format document to Markdown conversion |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 16 | React meta-framework, App Router + Turbopack |
| **React** | 19 | UI library |
| **TypeScript** | 5.x | Type safety |
| **TailwindCSS** | 4 | Utility-first CSS framework |
| **Shadcn UI** | - | Base component library |
| **MagicUI** | - | Modern animation components |
| **TanStack Query** | - | Server state management |
| **LangGraph SDK** | - | Agent interaction |

## Project Structure

```
medrix-flow/
├── backend/                        # Backend services
│   ├── packages/harness/medrix_flow/
│   │   ├── agents/                 # Agent system
│   │   │   ├── lead_agent/         #   Lead agent (factory + prompts)
│   │   │   ├── middlewares/        #   18 middleware components (incl. security audit, token tracking & visual quality gate)
│   │   │   ├── memory/             #   Memory extraction, correction detection, visual preference persistence & pluggable storage
│   │   │   └── thread_state.py     #   Thread state Schema
│   │   ├── sandbox/                # Sandbox execution engine + security auditing
│   │   ├── subagents/              # Subagent system (registry + executor + visual-specialist)
│   │   ├── tools/                  # Tool collection (incl. visual_quality_check, visual_refinement_check)
│   │   ├── mcp/                    # MCP protocol integration
│   │   ├── models/                 # Model factory + Provider patches
│   │   ├── skills/                 # Skill discovery & loading
│   │   ├── community/              # Community tools (Tavily/Jina/Firecrawl)
│   │   └── config/                 # Config system (hot-reload + env var resolution)
│   ├── app/gateway/                # FastAPI gateway
│   │   ├── app.py                  #   Application entry point
│   │   └── routers/                #   Route modules (models/mcp/skills/memory/setup)
│   ├── tests/                      # Test suite (277 test cases)
│   ├── langgraph.json              # LangGraph entry configuration
│   └── pyproject.toml              # Python dependencies
│
├── frontend/                       # Frontend application
│   ├── src/
│   │   ├── app/                    # Next.js App Router routes
│   │   ├── components/
│   │   │   ├── ui/                 #   Base UI components
│   │   │   ├── workspace/          #   Workspace components (chat/settings/sidebar)
│   │   │   └── ai-elements/        #   AI components (reasoning/code block/model selector)
│   │   ├── core/                   # Core business logic
│   │   │   ├── threads/            #   Thread management + streaming
│   │   │   ├── setup/              #   Configuration management (types/API/Hooks)
│   │   │   ├── i18n/               #   Internationalization (ZH/EN)
│   │   │   └── settings/           #   Local settings (localStorage)
│   │   └── hooks/                  # Custom React Hooks
│   └── package.json
│
├── skills/                         # Skill system
│   ├── public/                     #   Public skill packs
│   └── custom/                     #   Custom skills
│
├── scripts/                        # Script utilities
│   ├── serve.sh                    #   Service startup (parallel + health check)
│   ├── start-daemon.sh             #   Daemon startup
│   ├── config-upgrade.sh           #   Config version upgrade
│   └── deploy.sh                   #   Docker deployment
│
├── docker/                         # Docker configuration
│   ├── nginx/                      #   Nginx reverse proxy config
│   ├── docker-compose.yaml         #   Production deployment orchestration
│   └── docker-compose-dev.yaml     #   Development environment orchestration
│
├── config.example.yaml             # Configuration template (with full field examples)
├── Makefile                        # Root command entry point
└── README.md                       # This file
```

## Configuration

### Frontend UI Configuration (Recommended)

MedrixFlow supports managing all model and API key configurations directly through the web interface:

- **Model Management**: Add / edit / delete LLM models, supporting 5 preset providers + OpenAI Compatible mode
- **Connectivity Testing**: Each model configuration has a "Test" button that dynamically instantiates the Provider to verify availability
- **Tool API Keys**: Configure Tavily (web search) and Jina (web scraping) keys
- **Instant Effect**: Saving automatically writes to `config.yaml` and `.env`, and the service hot-reloads

**How to open**: Bottom-left "Settings & More" → "Settings" → "Configuration" tab

### Manual Configuration (Advanced Users)

Edit `config.yaml` in the project root directory directly. Main configuration sections:

| Section | Description |
|---------|-------------|
| `models` | LLM model definitions (class paths, API Keys, Thinking/Vision support) |
| `tools` | Tool definitions (module paths, groups) |
| `sandbox` | Execution environment (local / Docker / K3s) + `allow_host_bash` security switch |
| `skills` | Skill directory paths |
| `memory` | Memory system (enabled, storage, debounce, fact limit, storage backend class path) |
| `summarization` | Context summarization (trigger strategy, retention policy) |
| `subagents` | Subagents (timeout configuration) |
| `channels` | IM channels (Feishu/Slack/Telegram) |
| `guardrails` | Tool call authorization guards |
| `token_usage` | Token usage tracking (enabled/disabled) |
| `checkpointer` | State persistence (memory/sqlite/postgres) |

### Environment Variables

Configuration values prefixed with `$` are automatically resolved as environment variables. Common variables:

- Model API Keys: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY`, `GOOGLE_API_KEY`
- Tool API Keys: `TAVILY_API_KEY`, `JINA_API_KEY`, `GITHUB_TOKEN`
- Config overrides: `MEDRIX_FLOW_CONFIG_PATH`, `MEDRIX_FLOW_EXTENSIONS_CONFIG_PATH`

### MCP Server Configuration (extensions_config.json)

```json
{
  "mcpServers": {
    "github": {
      "enabled": true,
      "type": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": { "GITHUB_TOKEN": "$GITHUB_TOKEN" }
    }
  }
}
```

## Supported Model Providers

| Provider | Provider Class Path | Notes |
|----------|---------------------|-------|
| OpenAI | `langchain_openai:ChatOpenAI` | GPT-4o / GPT-5 / o1 etc. |
| Anthropic | `langchain_anthropic:ChatAnthropic` | Claude 3.5/4 series |
| Google Gemini | `langchain_google_genai:ChatGoogleGenerativeAI` | Gemini 2.5 Pro/Flash |
| DeepSeek | `medrix_flow.models.patched_deepseek:PatchedChatDeepSeek` | DeepSeek V3 / Reasoner |
| OpenAI Compatible | `langchain_openai:ChatOpenAI` + custom base_url | Huawei ModelArts, Novita, MiniMax, OpenRouter etc. |

## Documentation

- [Configuration Guide](./backend/docs/CONFIGURATION.md)
- [Architecture Deep Dive](./backend/docs/ARCHITECTURE.md)
- [API Reference](./backend/docs/API.md)
- [File Upload](./backend/docs/FILE_UPLOAD.md)
- [Path Examples](./backend/docs/PATH_EXAMPLES.md)
- [Context Summarization](./backend/docs/summarization.md)
- [Plan Mode](./backend/docs/plan_mode_usage.md)
- [Setup Guide](./backend/docs/SETUP.md)

## License

MIT License — See the [LICENSE](./LICENSE) file for details.

## Acknowledgements

- [LangGraph](https://langchain-ai.github.io/langgraph/) — Graph state machine agent framework
- [LangChain](https://www.langchain.com/) — LLM application development framework
- [Next.js](https://nextjs.org/) — React meta-framework
- [Shadcn UI](https://ui.shadcn.com/) — UI component library
- All open-source library contributors
