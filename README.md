# MedrixFlow 2.6.2

[English](./README_en.md) | **中文**

<p align="center">
  <img src="https://img.shields.io/badge/Made%20with-LangGraph-blue?style=for-the-badge&logo=python" alt="LangGraph">
  <img src="https://img.shields.io/badge/Frontend-Next.js%2016-black?style=for-the-badge&logo=next.js" alt="Next.js">
  <img src="https://img.shields.io/badge/React-19-61DAFB?style=for-the-badge&logo=react" alt="React 19">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
</p>

<p align="center">
  <b>面向学术写作与实验报告的 AI 研究代理平台</b><br/>
  文献检索 · APA 7 References · 实验证据沉淀 · 多代理协作
</p>

---

MedrixFlow 是一个面向学术写作、文献综述、实验报告和研究交付的全栈 AI 代理编排平台。后端基于 LangGraph 实现多代理协作与状态管理，前端基于 Next.js 16 提供 thread-based chat 与 artifact 工作流。除了通用代理能力外，MedrixFlow 现在内置了结构化学术检索、APA 7 参考文献导出、CS/AI 与生物信息实验专家 Agent、本地证据库与报告产物交付链路，并在普通聊天中按用户意图自动分流科研、文献和实验任务，重点解决“学术感不足、引用不规范、实验结果难沉淀”的问题。

## 技术亮点

### 1. 学术研究闭环：从主题到 APA 7 References

围绕正式学术报告的核心链路，MedrixFlow 提供了一套后台自动分流的研究能力：

- **内置学术子代理**：`academic-researcher` 专门负责主题拆解、扩展检索、候选论文筛选、证据卡沉淀、大纲构建与参考文献导出
- **聊天内科研分流**：普通聊天中出现文献、论文、引用、APA/BibTeX、evidence map、related work 等意图时，优先走 `academic_research` 或复杂任务下的 `academic-researcher`
- **CS/AI 正式文献优先**：`cs_ai` 默认走 `DBLP`、`OpenReview`、`ACL Anthology`、`Semantic Scholar`、`OpenAlex`、`Crossref`、`arXiv` 的组合栈，并优先选择 conference/journal 正式版作为 canonical reference
- **正式报告导出**：单次研究任务可沉淀 `report.md`、`references.md`、`references.bib`、`evidence_map.json`、`retrieval_audit.json`，并按需导出 `graph.json`
- **本地证据存储**：研究项目、论文元数据、证据卡、章节映射与引用格式化结果都落到本地 SQLite，便于后续增量补文献与复用

### 2. 实验专家 Agent：CS/AI 与生信双路径

MedrixFlow 不只停留在“会写报告”，还补上了实验与结果图产出链路：

- **可见 system agent**：`cs-ai-lab` 面向回归、分类、聚类、降维、诊断图与论文级结果摘要；`bioinformatics-lab` 面向 bulk 表达分析、差异分析、富集分析与单细胞起步流程
- **Python-first 实验执行**：统一走本地 Python 实验链路，减少多运行时切换；支持结构化表格数据与生信常见输入
- **autoresearch-style 迭代实验**：模型训练、消融和代码调参类任务可采用 baseline first、固定评估口径、primary metric、trial log 与 `keep` / `discard` / `crash` 记录，不引入外部训练代码
- **科研图自动路由**：按任务意图与数据形状自动选择折线图、直方图、散点图、热力图、ROC/PR、volcano、violin、dot plot 等图型
- **论文级 bundle 导出**：实验默认产出 `experiment_plan.md`、`methods.md`、`results.md`、`metrics.json`、`figure_manifest.json`、`figures/`、`tables/`，必要时附带 `paper_ready_results.md`

### 3. 线程级交付与报告产物发现

学术写作真正可用，关键在于报告、参考文献和图表能否稳定落地并被用户快速找到：

- **线程级 outputs 目录**：学术报告、BibTeX、科研图和实验表默认落到当前线程产物目录，避免“聊完了找不到文件”
- **右侧文件区增强**：文件面板支持自动发现 thread `outputs`、手动刷新按钮、最新文件高亮、直接下载
- **轻聊天，重交付**：复杂研究任务优先交付 artifact bundle，而不是把长报告全部塞进一条聊天消息里

### 4. LangGraph 驱动的多代理编排

区别于简单的 LLM 链式调用，MedrixFlow 采用 **LangGraph 有向图状态机** 作为核心编排引擎：

