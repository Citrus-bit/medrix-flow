# MedrixFlow

[English](./README_en.md) | **中文**

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-LangGraph-blue?style=for-the-badge&logo=python" alt="LangGraph">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

MedrixFlow 是一个基于 LangGraph 构建的 AI 超级代理系统，具有沙箱执行、持久化记忆和可扩展工具集成能力。后端使 AI 代理能够执行代码、浏览网页、管理文件、将任务委托给子代理，并在隔离的每个线程环境中保留上下文。

---

## ✨ 特性

### 🤖 智能代理系统
- **主代理 (Lead Agent)**: 基于 LangGraph 的核心代理，支持动态模型选择、思考模式和视觉理解
- **子代理系统**: 支持并行任务执行，最多 3 个子代理并发，每个任务 15 分钟超时
- **中间件链**: 9 个中间件组件，处理线程隔离、文件上传、沙箱管理、记忆提取等

### 🔒 沙箱执行
- **线程隔离**: 每个对话线程拥有独立的文件系统空间
- **虚拟路径**: `/mnt/user-data/{workspace,uploads,outputs}` 自动映射到线程目录
- **工具集**: bash、ls、read_file、write_file、str_replace

### 💾 持久化记忆
- **自动提取**: AI 自动分析对话，提取用户背景、事实和偏好
- **结构化存储**: 用户上下文、历史记录、带置信度评分的事实
- **提示注入**: 顶级事实和上下文注入到代理提示中

### 🛠️ 工具生态系统
| 类别 | 工具 |
|------|------|
| 沙箱 | bash, ls, read_file, write_file, str_replace |
| 内置 | present_files, ask_clarification, view_image, task |
| 社区 | Tavily (网页搜索), Jina AI (网页抓取), Firecrawl, DuckDuckGo (图片搜索) |
| MCP | 支持任何 Model Context Protocol 服务器 |
| Skills | 领域特定工作流，通过系统提示注入 |

### 📱 多渠道支持
- **飞书**: 支持实时流式响应，卡片消息原地更新
- **Slack**: 支持消息交互
- **Telegram**: 支持机器人交互

---

## 🏗️ 架构

```
                        ┌──────────────────────────────────────┐
                        │          Nginx (端口 1000)           │
                        │        统一反向代理服务器               │
                        └───────┬──────────────────┬───────────┘
                                │                  │
              /api/langgraph/*  │                  │  /api/* (其他)
                                ▼                  ▼
               ┌────────────────────┐  ┌────────────────────────┐
               │ LangGraph 服务器    │  │   网关 API (8001)       │
               │    (端口 2024)      │  │   FastAPI REST         │
               │                    │  │                        │
               │ ┌────────────────┐ │  │   模型、MCP、Skills、    │
               │ │     主代理      │ │  │   记忆、上传、产物        │
               │ │  ┌──────────┐  │ │  │                        │
               │ │  │          │  │ │  └────────────────────────┘
               │ │  │ 中间件链  │  │ │
               │ │  └──────────┘  │ │
               │ │  ┌──────────┐  │ │
               │ │  │  工具集   │  │ │
               │ │  └──────────┘  │ │
               │ │  ┌──────────┐  │ │
               │ │  │ 子代理    │  │ │
               │ │  └──────────┘  │ │
               │ └────────────────┘ │
               └────────────────────┘
```

**请求路由** (通过 Nginx):
- `/api/langgraph/*` → LangGraph 服务器 - 代理交互、线程、流式传输
- `/api/*` (其他) → 网关 API - 模型、MCP、skills、记忆、产物、上传
- `/` (非 API) → 前端 - Next.js Web 界面

---

## 🚀 快速开始

只需 4 步即可运行 MedrixFlow，**无需手动编辑任何配置文件**。

### 1. 安装前置工具

| 工具 | 版本要求 | 安装方式 |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| uv | 最新版 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 10+ | `npm install -g pnpm` |
| nginx | - | macOS: `brew install nginx`，Linux: `sudo apt install nginx` |

### 2. 克隆 & 安装依赖

```bash
git clone https://github.com/Citrus-bit/medrix-flow.git
cd medrix-flow
make config    # 自动生成配置文件（首次运行）
make install   # 一键安装前后端依赖
```

### 3. 启动

```bash
make stop && make dev       # 启动所有服务（LangGraph + 网关 + 前端 + Nginx）
```

启动完成后，浏览器会自动打开 **http://localhost:1000**。

### 4. 配置模型 & API 密钥

首次打开页面时，设置面板会自动弹出，引导你完成配置：

1. 在「配置」页面添加你的 LLM 模型（支持 OpenAI、Anthropic、Google Gemini、DeepSeek 等）
2. 填入模型 API Key，点击「测试」验证连通性
3. 如需网页搜索/抓取功能，填入 Tavily / Jina 的 API Key
4. 点击「保存配置」—— 完成！

> 你也可以随时通过左下角的「设置和更多」→「设置」重新打开配置面板。

### 常用命令

| 命令 | 说明 |
|------|------|
| `make dev` | 启动所有服务（开发模式，支持热重载） |
| `make stop` | 停止所有服务 |
| `make check` | 检查前置工具是否已安装 |
| `make clean` | 停止服务并清理临时文件 |

