# MedrixFlow 项目需求文档

> 最后更新: 2026-04-02

## 1. 项目定位

MedrixFlow 是面向开发者和技术团队的 **全栈 AI 代理编排平台**。用户通过 Web 界面或 IM 渠道与 AI 代理对话，代理可执行代码、浏览网页、管理文件、委派子任务，并跨对话保持记忆。

### 目标用户

- 需要 AI 辅助编码/分析/研究的个人开发者
- 需要私有化部署 AI 助手的技术团队
- 需要多代理协作完成复杂任务的企业用户

## 2. 核心功能

### 2.1 代理对话系统

| 功能 | 状态 | 说明 |
|------|------|------|
| 多线程对话管理 | ✅ 已实现 | 创建/切换/删除对话线程 |
| SSE 流式响应 | ✅ 已实现 | 实时展示 Agent 响应、Thinking 过程 |
| 断连自动恢复 | ✅ 已实现 | 页面刷新/网络断连后自动重连 |
| 乐观 UI 更新 | ✅ 已实现 | 消息发送即刻展示，消除延迟感 |
| 会话标题自动生成 | ✅ 已实现 | 首轮对话后由 LLM 生成 |
| 子代理任务卡片 | ✅ 已实现 | 实时展示并行子任务进度 |
| Thinking/Reasoning 展示 | ✅ 已实现 | 脑图标 + shimmer 动画 + 实时计秒 |

### 2.2 多代理编排

| 功能 | 状态 | 说明 |
|------|------|------|
| Lead Agent + Subagent 架构 | ✅ 已实现 | 主代理拆分任务，最多 3 个子代理并行 |
| 17 层中间件链 | ✅ 已实现 | 覆盖线程隔离、安全审计、记忆等横切关注点 |
| 动态模型热切换 | ✅ 已实现 | 同一对话内切换不同 LLM |
| 循环检测 | ✅ 已实现 | 自动中断代理无限循环 |
| 子代理超时控制 | ✅ 已实现 | 每任务 15 分钟超时 |

### 2.3 沙箱执行

| 功能 | 状态 | 说明 |
|------|------|------|
| 线程级隔离 | ✅ 已实现 | 每个对话线程独立文件系统 |
| 本地沙箱 (LocalSandboxProvider) | ✅ 已实现 | 直接文件系统执行 |
| Docker 沙箱 (AioSandboxProvider) | ✅ 已实现 | 容器隔离执行 |
| Bash 命令安全审计 | ✅ 已实现 | 三级分类（block/warn/pass） |
| 文件读写/目录浏览 | ✅ 已实现 | 完整文件系统操作能力 |
| K3s Pod 级隔离 | 📋 计划中 | 生产级 Kubernetes 隔离 |

### 2.4 持久化记忆

| 功能 | 状态 | 说明 |
|------|------|------|
| 自动知识抽取 | ✅ 已实现 | LLM 分析对话提取用户背景/事实 |
| 用户纠正检测 | ✅ 已实现 | 11 条中英文正则匹配 |
| 防抖批处理 | ✅ 已实现 | 默认 30s debounce |
| System Prompt 注入 | ✅ 已实现 | 高置信度事实自动注入 |
| 可插拔存储后端 | ✅ 已实现 | 默认 JSON，可切换 SQLite/Redis |
| 记忆 UI 查看 | ✅ 已实现 | 设置面板中查看记忆数据 |

### 2.5 工具生态

| 功能 | 状态 | 说明 |
|------|------|------|
| 沙箱工具 (bash/ls/read/write) | ✅ 已实现 | 线程隔离的文件系统操作 |
| 网页搜索 (Tavily) | ✅ 已实现 | 社区工具 |
| 网页抓取 (Jina AI) | ✅ 已实现 | 社区工具 |
| 图片搜索 (DuckDuckGo) | ✅ 已实现 | 社区工具 |
| MCP 协议集成 | ✅ 已实现 | 支持 stdio/SSE/HTTP 传输 |
| MCP CRUD + 连接测试 | ✅ 已实现 | 前端 UI 完整管理 |
| Skills 技能系统 | ✅ 已实现 | 17 个公共技能 + 自定义技能 |
| 技能安装 (.skill 包) | ✅ 已实现 | 上传安装自定义技能 |

### 2.6 配置管理