- **Lead Agent + Subagent 分层架构**：主代理负责任务理解与拆分，最多 3 个子代理并行执行，每个任务独立 15 分钟超时控制
- **多层中间件链**：按严格顺序执行的中间件流水线，覆盖线程隔离、文件上传注入、沙箱生命周期、安全审计、上下文摘要、记忆提取、循环检测、工具错误降级、Token 用量追踪、视觉质量门控等横切关注点
- **动态模型热切换**：同一对话内可在不同 LLM 之间切换；模型能力通过 `supports_thinking`、`supports_reasoning_effort`、`supports_vision` 等标记声明，由前端按能力自动适配

### 5. 线程级沙箱隔离

每个对话线程拥有完全隔离的执行环境：

- **虚拟文件系统映射**：`/mnt/user-data/{workspace,uploads,outputs}` 自动映射到线程专属物理目录，杜绝跨线程数据泄露
- **双沙箱引擎**：支持本地直接执行（LocalSandboxProvider）和 Docker 容器隔离（AioSandboxProvider），生产环境可切换至 K3s Pod 级别隔离
- **工具链完整覆盖**：bash 执行、文件读写、字符串替换、目录浏览，代理拥有完整的文件系统操作能力

### 6. LLM 驱动的持久化记忆

不同于简单的对话历史拼接，MedrixFlow 实现了结构化的长期记忆系统：

- **自动知识抽取**：由 LLM 分析对话内容，自动提取用户背景（职业、偏好）、事实（带置信度评分）和上下文
- **用户纠正检测**：11 条中英文正则模式实时检测用户纠正意图（如「不对」「其实是」「actually」），触发记忆优先更新，避免错误事实被持久化
- **防抖批处理**：通过可配置的 debounce 机制（默认 30s）聚合多轮对话变化，减少 LLM 调用开销
- **可插拔存储后端**：默认 JSON 文件存储（`FileMemoryStorage`），支持通过配置 `storage_class` 切换为任意自定义存储实现（如 SQLite、Redis）
- **System Prompt 注入**：高置信度事实与用户上下文自动注入代理提示词，实现跨对话的个性化响应

### 7. 流式传输与前端配置即用

基于 LangGraph SDK 的 `useStream` 与前端配置面板，MedrixFlow 维持生产级使用体验：

- **SSE 流式渲染**：Agent 响应、Thinking 过程、子代理任务进度全部实时流式展示
- **断连自动恢复**：`reconnectOnMount + streamResumable` 机制确保页面刷新或网络断连后自动重连，后端继续运行不中断
- **前端配置即用**：模型与 API Key 配置全部可在 UI 中完成，保存后自动写入配置并热重载
- **模式即推理深度**：前端默认暴露 `flash / thinking / pro / ultra` 模式，对应不同 reasoning effort 与子代理能力，无需用户手调底层模型参数

### 8. 视觉输出质量系统与安全可观测性

系统内置视觉交付质检、安全审计和 Token 用量追踪能力：

- **视觉质量门控**：`visual_quality_check` 与 `visual_refinement_check` 在图表、PPT、图片交付前执行结构化自检
- **专用视觉子代理**：`visual-specialist` 负责高质量视觉输出与迭代精修
- **Bash 命令安全审计**：`SandboxAuditMiddleware` 对每条 bash 工具调用进行三级分类（block / warn / pass），自动阻断高危命令并记录审计日志
- **Token 用量追踪**：`TokenUsageMiddleware` 记录每次 LLM 调用的 input / output / total token 数量
- **沙箱安全感知**：`security.py` 提供运行时安全等级判断工具函数

## 当前交互说明

### 学术报告与文件交付

- 学术研究和实验任务默认把 `report.md`、`references.md`、`references.bib`、科研图、结果表等产物写入当前线程的 `outputs`
- 右侧文件区会自动发现这些产物，支持**手动刷新**、**最新文件高亮**、文件预览与下载
- 当任务更适合“交付文件”而不是“塞满聊天消息”时，代理会优先返回 artifact bundle，方便你直接继续写作或二次整理

### 科研自动分流

- 侧边栏不再单独展示“科研”入口，主工作流回到普通聊天；`/workspace/research` 仍保留为内部或直连 Research Dashboard
- 文献综述、论文引用、APA/BibTeX、related work、证据映射等任务优先走 `academic_research`，复杂交付可委派给 `academic-researcher`
- 只有当用户明确需要科研项目生命周期、阶段推进、创新性检查、实验 gate、审稿循环或 final bundle 时，才使用 `research_assistant`
- 真实数据实验、模型评估、生信分析和科研图产出继续走 `experiment_lab`

