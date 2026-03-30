# 🧬 MedrixFlow - 2.0

[English](./README.md) | 中文

[![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)](./backend/pyproject.toml)
[![Node.js](https://img.shields.io/badge/Node.js-22%2B-339933?logo=node.js&logoColor=white)](./Makefile)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)


MedrixFlow（**Med**ical **R**esearch **I**ntelligence and Data-driven e**X**ploration **Flow**）是一个开源的**超级智能体框架**，通过编排**子智能体**、**记忆系统**和**沙箱环境**来完成各种任务——由**可扩展技能**驱动。


## 目录

- [🧬 MedrixFlow - 2.0](#-medrixflow---20)
  - [目录](#目录)
  - [快速开始](#快速开始)
    - [配置](#配置)
    - [运行应用](#运行应用)
      - [选项 1：Docker（推荐）](#选项-1docker推荐)
      - [选项 2：本地开发](#选项-2本地开发)
    - [高级功能](#高级功能)
      - [沙箱模式](#沙箱模式)
      - [MCP 服务器](#mcp-服务器)
      - [即时通讯渠道](#即时通讯渠道)
  - [从深度研究到超级智能体框架](#从深度研究到超级智能体框架)
  - [核心功能](#核心功能)
    - [技能与工具](#技能与工具)
      - [Claude Code 集成](#claude-code-集成)
    - [子智能体](#子智能体)
    - [沙箱与文件系统](#沙箱与文件系统)
    - [上下文工程](#上下文工程)
    - [长期记忆](#长期记忆)
  - [推荐模型](#推荐模型)
  - [嵌入式 Python 客户端](#嵌入式-python-客户端)
  - [文档](#文档)
  - [贡献指南](#贡献指南)
  - [许可证](#许可证)
  - [致谢](#致谢)
  - [Star 历史](#star-历史)

## 快速开始

### 配置

1. **克隆 MedrixFlow 仓库**

   ```bash
   git clone https://github.com/your-org/medrix-flow.git
   cd medrix-flow
   ```

2. **生成本地配置文件**

   在项目根目录（`medrix-flow/`）下运行：

   ```bash
   make config
   ```

   此命令会根据提供的示例模板创建本地配置文件。

3. **配置您偏好的模型**

   编辑 `config.yaml` 并定义至少一个模型：

   ```yaml
   models:
     - name: gpt-4                       # 内部标识符
       display_name: GPT-4               # 显示名称
       use: langchain_openai:ChatOpenAI  # LangChain 类路径
       model: gpt-4                      # API 模型标识符
       api_key: $OPENAI_API_KEY          # API 密钥（推荐使用环境变量）
       max_tokens: 4096                  # 每次请求的最大 token 数
       temperature: 0.7                  # 采样温度

     - name: openrouter-gemini-2.5-flash
       display_name: Gemini 2.5 Flash (OpenRouter)
       use: langchain_openai:ChatOpenAI
       model: google/gemini-2.5-flash-preview
       api_key: $OPENAI_API_KEY          # OpenRouter 仍使用 OpenAI 兼容的字段名
       base_url: https://openrouter.ai/api/v1

     - name: gpt-5-responses
       display_name: GPT-5 (Responses API)
       use: langchain_openai:ChatOpenAI
       model: gpt-5
       api_key: $OPENAI_API_KEY
       use_responses_api: true
       output_version: responses/v1
   ```

   OpenRouter 和类似的 OpenAI 兼容网关应使用 `langchain_openai:ChatOpenAI` 加上 `base_url` 进行配置。如果您偏好提供商特定的环境变量名称，请将 `api_key` 显式指向该变量（例如 `api_key: $OPENROUTER_API_KEY`）。

   要将 OpenAI 模型路由到 `/v1/responses`，继续使用 `langchain_openai:ChatOpenAI` 并设置 `use_responses_api: true` 和 `output_version: responses/v1`。

   CLI 支持的提供商示例：

   ```yaml
   models:
     - name: gpt-5.4
       display_name: GPT-5.4 (Codex CLI)
       use: medrix_flow.models.openai_codex_provider:CodexChatModel
       model: gpt-5.4
       supports_thinking: true
       supports_reasoning_effort: true

     - name: claude-sonnet-4.6
       display_name: Claude Sonnet 4.6 (Claude Code OAuth)
       use: medrix_flow.models.claude_provider:ClaudeChatModel
       model: claude-sonnet-4-6
       max_tokens: 4096
       supports_thinking: true
   ```

   - Codex CLI 读取 `~/.codex/auth.json`
   - Codex Responses 端点目前拒绝 `max_tokens` 和 `max_output_tokens`，因此 `CodexChatModel` 不暴露请求级别的 token 上限
   - Claude Code 接受 `CLAUDE_CODE_OAUTH_TOKEN`、`ANTHROPIC_AUTH_TOKEN`、`CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR`、`CLAUDE_CODE_CREDENTIALS_PATH`，或明文 `~/.claude/.credentials.json`
   - 在 macOS 上，MedrixFlow 不会自动探测 Keychain。如有需要，请显式导出 Claude Code 认证：

   ```bash
   eval "$(python3 scripts/export_claude_code_oauth.py --print-export)"
   ```
   
4. **为已配置的模型设置 API 密钥**

   选择以下方法之一：

   - 方法 A：编辑项目根目录的 `.env` 文件（推荐）

   ```bash
   TAVILY_API_KEY=your-tavily-api-key
   OPENAI_API_KEY=your-openai-api-key
   # OpenRouter 在配置使用 langchain_openai:ChatOpenAI + base_url 时也使用 OPENAI_API_KEY
   # 根据需要添加其他提供商密钥
   INFOQUEST_API_KEY=your-infoquest-api-key
   ```

   - 方法 B：在 shell 中导出环境变量

   ```bash
   export OPENAI_API_KEY=your-openai-api-key
   ```

   对于 CLI 支持的提供商：
   - Codex CLI: `~/.codex/auth.json`
   - Claude Code OAuth: 显式环境变量/文件传递或 `~/.claude/.credentials.json`

   - 方法 C：直接编辑 `config.yaml`（生产环境不推荐）

   ```yaml
   models:
     - name: gpt-4
       api_key: your-actual-api-key-here  # 替换占位符
   ```

### 运行应用

#### 选项 1：Docker（推荐）

**开发**（热重载，源码挂载）：

```bash
make docker-init    # 拉取沙箱镜像（仅在首次或镜像更新时运行）
make docker-start   # 启动服务（根据 config.yaml 自动检测沙箱模式）
```

`make docker-start` 仅在 `config.yaml` 使用 provisioner 模式时（`sandbox.use: medrix_flow.community.aio_sandbox:AioSandboxProvider` 配合 `provisioner_url`）才会启动 `provisioner`。
后端进程会在下次访问配置时自动获取 `config.yaml` 的更改，因此模型元数据更新不需要在开发过程中手动重启。

**生产**（本地构建镜像，挂载运行时配置和数据）：

```bash
make up     # 构建镜像并启动所有生产服务
make down   # 停止并移除容器
```

> [!NOTE]
> LangGraph 智能体服务器目前通过 `langgraph dev`（开源 CLI 服务器）运行。

访问地址：http://localhost:1000

#### 选项 2：本地开发

如果您偏好本地运行服务：

前置条件：先完成上述"配置"步骤（`make config` 和模型 API 密钥）。`make dev` 需要有效的配置文件（默认为项目根目录的 `config.yaml`；可通过 `MEDRIX_FLOW_CONFIG_PATH` 覆盖）。

1. **检查前置条件**：
   ```bash
   make check  # 验证 Node.js 22+、pnpm、uv、nginx
   ```

2. **安装依赖**：
   ```bash
   make install  # 安装后端和前端依赖
   ```

3. **（可选）预拉取沙箱镜像**：
   ```bash
   # 如果使用 Docker/容器化沙箱，建议执行
   make setup-sandbox
   ```

4. **启动服务**：
   ```bash
   make dev
   ```

5. **访问**：http://localhost:1000

### 高级功能

#### 沙箱模式

MedrixFlow 支持多种沙箱执行模式：
- **本地执行**（直接在主机上运行沙箱代码）
- **Docker 执行**（在隔离的 Docker 容器中运行沙箱代码）
- **Kubernetes Docker 执行**（通过 provisioner 服务在 Kubernetes Pod 中运行沙箱代码）

对于 Docker 开发，服务启动遵循 `config.yaml` 中的沙箱模式。在本地/Docker 模式下，`provisioner` 不会启动。

请参阅[沙箱配置指南](backend/docs/CONFIGURATION.md#sandbox)配置您偏好的模式。

#### MCP 服务器

MedrixFlow 支持可配置的 MCP 服务器和技能以扩展其功能。
对于 HTTP/SSE MCP 服务器，支持 OAuth 令牌流程（`client_credentials`、`refresh_token`）。
请参阅 [MCP 服务器指南](backend/docs/MCP_SERVER.md)获取详细说明。

#### 即时通讯渠道

MedrixFlow 支持从消息应用接收任务。渠道配置后会自动启动——无需公网 IP。

| 渠道 | 传输方式 | 难度 |
|---------|-----------|------------|
| Telegram | Bot API（长轮询） | 简单 |
| Slack | Socket 模式 | 中等 |
| 飞书/ Lark | WebSocket | 中等 |

**在 `config.yaml` 中配置：**

```yaml
channels:
  # LangGraph 服务器 URL（默认：http://localhost:2024）
  langgraph_url: http://localhost:2024
  # Gateway API URL（默认：http://localhost:8001）
  gateway_url: http://localhost:8001

  # 可选：所有移动端渠道的全局会话默认值
  session:
    assistant_id: lead_agent
    config:
      recursion_limit: 100
    context:
      thinking_enabled: true
      is_plan_mode: false
      subagent_enabled: false

  feishu:
    enabled: true
    app_id: $FEISHU_APP_ID
    app_secret: $FEISHU_APP_SECRET

  slack:
    enabled: true
    bot_token: $SLACK_BOT_TOKEN     # xoxb-...
    app_token: $SLACK_APP_TOKEN     # xapp-... (Socket 模式)
    allowed_users: []               # 空 = 允许所有

  telegram:
    enabled: true
    bot_token: $TELEGRAM_BOT_TOKEN
    allowed_users: []               # 空 = 允许所有

    # 可选：每个渠道/用户的会话设置
    session:
      assistant_id: mobile_agent
      context:
        thinking_enabled: false
      users:
        "123456789":
          assistant_id: vip_agent
          config:
            recursion_limit: 150
          context:
            thinking_enabled: true
            subagent_enabled: true
```

在 `.env` 文件中设置相应的 API 密钥：

```bash
# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...

# 飞书 / Lark
FEISHU_APP_ID=cli_xxxx
FEISHU_APP_SECRET=your_app_secret
```

**Telegram 设置**

1. 与 [@BotFather](https://t.me/BotFather) 对话，发送 `/newbot`，然后复制 HTTP API 令牌。
2. 在 `.env` 中设置 `TELEGRAM_BOT_TOKEN` 并在 `config.yaml` 中启用该渠道。

**Slack 设置**

1. 在 [api.slack.com/apps](https://api.slack.com/apps) 创建 Slack 应用 → 创建新应用 → 从头开始。
2. 在 **OAuth & Permissions** 中，添加 Bot Token 权限范围：`app_mentions:read`、`chat:write`、`im:history`、`im:read`、`im:write`、`files:write`。
3. 启用 **Socket 模式** → 生成 App-Level Token（`xapp-…`），包含 `connections:write` 权限范围。
4. 在 **Event Subscriptions** 中，订阅机器人事件：`app_mention`、`message.im`。
5. 在 `.env` 中设置 `SLACK_BOT_TOKEN` 和 `SLACK_APP_TOKEN` 并在 `config.yaml` 中启用该渠道。

**飞书/ Lark 设置**

1. 在[飞书开放平台](https://open.feishu.cn/)创建应用 → 启用 **Bot** 能力。
2. 添加权限：`im:message`、`im:message.p2p_msg:readonly`、`im:resource`。
3. 在 **事件** 中，订阅 `im.message.receive_v1` 并选择 **长连接** 模式。
4. 复制 App ID 和 App Secret。在 `.env` 中设置 `FEISHU_APP_ID` 和 `FEISHU_APP_SECRET` 并在 `config.yaml` 中启用该渠道。

**命令**

渠道连接后，您可以直接在聊天中与 MedrixFlow 交互：

| 命令 | 描述 |
|---------|-------------|
| `/new` | 开始新对话 |
| `/status` | 显示当前线程信息 |
| `/models` | 列出可用模型 |
| `/memory` | 查看记忆 |
| `/help` | 显示帮助 |

> 没有命令前缀的消息会被视为普通聊天——MedrixFlow 会创建线程并进行对话式回复。

## 从深度研究到超级智能体框架

MedrixFlow 始于深度研究框架——社区用它做了更多的事情。自发布以来，开发者们用它构建数据管道、生成幻灯片、创建仪表板、自动化内容工作流——这些都是我们未曾预料的。

这告诉我们一个重要的道理：MedrixFlow 不仅仅是一个研究工具。它是一个**框架**——一个为智能体提供基础设施来完成实际工作的运行时。

所以我们从头重建了它。

MedrixFlow 2.0 不再是一个需要自己集成的框架。它是一个超级智能体框架——开箱即用，完全可扩展。基于 LangGraph 和 LangChain 构建，它内置了智能体所需的一切：文件系统、记忆、技能、沙箱执行，以及规划和生成子智能体来处理复杂多步骤任务的能力。

直接使用它。或者拆分成你想要的样子。

## 核心功能

### 技能与工具

技能是让 MedrixFlow 几乎能完成任何事情的原因。

标准的智能体技能是一个结构化的能力模块——一个 Markdown 文件，定义了工作流程、最佳实践和相关资源引用。MedrixFlow 内置了用于研究、报告生成、幻灯片创建、网页、图片和视频生成的技能。但真正的力量在于可扩展性：添加您自己的技能、替换内置技能，或将它们组合成复合工作流。

技能是渐进式加载的——只在任务需要时加载，而不是一次性全部加载。这保持了上下文窗口的精简，使 MedrixFlow 即使对 token 敏感模型也能良好运行。

当您通过 Gateway 安装 `.skill` 档案时，MedrixFlow 接受标准的可选 frontmatter 元数据（如 `version`、`author` 和 `compatibility`），而不是拒绝其他有效的外部技能。

工具遵循相同的理念。MedrixFlow 附带核心工具集——网络搜索、网络获取、文件操作、bash 执行——并通过 MCP 服务器和 Python 函数支持自定义工具。替换任何东西。添加任何东西。

Gateway 生成的跟进建议现在会在解析 JSON 数组响应之前规范化纯字符串模型输出和块/列表风格的富内容，因此特定提供商的内容包装器不会静默丢弃建议。

```
# 沙箱容器内的路径
/mnt/skills/public
├── research/SKILL.md
├── report-generation/SKILL.md
├── slide-creation/SKILL.md
├── web-page/SKILL.md
└── image-generation/SKILL.md

/mnt/skills/custom
└── your-custom-skill/SKILL.md      ← 您的自定义技能
```

#### Claude Code 集成

`claude-to-medrix_flow` 技能让您可以直接从 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 与运行的 MedrixFlow 实例交互。发送研究任务、检查状态、管理线程——无需离开终端。

**安装技能**：

```bash
npx skills add https://github.com/your-org/medrix-flow --skill claude-to-medrix_flow
```

然后确保 MedrixFlow 正在运行（默认地址 `http://localhost:2026`），并在 Claude Code 中使用 `/claude-to-medrix_flow` 命令。

**您可以做的事情**：
- 向 MedrixFlow 发送消息并获取流式响应
- 选择执行模式：flash（快速）、standard、pro（规划）、ultra（子智能体）
- 检查 MedrixFlow 健康状况、列出模型/技能/智能体
- 管理线程和对话历史
- 上传文件进行分析

**环境变量**（可选，用于自定义端点）：

```bash
MEDRIXFLOW_URL=http://localhost:2026            # 统一代理基础 URL
MEDRIXFLOW_GATEWAY_URL=http://localhost:2026    # Gateway API
MEDRIXFLOW_LANGGRAPH_URL=http://localhost:2026/api/langgraph  # LangGraph API
```

请参阅 [`skills/public/claude-to-medrix_flow/SKILL.md`](skills/public/claude-to-medrix_flow/SKILL.md) 获取完整的 API 参考。

### 子智能体

复杂任务很少能一次完成。MedrixFlow 会分解它们。

主智能体可以动态生成子智能体——每个子智能体都有自己的作用域上下文、工具和终止条件。子智能体在可能的情况下并行运行，返回结构化的结果，主智能体将所有内容综合成连贯的输出。

这就是 MedrixFlow 处理需要分钟到小时的任务的方式：一个研究任务可能会分散成十几个子智能体，每个子智能体探索不同的角度，然后汇聚成一份报告——或者一个网站——或者一份带有生成视觉效果的幻灯片。一个框架，多种能力。

### 沙箱与文件系统

MedrixFlow 不仅仅是*谈论*做事情。它有自己的计算机。

每个任务都在一个隔离的 Docker 容器中运行，拥有完整的文件系统——技能、工作区、上传、输出。智能体读取、写入和编辑文件。它执行 bash 命令和代码。它查看图片。全部沙箱化，全部可审计，会话之间零污染。

这就是拥有工具访问权限的聊天机器人和拥有实际执行环境的智能体之间的区别。

```
# 沙箱容器内的路径
/mnt/user-data/
├── uploads/          ← 您的文件
├── workspace/        ← 智能体的工作目录
└── outputs/          ← 最终交付物
```

### 上下文工程

**隔离的子智能体上下文**：每个子智能体都在自己的隔离上下文中运行。这意味着子智能体将无法看到主智能体或其他子智能体的上下文。这对于确保子智能体能够专注于当前任务而不被主智能体或其他子智能体的上下文分心非常重要。

**摘要**：在会话期间，MedrixFlow 积极管理上下文——总结已完成的子任务，将中间结果卸载到文件系统，压缩不再立即相关的内容。这使其能够在漫长的多步骤任务中保持敏锐，而不会耗尽上下文窗口。

### 长期记忆

大多数智能体在对话结束的那一刻就会忘记一切。MedrixFlow 会记住一切。

跨会话，MedrixFlow 会构建关于您的个人资料、偏好和积累知识的持久记忆。您使用得越多，它就越了解您——您的写作风格、您的技术栈、您反复出现的工作流程。记忆存储在本地，由您控制。

记忆更新现在会在应用时跳过重复的事实条目，因此重复的偏好和上下文不会在会话中无限累积。

## 推荐模型

MedrixFlow 与任何实现 OpenAI 兼容 API 的 LLM 配合使用——它是模型无关的。也就是说，它在支持以下功能的模型上表现最佳：

- **长上下文窗口**（100k+ token），用于深度研究和多步骤任务
- **推理能力**，用于自适应规划和复杂分解
- **多模态输入**，用于图像理解和视频理解
- **强大的工具使用能力**，用于可靠的函数调用和结构化输出

## 嵌入式 Python 客户端

MedrixFlow 可以作为嵌入式 Python 库使用，无需运行完整的 HTTP 服务。`MedrixFlowClient` 提供对所有智能体和 Gateway 功能的直接进程内访问，返回与 HTTP Gateway API 相同的响应模式。HTTP Gateway 还暴露 `DELETE /api/threads/{thread_id}`，用于在 LangGraph 线程本身被删除后移除 MedrixFlow 管理的本地线程数据：

```python
from medrix_flow.client import MedrixFlowClient

client = MedrixFlowClient()

# 对话
response = client.chat("Analyze this paper for me", thread_id="my-thread")

# 流式传输（LangGraph SSE 协议：values, messages-tuple, end）
for event in client.stream("hello"):
    if event.type == "messages-tuple" and event.data.get("type") == "ai":
        print(event.data["content"])

# 配置与管理 —— 返回与 Gateway 对齐的字典
models = client.list_models()        # {"models": [...]}
skills = client.list_skills()        # {"skills": [...]}
client.update_skill("web-search", enabled=True)
client.upload_files("thread-1", ["./report.pdf"])  # {"success": True, "files": [...]}
```

所有返回字典的方法都在 CI 中针对 Gateway Pydantic 响应模型进行验证（`TestGatewayConformance`），确保嵌入式客户端与 HTTP API 模式保持同步。请参阅 `backend/packages/harness/medrix_flow/client.py` 获取完整的 API 文档。

## 文档

- [贡献指南](CONTRIBUTING.md) - 开发环境设置和工作流程
- [配置指南](backend/docs/CONFIGURATION.md) - 设置和配置说明
- [架构概览](backend/CLAUDE.md) - 技术架构细节
- [后端架构](backend/README.md) - 后端架构和 API 参考

## 贡献指南

我们欢迎贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解开发设置、工作流程和指南。

回归测试覆盖包括 Docker 沙箱模式检测和 provisioner kubeconfig-path 处理测试，位于 `backend/tests/` 中。

## 许可证

本项目是开源的，基于 [MIT 许可证](./LICENSE)。

## 致谢

MedrixFlow 基于开源社区的出色工作构建。我们深深感激所有使 MedrixFlow 成为可能的项目和贡献者。确实，我们站在巨人的肩膀上。

我们衷心感谢以下项目的宝贵贡献：

- **[LangChain](https://github.com/langchain-ai/langchain)**：他们卓越的框架为我们的 LLM 交互和链提供了动力，实现了无缝集成和功能。
- **[LangGraph](https://github.com/langchain-ai/langgraph)**：他们创新的多智能体编排方法对于实现 MedrixFlow 的复杂工作流程起到了关键作用。

这些项目体现了开源协作的变革力量，我们很荣幸能够基于它们的基础进行构建。

## Star 历史

[![Star History Chart](https://api.star-history.com/svg?repos=your-org/medrix-flow&type=Date)](https://star-history.com/#your-org/medrix-flow&Date)