| 功能 | 状态 | 说明 |
|------|------|------|
| 前端 UI 配置 | ✅ 已实现 | 模型/API Key 全部在 UI 完成 |
| 首次访问自动引导 | ✅ 已实现 | sessionStorage 控制只弹一次 |
| 模型连通性测试 | ✅ 已实现 | 动态实例化 Provider 验证 |
| 配置热重载 | ✅ 已实现 | 保存后自动生效，无需重启 |
| 配置版本升级 | ✅ 已实现 | config-upgrade.sh 自动合并新字段 |

### 2.7 多渠道接入

| 功能 | 状态 | 说明 |
|------|------|------|
| Web 界面 | ✅ 已实现 | Next.js 16 全功能界面 |
| 飞书 (Feishu) | ✅ 已实现 | 流式响应 + 卡片原地更新 |
| Slack | ✅ 已实现 | Socket Mode WebSocket |
| Telegram | ✅ 已实现 | Bot 交互，每用户独立会话 |

### 2.8 安全与可观测性

| 功能 | 状态 | 说明 |
|------|------|------|
| Bash 命令安全审计 | ✅ 已实现 | SandboxAuditMiddleware 三级分类 |
| Token 用量追踪 | ✅ 已实现 | TokenUsageMiddleware 记录每次调用 |
| 沙箱安全门控 | ✅ 已实现 | allow_host_bash 配置开关 |
| Token 用量 UI 显示 | 📋 计划中 | 前端展示 token 消耗 |
| 对话导出 (Markdown/JSON) | 📋 计划中 | 导出对话历史 |
| Cmd+K 命令面板 | 📋 计划中 | 快捷操作 |

### 2.9 部署

| 功能 | 状态 | 说明 |
|------|------|------|
| 本地开发 (make dev) | ✅ 已实现 | 一键启动所有服务 |
| 守护进程模式 | ✅ 已实现 | make dev-daemon |
| Docker Compose 部署 | ✅ 已实现 | make up |
| 一键启动脚本 | ✅ 已实现 | start.command 双击启动 |
| 生产模式 | ✅ 已实现 | make start（性能优化） |

## 3. 非功能性需求

### 3.1 性能

- 前端首屏: Shiki/CodeMirror 懒加载（减少 ~700KB JS）
- 服务启动: 三服务并行启动（提速 40-60%）
- 配置升级: bash 级 grep 快速跳过无变更
- 缓存策略: TanStack Query `staleTime: 30s` + `refetchOnWindowFocus`

### 3.2 安全

- 沙箱隔离: 线程级文件系统隔离
- 命令审计: 高危命令自动阻断
- API Key 保护: 前端密码框显示 + 后端存储在 .env（gitignored）
- 注意: Setup API 返回完整 API Key（无 mask），依赖本地网络安全

### 3.3 可用性

- 支持中英文国际化
- Safari 兼容性修复（线程列表 + SSE 重连）
- IME 输入法兼容（useRef + delayed reset）

### 3.4 可维护性

- 后端: ruff lint + 277 单元测试 + CI
- 前端: ESLint + TypeScript strict + Prettier
- 配置: config.yaml 声明式配置 + 环境变量分离

## 4. 已知限制与约束

1. **LangGraph dev 服务器线程持久化**: 使用内存 + pickle 存储，服务重启会丢失线程。生产环境应用 PostgreSQL。
2. **BETTER_AUTH_SECRET**: 前端构建必需此环境变量，认证功能本身尚未启用。
3. **Demo 数据**: `frontend/public/demo/threads/` 保留了 13 个原 DeerFlow 演示线程数据。
4. **同名技能冲突**: public/custom 同名技能 UI 区分问题已识别但暂时保留。
5. **后端测试超时**: 完整测试套件可能超过 3 分钟。
6. **日志警告**: `Dropped unsupported LangGraph stream mode(s): tools` 不影响功能。

## 5. 支持的模型提供商

| 提供商 | Provider 类路径 |
|--------|-----------------|
| OpenAI | `langchain_openai:ChatOpenAI` |
| Anthropic | `langchain_anthropic:ChatAnthropic` |
| Google Gemini | `langchain_google_genai:ChatGoogleGenerativeAI` |
| DeepSeek | `medrix_flow.models.patched_deepseek:PatchedChatDeepSeek` |
| OpenAI Compatible | `langchain_openai:ChatOpenAI` + 自定义 base_url |

当前生产配置: GLM-5 via 华为 ModelArts (`max_tokens: 131072`)
