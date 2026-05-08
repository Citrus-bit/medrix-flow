# MedrixFlow 2.6.2

**English** | [中文](./README.md)

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-LangGraph-blue?style=for-the-badge&logo=python" alt="LangGraph">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" alt="React 19">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <b>An AI Research Agent Platform for Academic Writing and Experiment Reports</b><br/>
  Literature Retrieval · APA 7 References · Experimental Evidence · Multi-Agent Collaboration
</p>

---

MedrixFlow is a full-stack AI agent orchestration platform for academic writing, literature reviews, experiment reports, and research delivery. The backend uses LangGraph for multi-agent collaboration and state management, while the frontend provides a thread-based chat and artifact workflow built on Next.js 16. Beyond general-purpose agent capabilities, MedrixFlow now includes structured academic retrieval, APA 7 reference export, CS/AI and bioinformatics experiment specialist agents, local evidence storage, and report-oriented artifact delivery designed to solve the usual gaps in academic workflows: weak scholarly grounding, poor references, and disconnected experiment outputs.

## Key Features

### 1. Academic Research Pipeline: From Topic to APA 7 References

MedrixFlow now includes a dedicated, traceable pipeline for formal academic reporting:

- **Built-in academic subagent**: `academic-researcher` handles topic decomposition, query expansion, candidate paper screening, evidence card generation, outline building, and reference export
- **Formal-source-first CS/AI stack**: the default `cs_ai` path uses `DBLP`, `OpenReview`, `ACL Anthology`, `Semantic Scholar`, `OpenAlex`, `Crossref`, and `arXiv`, with conference/journal versions preferred as the canonical reference
- **Formal report exports**: a single research project can produce `report.md`, `references.md`, `references.bib`, `evidence_map.json`, `retrieval_audit.json`, and optionally `graph.json`
- **Local evidence persistence**: research projects, paper metadata, evidence cards, outline mappings, and formatted references are stored locally in SQLite for incremental reuse

### 2. Experiment Specialist Agents: CS/AI and Bioinformatics

MedrixFlow does not stop at writing. It also closes the gap between experiments and paper-ready outputs:

- **Visible system agents**: `cs-ai-lab` focuses on regression, classification, clustering, dimensionality reduction, diagnostics, and paper-ready result summaries; `bioinformatics-lab` focuses on bulk expression workflows, differential analysis, enrichment, and single-cell starter analyses
- **Python-first execution**: experiment workflows run through a unified local Python path to reduce runtime switching and keep outputs reproducible
- **Automatic scientific figure routing**: chart type is selected from task intent and data shape, including line plots, histograms, scatter plots, heatmaps, ROC/PR, volcano, violin, and dot plots
- **Paper-ready export bundle**: experiments can export `experiment_plan.md`, `methods.md`, `results.md`, `metrics.json`, `figure_manifest.json`, `figures/`, `tables/`, and when needed `paper_ready_results.md`

### 3. Thread-Level Delivery and Artifact Discovery

Academic workflows only work if users can reliably find the generated outputs:

- **Thread-level outputs directory**: reports, BibTeX, figures, and result tables are written into the current thread’s artifact directory
- **Improved right-side file panel**: the artifact panel supports auto-discovery of thread `outputs`, a manual refresh button, latest-file highlighting, preview, and download
- **Delivery over chat spam**: larger research tasks prefer artifact bundles instead of forcing long reports into a single chat message

### 4. LangGraph-Powered Multi-Agent Orchestration

Unlike simple LLM chaining, MedrixFlow uses a **LangGraph directed graph state machine** as its orchestration core:

- **Lead Agent + Subagent architecture**: the lead agent handles task understanding and decomposition, delegating to up to 3 subagents in parallel, each with a 15-minute timeout
- **Multi-layer middleware chain**: a strictly ordered pipeline handles thread isolation, uploads, sandbox lifecycle, security auditing, summarization, memory extraction, loop detection, tool error degradation, token tracking, and visual quality gating
- **Dynamic model hot-swapping**: conversations can switch LLMs mid-thread, with model capabilities declared through flags such as `supports_thinking`, `supports_reasoning_effort`, and `supports_vision`

