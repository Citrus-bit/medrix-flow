# MedrixFlow

[English](./README_en.md) | **中文**

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-LangGraph-blue?style=for-the-badge&logo=python" alt="LangGraph">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" alt="React 19">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <b>基于 LangGraph 构建的 AI 超级代理系统</b><br/>
  沙箱执行 · 持久化记忆 · 多代理协作 · 可扩展工具生态
</p>

---

MedrixFlow 是一个全栈 AI 代理编排平台，后端基于 LangGraph 实现多代理协作与状态管理，前端基于 Next.js 16 提供现代化交互界面。系统支持在隔离的线程级沙箱中执行代码、浏览网页、管理文件，并通过持久化记忆在跨对话间保留用户上下文。

## 技术亮点

### 1. LangGraph 驱动的多代理编排

区别于简单的 LLM 链式调用，MedrixFlow 采用 **LangGraph 有向图状态机** 作为核心编排引擎：

- **Lead Agent + Subagent 分层架构**：主代理负责任务理解与拆分，最多 3 个子代理并行执行，每个任务独立 15 分钟超时控制
- **16+ 层中间件链**：按严格顺序执行的中间件流水线，覆盖线程隔离、文件上传注入、沙箱生命周期、安全审计、上下文摘要、记忆提取、图像视觉、循环检测、工具错误降级、Token 用量追踪、视觉质量门控等横切关注点
- **动态模型热切换**：同一对话内可在不同 LLM 之间切换，支持 Thinking 模式、Vision 模式的运行时启停

### 2. 线程级沙箱隔离

每个对话线程拥有完全隔离的执行环境：

- **虚拟文件系统映射**：`/mnt/user-data/{workspace,uploads,outputs}` 自动映射到线程专属物理目录，杜绝跨线程数据泄露
- **双沙箱引擎**：支持本地直接执行（LocalSandboxProvider）和 Docker 容器隔离（AioSandboxProvider），生产环境可切换至 K3s Pod 级别隔离
- **工具链完整覆盖**：bash 执行、文件读写、字符串替换、目录浏览 - 代理拥有完整的文件系统操作能力

### 3. LLM 驱动的持久化记忆

不同于简单的对话历史拼接，MedrixFlow 实现了结构化的长期记忆系统：

- **自动知识抽取**：由 LLM 分析对话内容，自动提取用户背景（职业、偏好）、事实（带置信度评分）和上下文
- **用户纠正检测**：11 条中英文正则模式实时检测用户纠正意图（如「不对」「其实是」「actually」），触发记忆优先更新，避免错误事实被持久化
- **防抖批处理**：通过可配置的 debounce 机制（默认 30s）聚合多轮对话变化，减少 LLM 调用开销
- **可插拔存储后端**：默认 JSON 文件存储（`FileMemoryStorage`），支持通过配置 `storage_class` 切换为任意自定义存储实现（如 SQLite、Redis）
- **System Prompt 注入**：高置信度事实与用户上下文自动注入代理提示词，实现跨对话的个性化响应

### 4. 流式传输与断连恢复

基于 LangGraph SDK 的 useStream 实现生产级流式体验：

- **SSE 流式渲染**：Agent 响应、Thinking 过程、子代理任务进度全部实时流式展示
- **断连自动恢复**：reconnectOnMount + streamResumable 机制确保页面刷新或网络断连后自动重连，后端继续运行不中断
- **乐观 UI 更新**：消息发送即刻展示，线程列表 optimistic 插入，消除网络延迟感知

### 5. 前端配置即用（Zero-Config UX）

模型和 API Key 配置完全在前端 UI 完成，无需手动编辑任何配置文件：

- **首次访问自动引导**：新标签页自动弹出配置面板，通过 sessionStorage 确保同一浏览器会话只触发一次
- **一键测试连通性**：动态实例化 Provider 类发送 ainvoke("Hi") 验证模型可用性
- **热重载生效**：配置保存后自动写入 config.yaml + .env，调用 reload_app_config() 即时生效，无需重启服务