### 澄清与确认

- 当代理需要用户补充信息或确认风险操作时，会调用 `ask_clarification`
- Web UI 会把这类请求渲染成按钮式选项，而不是只显示一段文本
- 选项卡片底部固定包含 `type something`，用户可以切回自由输入

### LaTeX / PDF 预览

- `present_files` 在展示 `.tex` 文件时，会尝试自动生成预览 PDF
- `manuscript_export` 是论文成稿的高层出口：一次调用写入 `.tex`、`references.bib`、`citation_audit.json`，审计通过后生成 `.pdf`
- 当前实现优先调用本机 `tectonic`，不依赖 `pdflatex`、`xelatex` 或 `latexmk`
- 论文/综述/实验论文类交付默认应输出 `manuscript.tex`、`references.bib`、`citation_audit.json` 和 `manuscript.pdf`
- 若 `.tex` 同目录存在 `references.bib`，`present_files` 会先执行 citation audit；缺失 citation key 或未经允许的 `\nocite{*}` 会阻断 PDF 生成并展示审计文件
- 预览链路会自动补常见 LaTeX 兼容处理，例如下载远程图片、补充 `subfig`、清理部分 Unicode 上下标

### 生产环境安全要求

- 生产部署必须显式设置 `MEDRIX_FLOW_ENV=production`，这样 Python 侧才会启用生产安全守卫并拒绝 `LocalSandboxProvider`
- 通过 nginx 暴露 UI/API 时，必须设置 `MEDRIX_FLOW_UI_PASSWORD`，否则 `/workspace`、`/api/*`、`/api/langgraph/*`、`/docs` 会进入 fail-closed 保护
- 如需脚本化调用受保护接口，可额外设置 `MEDRIX_GATEWAY_ADMIN_TOKEN`，并通过请求头 `x-medrix-admin-token` 访问

### Skills 与扩展