---

## 📁 项目结构

```
medrix-flow/
├── backend/                    # 后端服务
│   ├── src/
│   │   ├── agents/            # 代理系统
│   │   │   ├── lead_agent/    # 主代理 (工厂、提示词)
│   │   │   ├── middlewares/   # 9 个中间件组件
│   │   │   ├── memory/        # 记忆提取与存储
│   │   │   └── thread_state.py
│   │   ├── gateway/           # FastAPI 网关
│   │   │   ├── app.py
│   │   │   └── routers/      # 路由模块
│   │   ├── sandbox/          # 沙箱执行
│   │   ├── subagents/        # 子代理系统
│   │   ├── tools/            # 工具集
│   │   ├── mcp/              # MCP 协议集成
│   │   ├── models/           # 模型工厂
│   │   ├── skills/           # Skill 发现与加载
│   │   └── config/           # 配置系统
│   ├── docs/                 # 文档
│   ├── tests/                # 测试
│   ├── pyproject.toml        # Python 依赖
│   └── Makefile              # 开发命令
│
├── frontend/                  # 前端应用
│   ├── src/
│   │   ├── app/              # Next.js App Router
│   │   ├── components/       # React 组件
│   │   ├── core/             # 核心业务逻辑
│   │   ├── hooks/            # 自定义 Hooks
│   │   └── lib/              # 共享库
│   ├── public/               # 静态资源
│   ├── package.json          # Node 依赖
│   └── README.md             # 前端文档
│
├── skills/                   # 技能系统
│   ├── public/               # 公共技能
│   └── custom/               # 自定义技能
│
├── scripts/                  # 脚本工具
├── logs/                     # 日志文件
├── docker/                   # Docker 配置
├── config.example.yaml       # 配置示例
├── Makefile                  # 根目录命令
└── README.md                 # 本文件
```

---

## ⚙️ 配置说明

### 前端配置（推荐）

MedrixFlow 支持通过 Web 界面直接管理模型和 API 密钥，无需手动编辑配置文件：

- **模型配置**：添加/编辑/删除 LLM 模型，支持一键测试连通性
- **工具 API Key**：配置 Tavily（网页搜索）和 Jina（网页抓取）的密钥
- **保存即生效**：所有更改自动持久化到 `config.yaml` 和 `.env`，服务自动热重载

打开方式：左下角「设置和更多」→「设置」→「配置」标签页。

### 手动配置（高级用户）

如需更精细的控制，可以直接编辑项目根目录下的 `config.yaml`：

主要配置项:
- `models` - LLM 模型配置 (类路径、API 密钥、思考/视觉支持)
- `tools` - 工具定义 (模块路径和分组)
- `tool_groups` - 逻辑工具分组
- `sandbox` - 执行环境提供者
- `skills` - Skills 目录路径
- `title` - 自动标题生成设置
- `summarization` - 上下文摘要设置
- `subagents` - 子代理系统 (启用/禁用)
- `memory` - 记忆系统设置

### 扩展配置 (`extensions_config.json`)

MCP 服务器和 skill 状态的统一配置:

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

### 环境变量

- `MEDRIX_FLOW_CONFIG_PATH` - 覆盖 config.yaml 位置
- `MEDRIX_FLOW_EXTENSIONS_CONFIG_PATH` - 覆盖 extensions_config.json 位置
- 模型 API 密钥: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `DEEPSEEK_API_KEY` 等
- 工具 API 密钥: `TAVILY_API_KEY`, `GITHUB_TOKEN` 等

---

## 🛠️ 技术栈

### 后端
- **LangGraph** (1.0.6+) - 代理框架和多代理编排
- **LangChain** (1.2.3+) - LLM 抽象和工具系统
- **FastAPI** (0.115.0+) - 网关 REST API
- **langchain-mcp-adapters** - Model Context Protocol 支持
- **agent-sandbox** - 沙箱代码执行
- **markitdown** - 多格式文档转换
- **tavily-python** / **firecrawl-py** - 网页搜索和抓取

### 前端
- **Next.js 16** - React 框架 (App Router)
- **React 19** - UI 库
- **Tailwind CSS 4** - 样式框架
- **Shadcn UI** - UI 组件库
- **MagicUI** - 现代 UI 组件
- **LangGraph SDK** - 代理交互
- **Vercel AI Elements** - AI UI 元素

---

## 📖 文档

- [配置指南](./backend/docs/CONFIGURATION.md)
- [架构详解](./backend/docs/ARCHITECTURE.md)
- [API 参考](./backend/docs/API.md)
- [文件上传](./backend/docs/FILE_UPLOAD.md)
- [路径示例](./backend/docs/PATH_EXAMPLES.md)
- [上下文摘要](./backend/docs/summarization.md)
- [计划模式](./backend/docs/plan_mode_usage.md)
- [安装指南](./backend/docs/SETUP.md)

---

## 📄 许可证

MIT License - 查看 [LICENSE](./LICENSE) 文件了解更多详情。

---

## 🌟 鸣谢

- [LangGraph](https://langchain-ai.github.io/langgraph/) - 强大的图状态机框架
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架
- [Next.js](https://nextjs.org/) - React 元框架
- 所有开源库的贡献者