### 6. 多渠道接入（IM 集成）

除 Web 界面外，还支持 IM 渠道接入：

- **飞书**：实时流式响应，卡片消息原地更新（存储 message_id 逐块 patch 同一卡片）
- **Slack**：Socket Mode WebSocket 连接，无需公网 IP
- **Telegram**：Bot 交互，支持每用户独立会话配置

### 7. 视觉输出质量系统

MedrixFlow 内置了专业级视觉输出质量保障体系，覆盖图表、PPT、图片生成全链路：

- **提示词约束注入**：当视觉类技能激活时，自动注入设计标准（60-30-10 配色规则、排版层次、8pt 网格间距、无障碍对比度）、任务专属规则（图表/PPT/图片各有针对性约束）以及强制工作流（澄清 → 规格 → 自审 → 迭代 → 交付）
- **质量门控工具**：`visual_quality_check` 在交付前执行结构化自检（图表 5 项、PPT 5 项、图片 5 项），返回 PASS / FAIL / FIXED 状态；`visual_refinement_check` 支持迭代精修，按内容准确性、风格匹配、色彩保真度等维度评分 1-10，低于 7 分自动触发重做（最多 3 轮）
- **中间件强制执行**：`VisualQualityMiddleware` 在代理调用 `present_files` 交付视觉文件时，检测是否已运行质量检查，未通过则注入提醒
- **专用视觉子代理**：`visual-specialist` 子代理内置设计专业知识和完整的质量工作流，Lead Agent 可将图表、PPT、图片任务委派给它
- **记忆偏好持久化**：记忆系统新增 `visual_preference` 事实类别，跨对话保留用户的配色偏好、字体选择、品牌规范等设计偏好
- **设计资源库**：内置 12 套专业配色方案（商务蓝、科技紫、医疗绿、无障碍高对比等）、5 套图表场景预设（高管仪表盘、技术报告、营销报告等）、5 套 PPT 场景预设（路演、季报、产品发布等），代理可自动匹配并引用
- **PPT 脚本增强**：`generate.py` 新增幻灯片切换动画、演讲者备注、封面/包含图片适配模式、元数据（作者/关键词）支持

### 8. 安全审计与可观测性

系统内置安全审计和 Token 用量追踪能力，无需外部工具：

- **Bash 命令安全审计**：`SandboxAuditMiddleware` 对每条 bash 工具调用进行三级分类（block / warn / pass），结合配置中的 `allow_host_bash` 开关，自动阻断高危命令（`rm -rf /`、`curl | sh` 等），警告中危操作（`chmod`、`kill` 等），全量审计日志输出
- **Token 用量追踪**：`TokenUsageMiddleware` 在每次 LLM 调用后记录 input / output / total token 数量，为成本监控和配额管理提供数据基础
- **沙箱安全感知**：`security.py` 提供 `uses_local_sandbox_provider()` 和 `is_host_bash_allowed()` 工具函数，运行时动态判断当前沙箱安全等级

## 技术难点与解决方案

### 中间件编排的顺序依赖

**难点**：16+ 个中间件各自处理不同的横切关注点，但彼此存在隐式依赖。例如 SandboxMiddleware 必须在 UploadsMiddleware 之后（需要线程目录已创建），ClarificationMiddleware 必须在最后（需要中断图执行），SandboxAuditMiddleware 必须在 ToolErrorHandling 之后（需要拦截已包装的工具调用）。

**方案**：采用显式有序中间件链模式，每个中间件声明其执行阶段，运行时按固定顺序串行执行。中间件列表包括：ThreadData -> Uploads -> Sandbox -> DanglingToolCall -> (Guardrail) -> ToolErrorHandling -> (Summarization) -> (TodoList) -> Title -> Memory -> (ViewImage) -> (DeferredToolFilter) -> (SubagentLimit) -> LoopDetection -> SandboxAudit -> TokenUsage -> Clarification。