- Skills 从项目根目录的 `skills/public` 与 `skills/custom` 自动发现
- 技能启用状态与 MCP 配置统一保存在 `extensions_config.json`
- 用户可以通过设置页启用/停用 skill，也可以把自定义 skill 直接放进 `skills/custom`
- 当前公共 skill 覆盖学术深研、实验分析、数据分析、Nature 风格图表、PPT/图片/视频/播客生成、网页设计、技能/插件创建与 GitHub 深研等工作流

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
          │ │    Lead Agent    │ │  │  /api/agents      Agent 列表 │
          │ │                  │ │  │  /api/academic/*  学术研究   │
          │ │   多层中间件链   │ │  │  /api/experiments/* 实验项目 │
          │ │       |          │ │  │  /api/threads/*   线程/产物  │
          │ │   工具系统        │ │  │  /api/skills      技能管理   │
          │ │       |          │ │  │  /api/setup/*     配置管理   │
          │ │  子代理(x3并行)   │ │  │  /api/mcp/config  MCP 配置   │
          │ └──────────────────┘ │  └──────────────────────────────┘
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
- `/api/*`（其他）-> Gateway API：模型、MCP、Skills、学术研究、实验项目、运行/反馈、文件上传、产物
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
| 17 | ClarificationMiddleware | 拦截澄清请求并中断图执行，前端渲染为按钮式确认卡片（必须在最后） |
| 18 | VisualQualityMiddleware | 视觉输出质量门控：交付前检测是否已运行 visual_quality_check，未通过则注入提醒 |

### 工具生态

| 类别 | 工具 | 说明 |
|------|------|------|
| 学术研究 | `academic_research` | 结构化文献检索、元数据规范化、论文去重、证据卡沉淀、APA 参考文献导出 |
| 科研任务编排 | `research_assistant` | 后台 staged research quest、创新性检查、证据 gate、实验计划、审稿循环与 final bundle 管理 |
| 实验执行 | `experiment_lab` | Python-first 实验流水线、科研图自动路由、结果 bundle 导出 |
| 沙箱 | bash, ls, read_file, write_file, str_replace | 线程隔离的文件系统操作 |
| 内置 | present_files, ask_clarification, citation_audit, manuscript_export, view_image, task, visual_quality_check, visual_refinement_check | 文件展示、交互澄清、引用审计、一键论文 PDF 导出、图像理解、子代理委派、视觉质量门控、迭代精修检查 |
| 社区 | Tavily, Jina AI, Firecrawl, DuckDuckGo | 网页搜索、网页抓取、图片搜索 |
| MCP | 任意 MCP 兼容服务器 | 支持 stdio/SSE/HTTP 传输协议 |
| Skills | 领域专属工作流 | 从 `skills/public` 和 `skills/custom` 发现，并按启用状态注入的技能包 |

### 学术 / 实验 API

| 路径 | 说明 |
|------|------|
| `POST /api/academic/projects` | 创建或复用学术研究项目，绑定 `thread_id` 与研究主题 |
| `POST /api/academic/projects/{project_id}/ingest` | 多源抓取论文、归一化元数据、去重并沉淀证据池 |
| `POST /api/academic/projects/{project_id}/synthesize` | 生成正式报告、APA 参考文献、BibTeX 与证据映射文件 |
| `GET /api/academic/projects/{project_id}/references?style=apa7` | 读取 APA 7 参考文献结果 |
| `POST /api/research/quests` | 后台或直连 Research Dashboard 创建 staged research quest |
| `POST /api/research/quests/{quest_id}/advance` | 推进 intake、literature、novelty、evidence、experiment、manuscript、review、final bundle 等阶段 |
| `POST /api/research/quests/{quest_id}/gate` | 记录实验执行、预审、最终发布等人工 gate 决策 |
| `POST /api/experiments/projects` | 创建实验项目，绑定专家 Agent、数据集和可选学术项目 |
| `POST /api/experiments/projects/{project_id}/execute` | 执行实验主流程并生成指标、图表和结果摘要 |
| `POST /api/experiments/projects/{project_id}/export` | 导出实验 bundle，必要时生成 `paper_ready_results.md` |

## 学术写作新增能力

- **文献综述 / related work**：给定研究主题后，可走 `academic-researcher` + `academic-deep-research` 工作流，自动完成检索式扩展、多源抓取、去重、核心论文池构建与证据映射
- **APA 7 References**：正式报告链路会导出当前项目中全部已核验 canonical references，不设导出上限，并自动生成 `references.md`、`references.bib` 与 `retrieval_audit.json`
- **实验支撑写作**：`cs-ai-lab` 与 `bioinformatics-lab` 可直接把表格实验或生信分析结果转成 figures / tables / methods / results bundle，减少“论文只有文字没有实验”的断层
- **可控迭代实验**：受 autoresearch-style 思路启发，模型训练和消融类实验默认强调 baseline、固定指标、固定评估预算和 `keep` / `discard` / `crash` 记录，而不是无约束地修改代码
- **本地证据沉淀**：学术项目与实验项目都可在本地持续复用，便于同一 thread 反复补文献、补实验、补 references，而不是每次都从零开始
- **文件交付友好**：右侧 artifact 面板更适合查找新报告、新图表和新参考文献文件，避免生成完毕后仍要反复让代理“再发一遍”

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
| tectonic | 推荐 | 用于 `.tex` 文件的本地 PDF 预览与导出 |

### 第 2 步：克隆与安装

```bash
git clone https://github.com/Citrus-bit/medrix-flow.git
cd medrix-flow
make config    # 自动生成 config.yaml 和 .env（仅首次需要）
make install   # 一键安装前后端所有依赖（后端含 dev 依赖组）
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
3. **配置文生图 / 工具 / 学术密钥**（可选）：如需科研文生图、网页搜索或学术检索增强，先选择当前生效的文生图提供商（Google AI Studio 或 OpenAI 兼容第三方接口），再填入对应的图像 API Key，以及 Tavily / Jina / OpenAlex / Semantic Scholar 等密钥
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
| `make verify` | 本地执行与 CI 对齐的校验（backend lint/test + frontend lint/typecheck） |
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
│   │   │   ├── middlewares/        #   中间件组件（含安全审计、Token 追踪、视觉质量门控）
│   │   │   ├── memory/             #   记忆抽取、纠正检测、视觉偏好持久化与可插拔存储
│   │   │   └── thread_state.py     #   线程状态 Schema
│   │   ├── academic/               # 学术研究闭环（多源检索、去重、APA 导出、证据库/图谱投影）
│   │   ├── experiments/            # 实验执行流水线（CS/AI + 生信、自动选图、bundle 导出）
│   │   ├── runtime/                # Runs、消息持久化、反馈与流桥接
│   │   ├── sandbox/                # 沙箱执行引擎 + 安全审计
│   │   ├── subagents/              # 子代理系统（含 academic-researcher、实验专家、visual-specialist）
│   │   ├── tools/                  # 工具集（含 academic_research、research_assistant、experiment_lab、视觉质检）
│   │   ├── mcp/                    # MCP 协议集成
│   │   ├── models/                 # 模型工厂 + Provider 补丁
│   │   ├── skills/                 # Skill 发现与加载
│   │   ├── community/              # 社区工具（Tavily/Jina/Firecrawl）
│   │   └── config/                 # 配置系统（热重载 + 环境变量解析 + system agents）
│   ├── app/gateway/                # FastAPI 网关
│   │   ├── app.py                  #   应用入口
│   │   └── routers/                #   路由模块（threads/artifacts/agents/academic/experiments/runs/...）
│   ├── tests/                      # 测试套件
│   ├── langgraph.json              # LangGraph 入口配置
│   └── pyproject.toml              # Python 依赖
│
├── frontend/                       # 前端应用
│   ├── src/
│   │   ├── app/                    # Next.js App Router 路由（含保留的 /workspace/research 直连页）
│   │   ├── components/
│   │   │   ├── ui/                 #   基础 UI 组件
│   │   │   ├── workspace/          #   工作区组件（聊天/智能体/设置/侧边栏；侧边栏主入口为对话和智能体）
│   │   │   └── ai-elements/        #   AI 组件（推理/代码块/模型选择器）
│   │   ├── core/                   # 核心业务逻辑
│   │   │   ├── threads/            #   线程管理 + 流式传输
│   │   │   ├── artifacts/          #   线程产物清单、刷新、高亮与内容加载
│   │   │   ├── setup/              #   配置管理（类型/API/Hooks）
│   │   │   ├── i18n/               #   国际化（中/英）
│   │   │   └── settings/           #   本地设置（localStorage）
│   │   └── hooks/                  # 自定义 React Hooks
│   └── package.json
│
├── skills/                         # 技能系统
│   ├── public/                     #   公共技能包（academic/experiment/data/figure/PPT/image/video/podcast/skill helpers）
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

- **模型管理**：添加 / 编辑 / 删除 LLM 模型，支持预设提供商与 OpenAI Compatible 兼容模式
- **连通性测试**：每个模型配置旁的「测试」按钮，动态实例化 Provider 验证可用性
- **工具 API Key**：配置 Tavily（网页搜索）和 Jina（网页抓取）的密钥
- **即时生效**：保存后自动写入 config.yaml 和 .env，服务自动热重载
- **能力默认开启**：模型配置中的 Thinking / Vision 能力默认开启，前端不再提供单独切换开关

**打开方式**：左下角「设置和更多」->「设置」->「配置」标签页

### 手动配置（高级用户）

直接编辑项目根目录的 `config.yaml`，主要配置段：

| 配置段 | 说明 |
|--------|------|
| `models` | LLM 模型定义（类路径、API Key、能力标记，如 `supports_thinking` / `supports_reasoning_effort` / `supports_vision`） |
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
- 工具 / 文生图 / 学术 API Key：`TAVILY_API_KEY`、`JINA_API_KEY`、`GEMINI_API_KEY`、`GOOGLE_API_KEY`、`IMAGE_GEN_ACTIVE_PROVIDER`、`IMAGE_GEN_GOOGLE_MODEL`、`IMAGE_GEN_OPENAI_MODEL`、`IMAGE_GEN_OPENAI_BASE_URL`、`IMAGE_GEN_OPENAI_API_KEY`、`GITHUB_TOKEN`、`OPENALEX_API_KEY`、`SEMANTIC_SCHOLAR_API_KEY`
- 配置覆盖：`MEDRIX_FLOW_CONFIG_PATH`、`MEDRIX_FLOW_EXTENSIONS_CONFIG_PATH`

### MCP 与 Skills 配置（`extensions_config.json`）

可从项目根目录的 `extensions_config.example.json` 复制一份作为起点，也可以在设置页中直接维护。

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

## Star History

<a href="https://star-history.com/#Citrus-bit/medrix-flow&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=Citrus-bit/medrix-flow&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=Citrus-bit/medrix-flow&type=Date" />
    <img alt="Star History Chart" src="https://api.star-history.com/svg?repos=Citrus-bit/medrix-flow&type=Date" />
  </picture>
</a>