### 5. Thread-Level Sandbox Isolation

Each conversation thread has a fully isolated execution environment:

- **Virtual filesystem mapping**: `/mnt/user-data/{workspace,uploads,outputs}` is mapped to thread-specific physical directories to prevent cross-thread data leakage
- **Dual sandbox engine**: supports local direct execution (`LocalSandboxProvider`) and Docker-based isolation (`AioSandboxProvider`), with K3s pod isolation as a production option
- **Complete toolchain coverage**: bash execution, file read/write, string replacement, and directory browsing are all available inside the isolated workspace

### 6. LLM-Driven Persistent Memory

Unlike simple history concatenation, MedrixFlow implements a structured long-term memory system:

- **Automatic knowledge extraction**: the LLM extracts user background, preferences, facts, and context from conversations
- **User correction detection**: 11 EN/ZH regex patterns detect corrections in real time and prioritize memory updates
- **Debounced batch processing**: multi-turn changes are aggregated with a configurable debounce window (default 30s) to reduce LLM overhead
- **Pluggable storage backend**: JSON file storage is the default, but `storage_class` can be swapped for SQLite, Redis, or custom implementations
- **System prompt injection**: high-confidence facts and user context are automatically injected into prompts for cross-session personalization

### 7. Streaming and Zero-Config Frontend UX

MedrixFlow keeps the UX production-ready through the LangGraph SDK’s `useStream` and a frontend-first setup flow:

- **SSE streaming rendering**: responses, thinking traces, and subagent progress stream in real time
- **Automatic disconnection recovery**: `reconnectOnMount + streamResumable` allows recovery after refresh or network interruption while backend execution continues
- **Frontend-first setup**: model and API key configuration is handled in the UI and hot-reloaded into the app
- **Modes map to reasoning depth**: `flash / pro / ultra` expose higher-level behavior instead of low-level model toggles

### 8. Visual Quality, Security Auditing, and Observability

The platform also keeps strong delivery quality and operational visibility:

- **Visual quality gates**: `visual_quality_check` and `visual_refinement_check` enforce structured QA before charts, PPT, or image outputs are delivered
- **Dedicated visual subagent**: `visual-specialist` handles high-quality visual generation and iterative refinement
- **Bash command auditing**: `SandboxAuditMiddleware` classifies every bash call into block / warn / pass and records audit logs
- **Token usage tracking**: `TokenUsageMiddleware` records input / output / total token counts per LLM call
- **Sandbox security awareness**: `security.py` exposes helpers to determine the current sandbox security level at runtime

## Current Interaction Notes

### Academic Reports and File Delivery

- Academic research and experiment tasks write outputs such as `report.md`, `references.md`, `references.bib`, figures, and result tables into the current thread’s `outputs`
- The right-side file panel auto-discovers these artifacts and supports **manual refresh**, **latest-file highlighting**, preview, and download
- When a task is better delivered as files than as chat prose, the agent prefers returning an artifact bundle that can be reused directly in writing workflows

### Clarification and Confirmation

- When the agent needs more information or explicit approval, it calls `ask_clarification`
- In the web UI, these requests are rendered as button-based choices instead of plain text only
- Each clarification card includes a final `type something` option so the user can switch back to free-form input

### LaTeX / PDF Preview

- When `present_files` is used on a `.tex` file, the app attempts to generate a preview PDF automatically
- The current implementation prefers local `tectonic` and does not require `pdflatex`, `xelatex`, or `latexmk`
- The preview pipeline also applies common compatibility fixes such as downloading remote images, injecting `subfig`, and normalizing some Unicode sub/superscripts

### Production Security Requirements