### 流式传输的状态一致性

**难点**：SSE 流式传输中，前端需要同时处理多种流类型（消息、Thinking 推理、子代理任务事件、工具调用），且页面刷新后需要恢复流状态。Safari 浏览器对 SSE 重连行为不一致。

**方案**：
- 使用 sessionStorage 存储 `lg:stream:{threadId}` 到 `runId` 的映射，实现 `reconnectOnMount` 断点续传
- 后端设置 `onDisconnect: "continue"` 确保客户端断连后运行不中断
- 线程列表添加 `refetchOnWindowFocus`、`staleTime: 30s`、`visibilitychange` 监听器修复 Safari 兼容性
- 子代理任务通过 `onCustomEvent` 触发 `useUpdateSubtask()` 实时更新 SubtaskCard

### 配置热重载的一致性

**难点**：config.yaml 和 .env 由前端 UI 修改后需要立即生效，但 LangGraph Server、Gateway API、前端三个进程各自持有配置缓存。

**方案**：AppConfig 单例采用 mtime 文件修改时间检测 + 自动热重载机制。Gateway API 每次请求通过 `get_app_config()` 获取配置时自动检查文件变更，LangGraph Server 在 Gateway 的 `--reload` 模式下监听 yaml 文件变化自动重启。环境变量通过 `load_dotenv` + `resolve_env_variables` 递归替换 `$VAR` 引用。

### 长对话的上下文管理

**难点**：长对话容易超出模型的 token 上限，导致请求失败或上下文丢失。

**方案**：实现可配置的 SummarizationMiddleware，支持三种触发策略（token 阈值、消息数量、模型上限百分比），触发后由轻量模型生成摘要，保留最近 N 条消息 + 摘要作为新的上下文。

## 性能优化

### 启动速度优化

| 优化项 | 措施 | 效果 |
|--------|------|------|
| 服务并行启动 | LangGraph、Gateway、Frontend 三个服务同时启动，仅 Nginx 在三端口就绪后启动 | 启动提速 40-60% |
| 配置升级快速跳过 | config-upgrade.sh 添加 bash 级 grep 对比 config_version，版本一致时直接退出不启动 Python | 减少冷启动 1-2s |
| 无用依赖清理 | 移除零引用的 kubernetes 和 duckdb 包（约 130MB），移除 Nuxt 项目中误引入的 nuxt-og-image | 安装体积缩减，加速 CI |

### 前端运行时优化

| 优化项 | 措施 | 效果 |
|--------|------|------|
| Shiki 代码高亮懒加载 | codeToHtml 改为 `await import("shiki")` 动态导入，类型 import 保持静态 | 首屏 JS 体积减少 ~200KB |
| CodeMirror 编辑器懒加载 | 10 个 CodeMirror 包（7 语言 + 2 主题 + react-codemirror）用 `next/dynamic` + `ssr: false` 包裹，内部通过 `Promise.all()` 并行加载 | 首屏 JS 体积减少 ~500KB |
| 乐观 UI 更新 | 消息发送即时显示，线程创建 optimistic 插入 query cache | 消除网络延迟感知 |
| TanStack Query 缓存策略 | `staleTime: 30s` + `refetchOnWindowFocus` + `visibilitychange` 监听 | 减少不必要的 API 请求 |

### Bug 修复带来的稳定性提升

