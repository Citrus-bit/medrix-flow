/**
 * About MedrixFlow markdown content. Inlined to avoid raw-loader dependency
 * (Turbopack cannot resolve raw-loader for .md imports).
 */
export const aboutMarkdown = `# 🧬 关于 MedrixFlow

MedrixFlow 是一个开源的智能体编排平台，专注于将大型语言模型的能力转化为可执行的工作流。它提供了完整的工具链，让 AI 助手能够真正地"动手做事"——搜索信息、执行代码、管理文件、协调多个子任务。

本项目基于 [DeerFlow](https://github.com/bytedance/deer-flow) 架构进行了品牌定制和二次开发。

---

## 核心能力

- **技能系统**：通过可插拔的 Skill 模块扩展 Agent 能力，覆盖深度研究、数据分析、内容创作等场景
- **沙箱执行**：在隔离环境中安全运行代码，支持文件读写和命令执行
- **子代理协作**：将复杂任务拆解为多个子任务，由不同的 Agent 并行处理
- **长期记忆**：跨会话记住用户偏好和上下文，提供个性化体验
- **多模型支持**：灵活接入各类 LLM 服务，按需切换模型

---

## 开源信息

- **GitHub 仓库**：[github.com/Citrus-bit/medrix-flow](https://github.com/Citrus-bit/medrix-flow)
- **开源协议**：MIT License

---

## 致谢

本项目依赖并受益于以下优秀的开源项目：

- **[LangChain](https://github.com/langchain-ai/langchain)** — LLM 应用开发框架
- **[LangGraph](https://github.com/langchain-ai/langgraph)** — 多智能体编排引擎
- **[Next.js](https://nextjs.org/)** — Web 前端框架
- **[DeerFlow](https://github.com/bytedance/deer-flow)** — 项目架构基础
`;