- Production deployments must explicitly set `MEDRIX_FLOW_ENV=production` so the Python services enable their production safety guards and reject `LocalSandboxProvider`
- When nginx exposes the UI/API, `MEDRIX_FLOW_UI_PASSWORD` must be configured or `/workspace`, `/api/*`, `/api/langgraph/*`, and `/docs` will fail closed
- For scripted access to protected endpoints, you can additionally configure `MEDRIX_GATEWAY_ADMIN_TOKEN` and send it as the `x-medrix-admin-token` header

### Skills and Extensions

- Skills are auto-discovered from `skills/public` and `skills/custom`
- Skill enablement state and MCP configuration are stored together in `extensions_config.json`
- Users can enable or disable skills from the settings page, or drop custom skills directly into `skills/custom`

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
          │ ┌──────────────────┐ │  │  /api/models        Models   │
          │ │    Lead Agent    │ │  │  /api/agents        Agents   │
          │ │                  │ │  │  /api/academic/*    Academic │
          │ │   Multi-Layer    │ │  │  /api/experiments/* Experim. │
          │ │  Middleware Chain │ │  │  /api/threads/*     Threads  │
          │ │       |          │ │  │  /api/skills        Skills   │
          │ │   Tool System    │ │  │  /api/setup/*       Config   │
          │ │       |          │ │  │  /api/mcp/config    MCP Cfg  │
          │ │  Subagents(x3)   │ │  └──────────────────────────────┘
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
- `/api/*` (other) → Gateway API: Models, MCP, Skills, academic research, experiment projects, run/feedback APIs, uploads, and artifacts
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
| 17 | ClarificationMiddleware | Intercepts clarification requests, interrupts graph execution, and feeds the frontend clarification card (must be last) |
| 18 | VisualQualityMiddleware | Visual output quality gate: checks if visual_quality_check was run before presenting visual files, injects reminder if not |

### Tool Ecosystem

| Category | Tools | Description |
|----------|-------|-------------|
| Academic Research | `academic_research` | Structured literature retrieval, metadata normalization, paper deduplication, evidence-card persistence, and APA reference export |
| Experiment Execution | `experiment_lab` | Python-first experiment pipeline, scientific figure routing, and result bundle export |
| Sandbox | bash, ls, read_file, write_file, str_replace | Thread-isolated filesystem operations |
| Built-in | present_files, ask_clarification, view_image, task, visual_quality_check, visual_refinement_check | File presentation, interactive clarification, image understanding, subagent delegation, visual quality gate, iterative refinement check |
| Community | Tavily, Jina AI, Firecrawl, DuckDuckGo | Web search, web scraping, image search |
| MCP | Any MCP-compatible server | Supports stdio/SSE/HTTP transport protocols |
| Skills | Domain-specific workflows | Skill packs discovered from `skills/public` and `skills/custom`, injected based on enablement state |

### Academic / Experiment APIs

| Route | Description |
|-------|-------------|
| `POST /api/academic/projects` | Create or reuse an academic project bound to a `thread_id` and topic |
| `POST /api/academic/projects/{project_id}/ingest` | Retrieve papers from multiple sources, normalize metadata, deduplicate, and build the evidence pool |
| `POST /api/academic/projects/{project_id}/synthesize` | Generate the formal report, APA references, BibTeX, and evidence mapping files |
| `GET /api/academic/projects/{project_id}/references?style=apa7` | Read the APA 7 reference set |
| `POST /api/experiments/projects` | Create an experiment project bound to an expert agent, datasets, and an optional academic project |
| `POST /api/experiments/projects/{project_id}/execute` | Run the experiment pipeline and generate metrics, figures, and result summaries |
| `POST /api/experiments/projects/{project_id}/export` | Export the experiment bundle, optionally including `paper_ready_results.md` |

## Academic Writing Additions

- **Literature review / related work**: given a topic, MedrixFlow can use `academic-researcher` with `academic-deep-research` to expand queries, search multiple academic sources, deduplicate, and build a core paper pool with evidence mappings
- **APA 7 references**: formal report workflows export all verified canonical references for the current project without an export cap, along with `references.md`, `references.bib`, and `retrieval_audit.json`
- **Experiment-backed writing**: `cs-ai-lab` and `bioinformatics-lab` can turn structured datasets or expression analyses into figures, tables, methods, and results bundles, reducing the gap between prose and evidence
- **Local evidence reuse**: academic and experiment projects can be incrementally reused in the same thread, so follow-up literature, references, and experiments do not have to start from scratch
- **Artifact-first delivery**: the right-side artifact panel is now better suited for locating newly generated reports, figures, and references without repeatedly asking the agent to resend them

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
| tectonic | Recommended | Local PDF preview/export for `.tex` files |

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
3. **Configure Tool / Academic Keys** (optional): If you need web search and academic retrieval enhancement, enter Tavily / Jina / OpenAlex / Semantic Scholar API keys
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
│   │   │   ├── middlewares/        #   Middleware components (incl. security audit, token tracking & visual quality gate)
│   │   │   ├── memory/             #   Memory extraction, correction detection, visual preference persistence & pluggable storage
│   │   │   └── thread_state.py     #   Thread state Schema
│   │   ├── academic/               # Academic research pipeline (multi-source retrieval, dedupe, APA export, evidence store / graph projection)
│   │   ├── experiments/            # Experiment workflows (CS/AI + bioinformatics, figure routing, bundle export)
│   │   ├── runtime/                # Runs, message persistence, feedback, and stream bridge
│   │   ├── sandbox/                # Sandbox execution engine + security auditing
│   │   ├── subagents/              # Subagent system (incl. academic-researcher, experiment specialists, visual-specialist)
│   │   ├── tools/                  # Tool collection (incl. academic_research, experiment_lab, visual QA)
│   │   ├── mcp/                    # MCP protocol integration
│   │   ├── models/                 # Model factory + Provider patches
│   │   ├── skills/                 # Skill discovery & loading
│   │   ├── community/              # Community tools (Tavily/Jina/Firecrawl)
│   │   └── config/                 # Config system (hot-reload + env var resolution + system agents)
│   ├── app/gateway/                # FastAPI gateway
│   │   ├── app.py                  #   Application entry point
│   │   └── routers/                #   Route modules (threads/artifacts/agents/academic/experiments/runs/...)
│   ├── tests/                      # Test suite
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
│   │   │   ├── artifacts/          #   Thread artifact inventory, refresh, highlighting, and content loading
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
└── README_en.md                    # This file
```

## Configuration

### Frontend UI Configuration (Recommended)

MedrixFlow supports managing all model and API key configurations directly through the web interface:

- **Model Management**: Add / edit / delete LLM models, supporting preset providers and OpenAI Compatible mode
- **Connectivity Testing**: Each model configuration has a "Test" button that dynamically instantiates the Provider to verify availability
- **Tool API Keys**: Configure Tavily (web search) and Jina (web scraping) keys
- **Instant Effect**: Saving automatically writes to `config.yaml` and `.env`, and the service hot-reloads
- **Capabilities Default On**: Thinking and vision capabilities are enabled by default in model setup; the frontend no longer exposes separate toggles for them

**How to open**: Bottom-left "Settings & More" → "Settings" → "Configuration" tab

### Manual Configuration (Advanced Users)

Edit `config.yaml` in the project root directory directly. Main configuration sections:

| Section | Description |
|---------|-------------|
| `models` | LLM model definitions (class paths, API Keys, capability flags such as `supports_thinking`, `supports_reasoning_effort`, and `supports_vision`) |
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
- Tool / academic API Keys: `TAVILY_API_KEY`, `JINA_API_KEY`, `GITHUB_TOKEN`, `OPENALEX_API_KEY`, `SEMANTIC_SCHOLAR_API_KEY`
- Config overrides: `MEDRIX_FLOW_CONFIG_PATH`, `MEDRIX_FLOW_EXTENSIONS_CONFIG_PATH`

### MCP and Skills Configuration (`extensions_config.json`)

You can copy `extensions_config.example.json` from the project root as a starting point, or manage it from the settings UI.

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