| 问题 | 根因 | 修复 |
|------|------|------|
| max_tokens 400 错误 | GLM-5 通过华为 ModelArts 最大支持 131072，原配置 200000 导致 BadRequest 被前端静默吞掉 | 修正为 131072 |
| 消息发送期间追加导致 UI 卡死 | sendMessage 中 sendInFlightRef 为 true 时直接 return 丢弃第二条消息 | 改为先 `await thread.stop()` 取消当前运行再发送新消息 |
| 线程列表消失（Safari） | useThreads 缺少 refetch 策略，tab 切换后缓存过期 | 添加 refetchOnWindowFocus、staleTime、visibilitychange 监听、onCreated optimistic 插入 |
| Thinking 状态显示异常 | 乐观 thinking 占位消息使用静态 spinner，与实际推理内容切换时闪烁 | 改用 Reasoning 组件（脑图标 + shimmer 动画 + 实时计秒器） |

## 系统架构

```
                     ┌─────────────────────────────────────────────┐
                     │            Nginx (端口 1000)                │
                     │           统一反向代理入口                   │
                     └──────┬────────────────────┬─────────────────┘
                            │                    │
          /api/langgraph/*  │                    │  /api/* (其他)
                            v                    v
          ┌──────────────────────┐  ┌──────────────────────────────┐
          │  LangGraph Server    │  │   Gateway API (端口 8001)    │
          │    (端口 2024)       │  │   FastAPI REST               │
          │                      │  │                              │
          │ ┌──────────────────┐ │  │  /api/models      模型列表   │
          │ │    Lead Agent    │ │  │  /api/mcp/config  MCP 配置   │
          │ │                  │ │  │  /api/skills      技能管理   │
          │ │  16+ 层中间件链  │ │  │  /api/memory      记忆数据   │
          │ │       |          │ │  │  /api/setup/*     配置管理   │
          │ │   工具系统        │ │  │  /api/threads/*   线程管理   │
          │ │       |          │ │  │                              │
          │ │  子代理(x3并行)   │ │  └──────────────────────────────┘
          │ └──────────────────┘ │
          └──────────────────────┘
                            │
          ┌──────────────────────┐
          │   Frontend (端口 3000)│
          │   Next.js 16         │
          │   React 19           │
          │   TailwindCSS 4      │
          │   Shadcn UI          │
          └──────────────────────┘
```

**请求路由**（通过 Nginx）：
- `/api/langgraph/*` -> LangGraph Server：代理交互、线程管理、SSE 流式传输
- `/api/*`（其他）-> Gateway API：模型、MCP、Skills、记忆、文件上传、产物
- `/`（非 API）-> Frontend：Next.js Web 界面

### 中间件链详解

| 序号 | 中间件 | 职责 |
|------|--------|------|
| 1 | ThreadDataMiddleware | 创建线程专属隔离目录（workspace/uploads/outputs） |
| 2 | UploadsMiddleware | 将新上传的文件注入到对话上下文 |
| 3 | SandboxMiddleware | 获取并管理沙箱执行环境生命周期 |
| 4 | DanglingToolCallMiddleware | 清理悬挂的未完成工具调用，确保模型看到完整历史 |
| 5 | GuardrailMiddleware | 工具调用前的授权守卫（可选，按配置启用） |
| 6 | ToolErrorHandlingMiddleware | 工具调用失败时的错误降级处理 |
| 7 | SummarizationMiddleware | 接近 token 上限时自动摘要压缩上下文（可选） |
| 8 | TodoListMiddleware | 计划模式下跟踪多步骤任务进度（可选） |
| 9 | TitleMiddleware | 首轮对话后自动生成会话标题 |
| 10 | MemoryMiddleware | 将对话排入异步记忆抽取队列，支持用户纠正检测 |
| 11 | ViewImageMiddleware | 为视觉模型注入图像数据（按模型能力启用） |
| 12 | DeferredToolFilterMiddleware | 延迟工具加载，减少上下文占用（按配置启用） |
| 13 | SubagentLimitMiddleware | 控制子代理并发数量上限（按配置启用） |
| 14 | LoopDetectionMiddleware | 检测并中断代理的无限循环调用 |
| 15 | SandboxAuditMiddleware | Bash 命令安全审计：三级分类（block/warn/pass）+ 审计日志 |
| 16 | TokenUsageMiddleware | 记录每次 LLM 调用的 input/output/total token 用量 |
| 17 | ClarificationMiddleware | 拦截澄清请求并中断图执行（必须在最后） |
| 18 | VisualQualityMiddleware | 视觉输出质量门控：交付前检测是否已运行 visual_quality_check，未通过则注入提醒 |

