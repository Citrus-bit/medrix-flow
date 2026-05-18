import type { Translations } from "./types";

export const zhCN: Translations = {
  // Locale meta
  locale: {
    localName: "中文",
  },

  // Common
  common: {
    home: "首页",
    settings: "设置",
    delete: "删除",
    rename: "重命名",
    share: "分享",
    openInNewWindow: "在新窗口打开",
    close: "关闭",
    more: "更多",
    search: "搜索",
    download: "下载",
    thinking: "思考",
    artifacts: "文件",
    public: "公共",
    custom: "自定义",
    notAvailableInDemoMode: "在演示模式下不可用",
    loading: "加载中...",
    version: "版本",
    lastUpdated: "最后更新",
    code: "代码",
    preview: "预览",
    cancel: "取消",
    save: "保存",
    install: "安装",
    create: "创建",
    export: "导出",
    exportAsMarkdown: "导出为 Markdown",
    exportAsJSON: "导出为 JSON",
    exportSuccess: "对话已导出",
    backendUnavailable: "无法连接后端服务",
    backendUnavailableHint: "请点击重试。如问题持续，请在终端执行：make stop && make dev",
    retryNow: "重试",
    refresh: "刷新",
    latest: "最新",
  },

  // Welcome
  welcome: {
    greeting: "Anaxa Research Workspace",
    description:
      "面向可审计科研流程：整合文献检索、证据映射、实验编排、LaTeX/PDF 成稿与质量审查，帮助你把研究问题推进为可复核的学术产物。",

    createYourOwnSkill: "创建你自己的 Agent Skill",
    createYourOwnSkillDescription:
      "创建你的 Agent Skill 来扩展 Anaxa 的科研工作流。通过自定义技能，Anaxa\n可以帮你检索文献、分析数据，并生成幻灯片、\n网页等可交付成果。",
  },

  // Clipboard
  clipboard: {
    copyToClipboard: "复制到剪贴板",
    copiedToClipboard: "已复制到剪贴板",
    failedToCopyToClipboard: "复制到剪贴板失败",
    linkCopied: "链接已复制到剪贴板",
  },

  // Input Box
  inputBox: {
    placeholder: "今天我能为你做些什么？",
    createSkillPrompt:
      "我们一起用 skill-creator 技能来创建一个技能吧。先问问我希望这个技能能做什么。",
    addAttachments: "添加附件",
    mode: "模式",
    flashMode: "闪速",
    flashModeDescription: "快速且高效的完成任务，但可能不够精准",
    reasoningMode: "思考",
    reasoningModeDescription: "思考后再行动，在时间与准确性之间取得平衡",
    proMode: "Pro",
    proModeDescription: "先补充关键细节再执行，获得更精准的结果，可能需要更多时间",
    ultraMode: "Ultra",
    ultraModeDescription:
      "继承自 Pro 模式，可调用子代理分工协作，适合复杂多步骤任务，能力最强",
    reasoningEffort: "推理深度",
    reasoningEffortMinimal: "最低",
    reasoningEffortMinimalDescription: "检索 + 直接输出",
    reasoningEffortLow: "低",
    reasoningEffortLowDescription: "简单逻辑校验 + 浅层推演",
    reasoningEffortMedium: "中",
    reasoningEffortMediumDescription: "多层逻辑分析 + 基础验证",
    reasoningEffortHigh: "高",
    reasoningEffortHighDescription: "全维度逻辑推演 + 多路径验证 + 反推校验",
    reasoningEffortUnsupported: "当前模型不支持",
    reasoningEffortDisabledInFlash: "闪速模式关闭",
    searchModels: "搜索模型...",
    surpriseMe: "小惊喜",
    surpriseMePrompt: "给我一个小惊喜吧",
    followupLoading: "正在生成可能的后续问题...",
    followupConfirmTitle: "发送建议问题？",
    followupConfirmDescription: "当前输入框已有内容，选择发送方式。",
    followupConfirmAppend: "追加并发送",
    followupConfirmReplace: "替换并发送",
    syntheticExperimentMode: "模拟实验模式",
    syntheticExperimentModeDescription:
      "允许模拟个人实验数据；文献、baseline、公开 benchmark 不得伪造。",
  },

  // Sidebar
  sidebar: {
    newChat: "新对话",
    chats: "对话",
    recentChats: "最近的对话",
    demoChats: "演示对话",
    agents: "智能体",
    research: "科研",
  },

  // Agents
  agents: {
    title: "智能体",
    description: "创建和管理具有专属 Prompt 与能力的自定义智能体。",
    newAgent: "新建智能体",
    emptyTitle: "还没有自定义智能体",
    emptyDescription: "创建你的第一个自定义智能体，设置专属系统提示词。",
    chat: "对话",
    delete: "删除",
    deleteConfirm: "确定要删除该智能体吗？此操作不可撤销。",
    deleteSuccess: "智能体已删除",
    newChat: "新对话",
    createPageTitle: "设计你的智能体",
    createPageSubtitle: "描述你想要的智能体，我来帮你通过对话创建。",
    nameStepTitle: "给新智能体起个名字",
    nameStepHint:
      "只允许字母、数字和连字符，存储时自动转为小写（例如 code-reviewer）",
    nameStepPlaceholder: "例如 code-reviewer",
    nameStepContinue: "继续",
    nameStepInvalidError: "名称无效，只允许字母、数字和连字符",
    nameStepAlreadyExistsError: "已存在同名智能体",
    nameStepCheckError: "无法验证名称可用性，请稍后重试",
    nameStepBootstrapMessage:
      "新智能体的名称是 {name}，现在开始为它生成 **SOUL**。",
    agentCreated: "智能体已创建！",
    startChatting: "开始对话",
    backToGallery: "返回工作区",
    systemAgent: "系统内置",
    customAgent: "自定义",
    readonly: "只读",
    readonlyCreateTitle: "前端智能体配置已改为只读",
    readonlyCreateDescription:
      "当前可用智能体会在“设置和更多 -> 功能”中统一展示。新增或修改智能体请通过后端配置文件或脚本化管理完成。",
  },

  // Breadcrumb
  breadcrumb: {
    workspace: "工作区",
    chats: "对话",
  },

  // Workspace
  workspace: {
    visitGithub: "在 GitHub 上查看 Anaxa",
    settingsAndMore: "设置和更多",
    about: "关于 Anaxa",
    switchToEnglish: "切换到英文",
    switchToChinese: "切换到中文",
    languageEnglish: "English",
    languageChinese: "中文",
  },

  // Conversation
  conversation: {
    noMessages: "还没有消息",
    startConversation: "开始新的对话以查看消息",
    modelProviderOverloaded:
      "模型服务暂时过载、并发受限或不可用，请稍后重试或切换模型。",
  },

  runStatus: {
    running: "运行中",
    reconnecting: "后台任务仍在运行，正在尝试恢复流式连接...",
    error: "任务已出错",
    interrupted: "任务已中断",
    modelRetrying: (attempt: number, seconds: number) =>
      `模型暂时不可用，正在第 ${attempt} 次重试，约 ${seconds} 秒后继续`,
    lastEvent: (time: string) => `最近事件 ${time}`,
  },

  threadDetails: {
    trigger: "详情",
    tooltip: "查看工作流、产出文件、统计和运行日志",
    title: "详情",
    description: "Agent 工作流、工具调用、产出文件与运行日志",
    flow: "流程",
    files: "产出",
    stats: "统计",
    logs: "日志",
    taskRun: "用户目标 / Run",
    noWorkflowTitle: "暂无可视化决策流程",
    noWorkflowDescription:
      "当前运行还没有记录到可还原的 agent 规划、决策或工具步骤；产出文件请在“产出”页查看。",
    noWorkflowEventsTitle: "暂无工作流事件",
    noWorkflowEventsDescription:
      "当前运行已注册，但还没有记录到可展示的 agent 事件。",
    noSummary: "暂无摘要。",
    currentRun: "当前 Run",
    wholeThread: "整个对话",
    stopCurrentTask: "停止当前任务",
    stopRequested: "已请求停止当前任务",
    stopFailed: "停止任务失败",
    exportThreadMarkdown: "导出对话 Markdown",
    exportThreadJSON: "导出对话 JSON",
    exportWorkflowJSON: "导出运行轨迹 JSON",
    activeRunPolling:
      "后台 run 仍在运行，详情面板正在轮询新的事件。",
    streaming: "流式输出中",
    noFilesTitle: "暂无产出文件",
    noFilesDescription:
      "当 agent 生成 PDF、表格、图片或代码文件后，会显示在这里。",
    noLogsTitle: "暂无运行日志",
    noLogsDescription:
      "运行开始后，工具调用、子任务、文件产出和状态事件会逐步记录。",
    unrecorded: "未记录",
    slowSteps: "慢步骤来源",
    noSlowSteps: "暂无慢步骤估算。",
    eventCount: (count: number) => `${count} 个事件`,
    labels: {
      status: "状态",
      caller: "调用方",
      seq: "序号",
      event: "事件",
      step: "步骤",
      run: "Run",
      started: "开始时间",
      lastEvent: "最近事件",
      duration: "估算耗时",
      events: "事件数",
      artifacts: "产出数",
      totalDuration: "总耗时",
      decisionType: "决策类型",
      rationale: "依据",
      nextStep: "下一步",
      outcome: "结果",
      alternatives: "备选项",
      relatedTool: "关联工具",
    },
    nodeKinds: {
      user: "用户",
      agent: "Agent",
      decision: "决策",
      subagent: "子任务",
      tool: "工具",
      artifact: "文件",
      checkpoint: "检查点",
      final: "完成",
      error: "错误",
      event: "事件",
    },
    status: {
      pending: "等待中",
      running: "运行中",
      success: "已完成",
      error: "错误",
      interrupted: "已中断",
      unknown: "未知",
    },
  },

  // Chats
  chats: {
    searchChats: "搜索对话",
  },

  // Page titles (document title)
  pages: {
    appName: "Anaxa",
    chats: "对话",
    newChat: "新对话",
    untitled: "未命名",
  },

  // Tool calls
  toolCalls: {
    moreSteps: (count: number) => `查看其他 ${count} 个步骤`,
    lessSteps: "隐藏步骤",
    executeCommand: "执行命令",
    presentFiles: "展示文件",
    needYourHelp: "需要你的协助",
    useTool: (toolName: string) => `使用 “${toolName}” 工具`,
    searchFor: (query: string) => `搜索 “${query}”`,
    searchForRelatedInfo: "搜索相关信息",
    searchForRelatedImages: "搜索相关图片",
    searchForRelatedImagesFor: (query: string) => `搜索相关图片 “${query}”`,
    searchOnWebFor: (query: string) => `在网络上搜索 “${query}”`,
    viewWebPage: "查看网页",
    listFolder: "列出文件夹",
    readFile: "读取文件",
    writeFile: "写入文件",
    clickToViewContent: "点击查看文件内容",
    writeTodos: "更新 To-do 列表",
    skillInstallTooltip: "安装技能并使其可在 Anaxa 中使用",
  },

  uploads: {
    uploading: "上传中...",
    uploadingFiles: "文件上传中，请稍候...",
  },

  subtasks: {
    subtask: "子任务",
    executing: (count: number) =>
      `${count > 1 ? "并行" : ""}执行 ${count} 个子任务`,
    in_progress: "子任务运行中",
    completed: "子任务已完成",
    failed: "子任务失败",
  },

  // Token Usage
  tokenUsage: {
    title: "Token 用量",
    input: "输入",
    output: "输出",
    total: "总计",
  },
  
  // Shortcuts
  shortcuts: {
    searchActions: "搜索操作...",
    noResults: "未找到结果。",
    actions: "操作",
    keyboardShortcuts: "键盘快捷键",
    keyboardShortcutsDescription: "使用键盘快捷键更快地操作 Anaxa。",
    openCommandPalette: "打开命令面板",
    toggleSidebar: "切换侧边栏",
  },

  // Settings
  settings: {
    title: "设置",
    description: "配置 Anaxa 的模型、能力清单与通知。",
    sections: {
      setup: "配置",
      features: "功能",
      notification: "通知",
    },
    features: {
      title: "功能",
      description: "只读查看当前可用的智能体、MCP 工具和技能配置。",
      readonlyHint: "这里用于审计当前能力边界，不提供前端修改入口。",
      agentsTitle: "智能体",
      toolsTitle: "工具",
      skillsTitle: "技能",
      emptyAgents: "暂无智能体配置。",
      emptyTools: "暂无 MCP 工具配置。",
      emptySkills: "暂无技能配置。",
      noDescription: "暂无描述。",
      readonly: "只读",
      customEditable: "自定义",
      enabled: "启用",
      disabled: "停用",
      transport: "协议",
      endpoint: "端点",
      arguments: "参数",
      envKeys: "环境变量键",
      headerKeys: "HTTP 头键",
      oauthEnabled: "OAuth",
      notConfigured: "未配置",
    },
    notification: {
      title: "通知",
      description:
        "Anaxa 只会在窗口不活跃时发送完成通知，特别适合长时间任务：你可以先去做别的事，完成后会收到提醒。",
      requestPermission: "请求通知权限",
      deniedHint:
        "通知权限已被拒绝。可在浏览器的网站设置中重新开启，以接收完成提醒。",
      testButton: "发送测试通知",
      testTitle: "Anaxa",
      testBody: "这是一条测试通知。",
      notSupported: "当前浏览器不支持通知功能。",
      disableNotification: "关闭通知",
    },
    acknowledge: {
      emptyTitle: "致谢",
      emptyDescription: "相关的致谢信息会展示在这里。",
    },
  },

  setup: {
    title: "配置",
    description: "配置你的 LLM 模型、文生图提供商、工具 API 密钥和学术检索 API 密钥。",
    modelsTitle: "模型配置",
    modelsDescription:
      "添加和管理 LLM 模型提供商。每个模型需要提供商类型、模型名称和 API 密钥。",
    toolKeysTitle: "工具 / 学术 API 密钥",
    toolKeysDescription:
      "配置网络搜索（Tavily）、网页抓取（Jina）以及学术检索增强（OpenAlex、Semantic Scholar）的 API 密钥。",
    imageGenerationTitle: "文生图配置",
    imageGenerationDescription:
      "选择当前生效的文生图提供商，并分别配置 Google AI Studio 或 OpenAI 兼容第三方图像接口。",
    activeImageProvider: "当前生效的文生图提供商",
    googleAiStudio: "Google AI Studio",
    openaiCompatible: "第三方 OpenAI 兼容接口",
    addModel: "添加模型",
    model: "模型",
    provider: "提供商",
    apiKey: "API Key",
    baseUrl: "Base URL",
    testConnection: "测试",
    testToolKey: "测试密钥",
    testImageProvider: "测试文生图模型",
    activeProviderBadge: "当前生效",
    imageGenerationMissingFields: "当前生效的文生图提供商缺少必填项：",
    saveAll: "保存配置",
    saveSuccess: "配置保存成功。",
    noChanges: "没有未保存的更改。",
    loadingSlow: "加载时间较长",
    loadingSlowHint: "后端服务可能还在启动中，你可以稍等片刻或重试。",
    retry: "重试",
    noModelsConfigured: "未配置模型",
    noModelsConfiguredHint: "请在设置中配置至少一个聊天模型以开始对话。",
    openSettings: "打开设置",
  },
};