### 工具生态

| 类别 | 工具 | 说明 |
|------|------|------|
| 沙箱 | bash, ls, read_file, write_file, str_replace | 线程隔离的文件系统操作 |
| 内置 | present_files, ask_clarification, view_image, task, visual_quality_check, visual_refinement_check | 文件展示、交互澄清、图像理解、子代理委派、视觉质量门控、迭代精修检查 |
| 社区 | Tavily, Jina AI, Firecrawl, DuckDuckGo | 网页搜索、网页抓取、图片搜索 |
| MCP | 任意 MCP 兼容服务器 | 支持 stdio/SSE/HTTP 传输协议 |
| Skills | 领域专属工作流 | 通过 System Prompt 注入的可配置技能包 |

## 快速开始

只需 4 步即可运行 MedrixFlow，**无需手动编辑任何配置文件**。

### 第 1 步：安装前置工具

| 工具 | 版本要求 | 安装方式 |
|------|---------|---------|
| Python | 3.12+ | [python.org](https://www.python.org/) |
| uv | 最新版 | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Node.js | 22+ | [nodejs.org](https://nodejs.org/) |
| pnpm | 10+ | `npm install -g pnpm` |
| nginx | - | macOS: `brew install nginx` / Linux: `sudo apt install nginx` |

### 第 2 步：克隆与安装

```bash
git clone https://github.com/Citrus-bit/medrix-flow.git
cd medrix-flow
make config    # 自动生成 config.yaml 和 .env（仅首次需要）
make install   # 一键安装前后端所有依赖
```

### 第 3 步：启动服务

```bash
make dev       # 启动所有服务（LangGraph + Gateway + Frontend + Nginx）
```

启动完成后浏览器自动打开 http://localhost:1000

> 也可以使用 `make dev-daemon` 在后台启动，或双击 `start.command` 一键启动。

### 第 4 步：在页面配置模型与 API Key

首次打开页面时，设置面板会**自动弹出**引导你完成配置：

1. **添加模型**：在「配置」页面选择提供商（OpenAI / Anthropic / Google Gemini / DeepSeek / OpenAI Compatible），填入模型名称
2. **填入 API Key**：输入对应的 API Key，点击「测试」按钮验证连通性
3. **配置工具密钥**（可选）：如需网页搜索功能，填入 Tavily / Jina 的 API Key
4. **保存配置** - 完成！配置自动持久化，服务自动热重载

> 后续可随时通过左下角「设置和更多」->「设置」->「配置」重新打开配置面板。

### 常用命令

| 命令 | 说明 |
|------|------|
| `make dev` | 开发模式启动（支持热重载） |
| `make start` | 生产模式启动（性能优化） |
| `make dev-daemon` | 后台守护进程启动 |
| `make stop` | 停止所有服务 |
| `make check` | 检查前置工具是否已安装 |
| `make clean` | 停止服务并清理临时文件 |
| `make up` | Docker 生产部署 |
| `make down` | 停止 Docker 容器 |

## 技术栈

### 后端

| 技术 | 版本 | 用途 |
|------|------|------|
| **LangGraph** | 1.0.6+ | 多代理编排引擎，有向图状态机 |
| **LangChain** | 1.2.3+ | LLM 抽象层、工具系统、MCP 适配器 |
| **FastAPI** | 0.115.0+ | Gateway REST API，异步高性能 |
| **Python** | 3.12+ | 后端运行时 |
| **uv** | 最新版 | 包管理器，替代 pip/poetry |
| **agent-sandbox** | - | 沙箱代码执行 |
| **markitdown** | - | 多格式文档转 Markdown |

### 前端

| 技术 | 版本 | 用途 |
|------|------|------|
| **Next.js** | 16 | React 元框架，App Router + Turbopack |
| **React** | 19 | UI 库 |
| **TypeScript** | 5.x | 类型安全 |
| **TailwindCSS** | 4 | 原子化 CSS 框架 |
| **Shadcn UI** | - | 基础组件库 |
| **MagicUI** | - | 现代动效组件 |
| **TanStack Query** | - | 服务端状态管理 |
| **LangGraph SDK** | - | Agent 交互 |

## 项目结构

```
medrix-flow/
├── backend/                        # 后端服务
│   ├── packages/harness/medrix_flow/
│   │   ├── agents/                 # 代理系统
│   │   │   ├── lead_agent/         #   主代理（工厂 + 提示词）
│   │   │   ├── middlewares/        #   18 个中间件组件（含安全审计、Token 追踪、视觉质量门控）
│   │   │   ├── memory/             #   记忆抽取、纠正检测、视觉偏好持久化与可插拔存储
│   │   │   └── thread_state.py     #   线程状态 Schema
│   │   ├── sandbox/                # 沙箱执行引擎 + 安全审计
│   │   ├── subagents/              # 子代理系统（注册 + 执行器 + visual-specialist）
│   │   ├── tools/                  # 工具集（含 visual_quality_check、visual_refinement_check）
│   │   ├── mcp/                    # MCP 协议集成
│   │   ├── models/                 # 模型工厂 + Provider 补丁
│   │   ├── skills/                 # Skill 发现与加载
│   │   ├── community/              # 社区工具（Tavily/Jina/Firecrawl）
│   │   └── config/                 # 配置系统（热重载 + 环境变量解析）
│   ├── app/gateway/                # FastAPI 网关
│   │   ├── app.py                  #   应用入口
│   │   └── routers/                #   路由模块（models/mcp/skills/memory/setup）
│   ├── tests/                      # 测试套件（277 个用例）
│   ├── langgraph.json              # LangGraph 入口配置
│   └── pyproject.toml              # Python 依赖
│
├── frontend/                       # 前端应用
│   ├── src/
│   │   ├── app/                    # Next.js App Router 路由
│   │   ├── components/
│   │   │   ├── ui/                 #   基础 UI 组件
│   │   │   ├── workspace/          #   工作区组件（聊天/设置/侧边栏）
│   │   │   └── ai-elements/        #   AI 组件（推理/代码块/模型选择器）
│   │   ├── core/                   # 核心业务逻辑
│   │   │   ├── threads/            #   线程管理 + 流式传输
│   │   │   ├── setup/              #   配置管理（类型/API/Hooks）
│   │   │   ├── i18n/               #   国际化（中/英）
│   │   │   └── settings/           #   本地设置（localStorage）
│   │   └── hooks/                  # 自定义 React Hooks
│   └── package.json
│
├── skills/                         # 技能系统
│   ├── public/                     #   公共技能包
│   └── custom/                     #   自定义技能
│
├── scripts/                        # 脚本工具
│   ├── serve.sh                    #   服务启动（并行 + 健康检查）
│   ├── start-daemon.sh             #   守护进程启动
│   ├── config-upgrade.sh           #   配置版本升级
│   └── deploy.sh                   #   Docker 部署
│
├── docker/                         # Docker 配置
│   ├── nginx/                      #   Nginx 反向代理配置
│   ├── docker-compose.yaml         #   生产部署编排
│   └── docker-compose-dev.yaml     #   开发环境编排
│
├── config.example.yaml             # 配置模板（含完整字段示例）
├── Makefile                        # 根目录命令入口
└── README.md                       # 本文件
```

## 配置说明

### 前端 UI 配置（推荐）

MedrixFlow 支持通过 Web 界面直接管理所有模型和 API 密钥配置：

- **模型管理**：添加 / 编辑 / 删除 LLM 模型，支持 5 种预设提供商 + OpenAI Compatible 兼容模式
- **连通性测试**：每个模型配置旁的「测试」按钮，动态实例化 Provider 验证可用性
- **工具 API Key**：配置 Tavily（网页搜索）和 Jina（网页抓取）的密钥
- **即时生效**：保存后自动写入 config.yaml 和 .env，服务自动热重载

**打开方式**：左下角「设置和更多」->「设置」->「配置」标签页

### 手动配置（高级用户）

直接编辑项目根目录的 `config.yaml`，主要配置段：

| 配置段 | 说明 |
|--------|------|
| `models` | LLM 模型定义（类路径、API Key、Thinking/Vision 支持） |
| `tools` | 工具定义（模块路径、分组） |
| `sandbox` | 执行环境（本地 / Docker / K3s）+ `allow_host_bash` 安全开关 |
| `skills` | 技能目录路径 |
| `memory` | 记忆系统（启用、存储、防抖、事实上限、存储后端类路径） |
| `summarization` | 上下文摘要（触发策略、保留策略） |
| `subagents` | 子代理（超时配置） |
| `channels` | IM 渠道（飞书/Slack/Telegram） |
| `guardrails` | 工具调用授权守卫 |
| `token_usage` | Token 用量追踪（启用/禁用） |
| `checkpointer` | 状态持久化（memory/sqlite/postgres） |

### 环境变量

配置值以 `$` 开头会自动解析为环境变量。常用变量：

- 模型 API Key：`OPENAI_API_KEY`、`ANTHROPIC_API_KEY`、`DEEPSEEK_API_KEY`、`GOOGLE_API_KEY`
- 工具 API Key：`TAVILY_API_KEY`、`JINA_API_KEY`、`GITHUB_TOKEN`
- 配置覆盖：`MEDRIX_FLOW_CONFIG_PATH`、`MEDRIX_FLOW_EXTENSIONS_CONFIG_PATH`

### MCP 服务器配置（extensions_config.json）

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

## 支持的模型提供商

| 提供商 | Provider 类路径 | 备注 |
|--------|-----------------|------|
| OpenAI | `langchain_openai:ChatOpenAI` | GPT-4o / GPT-5 / o1 等 |
| Anthropic | `langchain_anthropic:ChatAnthropic` | Claude 3.5/4 系列 |
| Google Gemini | `langchain_google_genai:ChatGoogleGenerativeAI` | Gemini 2.5 Pro/Flash |
| DeepSeek | `medrix_flow.models.patched_deepseek:PatchedChatDeepSeek` | DeepSeek V3 / Reasoner |
| OpenAI Compatible | `langchain_openai:ChatOpenAI` + 自定义 base_url | 华为 ModelArts、Novita、MiniMax、OpenRouter 等 |

## 文档

- [配置指南](./backend/docs/CONFIGURATION.md)
- [架构详解](./backend/docs/ARCHITECTURE.md)
- [API 参考](./backend/docs/API.md)
- [文件上传](./backend/docs/FILE_UPLOAD.md)
- [路径示例](./backend/docs/PATH_EXAMPLES.md)
- [上下文摘要](./backend/docs/summarization.md)
- [计划模式](./backend/docs/plan_mode_usage.md)
- [安装指南](./backend/docs/SETUP.md)

## 许可证

MIT License - 查看 [LICENSE](./LICENSE) 文件了解更多详情。

## 鸣谢

- [LangGraph](https://langchain-ai.github.io/langgraph/) - 图状态机代理框架
- [LangChain](https://www.langchain.com/) - LLM 应用开发框架
- [Next.js](https://nextjs.org/) - React 元框架
- [Shadcn UI](https://ui.shadcn.com/) - UI 组件库
- 所有开源库的贡献者
