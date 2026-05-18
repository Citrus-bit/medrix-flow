import type { Translations } from "./types";

export const enUS: Translations = {
  // Locale meta
  locale: {
    localName: "English",
  },

  // Common
  common: {
    home: "Home",
    settings: "Settings",
    delete: "Delete",
    rename: "Rename",
    share: "Share",
    openInNewWindow: "Open in new window",
    close: "Close",
    more: "More",
    search: "Search",
    download: "Download",
    thinking: "Thinking",
    artifacts: "Artifacts",
    public: "Public",
    custom: "Custom",
    notAvailableInDemoMode: "Not available in demo mode",
    loading: "Loading...",
    version: "Version",
    lastUpdated: "Last updated",
    code: "Code",
    preview: "Preview",
    cancel: "Cancel",
    save: "Save",
    install: "Install",
    create: "Create",
    export: "Export",
    exportAsMarkdown: "Export as Markdown",
    exportAsJSON: "Export as JSON",
    exportSuccess: "Conversation exported",
    backendUnavailable: "Cannot connect to the backend service",
    backendUnavailableHint: "Try clicking Retry. If the problem persists, restart the server with: make stop && make dev",
    retryNow: "Retry",
    refresh: "Refresh",
    latest: "Latest",
  },

  // Welcome
  welcome: {
    greeting: "Anaxa Research Workspace",
    description:
      "A workspace for auditable scholarly workflows: literature discovery, claim-level evidence maps, experiment orchestration, LaTeX/PDF manuscripts, and quality review in one traceable pipeline.",

    createYourOwnSkill: "Create Your Own Skill",
    createYourOwnSkillDescription:
      "Create your own skill to extend Anaxa's research workflow. With customized skills,\nAnaxa can help you retrieve literature, analyze data, and generate\n artifacts like slides and web pages.",
  },

  // Clipboard
  clipboard: {
    copyToClipboard: "Copy to clipboard",
    copiedToClipboard: "Copied to clipboard",
    failedToCopyToClipboard: "Failed to copy to clipboard",
    linkCopied: "Link copied to clipboard",
  },

  // Input Box
  inputBox: {
    placeholder: "How can I assist you today?",
    createSkillPrompt:
      "We're going to build a new skill step by step with `skill-creator`. To start, what do you want this skill to do?",
    addAttachments: "Add attachments",
    mode: "Mode",
    flashMode: "Flash",
    flashModeDescription: "Fast and efficient, but may not be accurate",
    reasoningMode: "Reasoning",
    reasoningModeDescription:
      "Reasoning before action, balance between time and accuracy",
    proMode: "Pro",
    proModeDescription:
      "Clarify key details before execution for more accurate results. May take more time",
    ultraMode: "Ultra",
    ultraModeDescription:
      "Pro mode with subagents to divide work; best for complex multi-step tasks",
    reasoningEffort: "Reasoning Effort",
    reasoningEffortMinimal: "Minimal",
    reasoningEffortMinimalDescription: "Retrieval + Direct Output",
    reasoningEffortLow: "Low",
    reasoningEffortLowDescription: "Simple Logic Check + Shallow Deduction",
    reasoningEffortMedium: "Medium",
    reasoningEffortMediumDescription:
      "Multi-layer Logic Analysis + Basic Verification",
    reasoningEffortHigh: "High",
    reasoningEffortHighDescription:
      "Full-dimensional Logic Deduction + Multi-path Verification + Backward Check",
    reasoningEffortUnsupported: "Unsupported",
    reasoningEffortDisabledInFlash: "Disabled in Flash",
    searchModels: "Search models...",
    surpriseMe: "Surprise",
    surpriseMePrompt: "Surprise me",
    followupLoading: "Generating follow-up questions...",
    followupConfirmTitle: "Send suggestion?",
    followupConfirmDescription:
      "You already have text in the input. Choose how to send it.",
    followupConfirmAppend: "Append & send",
    followupConfirmReplace: "Replace & send",
    syntheticExperimentMode: "Simulation mode",
    syntheticExperimentModeDescription:
      "Allow simulated personal experiment data; literature, baselines, and public benchmarks must remain real.",
  },

  // Sidebar
  sidebar: {
    newChat: "New chat",
    chats: "Chats",
    recentChats: "Recent chats",
    demoChats: "Demo chats",
    agents: "Agents",
    research: "Research",
  },

  // Agents
  agents: {
    title: "Agents",
    description:
      "Create and manage custom agents with specialized prompts and capabilities.",
    newAgent: "New Agent",
    emptyTitle: "No custom agents yet",
    emptyDescription:
      "Create your first custom agent with a specialized system prompt.",
    chat: "Chat",
    delete: "Delete",
    deleteConfirm:
      "Are you sure you want to delete this agent? This action cannot be undone.",
    deleteSuccess: "Agent deleted",
    newChat: "New chat",
    createPageTitle: "Design your Agent",
    createPageSubtitle:
      "Describe the agent you want — I'll help you create it through conversation.",
    nameStepTitle: "Name your new Agent",
    nameStepHint:
      "Letters, digits, and hyphens only — stored lowercase (e.g. code-reviewer)",
    nameStepPlaceholder: "e.g. code-reviewer",
    nameStepContinue: "Continue",
    nameStepInvalidError:
      "Invalid name — use only letters, digits, and hyphens",
    nameStepAlreadyExistsError: "An agent with this name already exists",
    nameStepCheckError: "Could not verify name availability — please try again",
    nameStepBootstrapMessage:
      "The new custom agent name is {name}. Let's bootstrap its **SOUL**.",
    agentCreated: "Agent created!",
    startChatting: "Start chatting",
    backToGallery: "Back to workspace",
    systemAgent: "System",
    customAgent: "Custom",
    readonly: "Read-only",
    readonlyCreateTitle: "Agent configuration is read-only in the frontend",
    readonlyCreateDescription:
      "Configured agents are now shown under Settings and more -> Features. Add or modify agents through backend configuration or scripted administration.",
  },

  // Breadcrumb
  breadcrumb: {
    workspace: "Workspace",
    chats: "Chats",
  },

  // Workspace
  workspace: {
    visitGithub: "Anaxa on GitHub",
    settingsAndMore: "Settings and more",
    about: "About Anaxa",
    switchToEnglish: "Switch to English",
    switchToChinese: "Switch to Chinese",
    languageEnglish: "English",
    languageChinese: "Chinese",
  },

  // Conversation
  conversation: {
    noMessages: "No messages yet",
    startConversation: "Start a conversation to see messages here",
    modelProviderOverloaded:
      "Model provider is temporarily overloaded, concurrency-limited, or unavailable. Retry later or switch models.",
  },

  runStatus: {
    running: "Running",
    reconnecting: "Backend run is still active. Reconnecting stream...",
    error: "Run ended with an error",
    interrupted: "Run interrupted",
    modelRetrying: (attempt: number, seconds: number) =>
      `Model temporarily unavailable. Retry ${attempt} in about ${seconds}s`,
    lastEvent: (time: string) => `Last event ${time}`,
  },

  threadDetails: {
    trigger: "Details",
    tooltip: "View workflow, output files, stats, and run logs",
    title: "Details",
    description: "Agent workflow, tool calls, output files, and run logs",
    flow: "Flow",
    files: "Files",
    stats: "Stats",
    logs: "Logs",
    taskRun: "User Goal / Run",
    noWorkflowTitle: "No visual decision flow yet",
    noWorkflowDescription:
      "This run has no restorable agent planning, decision, or tool-step events yet. Output files are available in the Files tab.",
    noWorkflowEventsTitle: "No workflow events yet",
    noWorkflowEventsDescription:
      "The run is registered, but no visible agent event has been recorded yet.",
    noSummary: "No summary available.",
    currentRun: "Current Run",
    wholeThread: "Whole Thread",
    stopCurrentTask: "Stop current task",
    stopRequested: "Stop request sent",
    stopFailed: "Failed to stop task",
    exportThreadMarkdown: "Export conversation Markdown",
    exportThreadJSON: "Export conversation JSON",
    exportWorkflowJSON: "Export run trace JSON",
    activeRunPolling:
      "Backend run is still active. The details panel is polling for new events.",
    streaming: "Streaming",
    noFilesTitle: "No output files yet",
    noFilesDescription:
      "Generated PDFs, tables, images, or code files will appear here.",
    noLogsTitle: "No run logs yet",
    noLogsDescription:
      "Tool calls, subtasks, file outputs, and status events will be recorded after the run starts.",
    unrecorded: "Not recorded",
    slowSteps: "Slow Step Sources",
    noSlowSteps: "No slow-step estimate yet.",
    eventCount: (count: number) => `${count} event${count === 1 ? "" : "s"}`,
    labels: {
      status: "Status",
      caller: "Caller",
      seq: "Seq",
      event: "Event",
      step: "Step",
      run: "Run",
      started: "Started",
      lastEvent: "Last Event",
      duration: "Estimated Duration",
      events: "Events",
      artifacts: "Artifacts",
      totalDuration: "Total Duration",
      decisionType: "Decision Type",
      rationale: "Rationale",
      nextStep: "Next Step",
      outcome: "Outcome",
      alternatives: "Alternatives",
      relatedTool: "Related Tool",
    },
    nodeKinds: {
      user: "User",
      agent: "Agent",
      decision: "Decision",
      subagent: "Subtask",
      tool: "Tool",
      artifact: "File",
      checkpoint: "Checkpoint",
      final: "Final",
      error: "Error",
      event: "Event",
    },
    status: {
      pending: "Pending",
      running: "Running",
      success: "Complete",
      error: "Error",
      interrupted: "Interrupted",
      unknown: "Unknown",
    },
  },

  // Chats
  chats: {
    searchChats: "Search chats",
  },

  // Page titles (document title)
  pages: {
    appName: "Anaxa",
    chats: "Chats",
    newChat: "New chat",
    untitled: "Untitled",
  },

  // Tool calls
  toolCalls: {
    moreSteps: (count: number) => `${count} more step${count === 1 ? "" : "s"}`,
    lessSteps: "Less steps",
    executeCommand: "Execute command",
    presentFiles: "Present files",
    needYourHelp: "Need your help",
    useTool: (toolName: string) => `Use "${toolName}" tool`,
    searchFor: (query: string) => `Search for "${query}"`,
    searchForRelatedInfo: "Search for related information",
    searchForRelatedImages: "Search for related images",
    searchForRelatedImagesFor: (query: string) =>
      `Search for related images for "${query}"`,
    searchOnWebFor: (query: string) => `Search on the web for "${query}"`,
    viewWebPage: "View web page",
    listFolder: "List folder",
    readFile: "Read file",
    writeFile: "Write file",
    clickToViewContent: "Click to view file content",
    writeTodos: "Update to-do list",
    skillInstallTooltip: "Install skill and make it available to Anaxa",
  },

  // Subtasks
  uploads: {
    uploading: "Uploading...",
    uploadingFiles: "Uploading files, please wait...",
  },

  subtasks: {
    subtask: "Subtask",
    executing: (count: number) =>
      `Executing ${count === 1 ? "" : count + " "}subtask${count === 1 ? "" : "s in parallel"}`,
    in_progress: "Running subtask",
    completed: "Subtask completed",
    failed: "Subtask failed",
  },

  // Token Usage
  tokenUsage: {
    title: "Token Usage",
    input: "Input",
    output: "Output",
    total: "Total",
  },
  
  // Shortcuts
  shortcuts: {
    searchActions: "Search actions...",
    noResults: "No results found.",
    actions: "Actions",
    keyboardShortcuts: "Keyboard Shortcuts",
    keyboardShortcutsDescription: "Navigate Anaxa faster with keyboard shortcuts.",
    openCommandPalette: "Open Command Palette",
    toggleSidebar: "Toggle Sidebar",
  },

  // Settings
  settings: {
    title: "Settings",
    description: "Configure Anaxa models, feature inventory, and notifications.",
    sections: {
      setup: "Setup",
      features: "Features",
      notification: "Notification",
    },
    features: {
      title: "Features",
      description: "Read-only inventory of configured agents, MCP tools, and skills.",
      readonlyHint: "This view audits the current capability surface. Frontend edits are disabled.",
      agentsTitle: "Agents",
      toolsTitle: "Tools",
      skillsTitle: "Skills",
      emptyAgents: "No agents configured.",
      emptyTools: "No MCP tools configured.",
      emptySkills: "No skills configured.",
      noDescription: "No description.",
      readonly: "Read-only",
      customEditable: "Custom",
      enabled: "Enabled",
      disabled: "Disabled",
      transport: "Transport",
      endpoint: "Endpoint",
      arguments: "Arguments",
      envKeys: "Environment keys",
      headerKeys: "HTTP header keys",
      oauthEnabled: "OAuth",
      notConfigured: "Not configured",
    },
    notification: {
      title: "Notification",
      description:
        "Anaxa only sends a completion notification when the window is not active. This is especially useful for long-running tasks so you can switch to other work and get notified when done.",
      requestPermission: "Request notification permission",
      deniedHint:
        "Notification permission was denied. You can enable it in your browser's site settings to receive completion alerts.",
      testButton: "Send test notification",
      testTitle: "Anaxa",
      testBody: "This is a test notification.",
      notSupported: "Your browser does not support notifications.",
      disableNotification: "Disable notification",
    },
    acknowledge: {
      emptyTitle: "Acknowledgements",
      emptyDescription: "Credits and acknowledgements will show here.",
    },
  },

  setup: {
    title: "Setup",
    description: "Configure your LLM models, image generation providers, tool API keys, and academic retrieval API keys.",
    modelsTitle: "Model Configuration",
    modelsDescription:
      "Add and manage your LLM model providers. Each model needs a provider, model name, and API key.",
    toolKeysTitle: "Tool / Academic API Keys",
    toolKeysDescription:
      "Configure API keys for web search (Tavily), web fetch (Jina), and academic retrieval enhancement (OpenAlex, Semantic Scholar).",
    imageGenerationTitle: "Image Generation",
    imageGenerationDescription:
      "Choose the active image generation provider and configure either Google AI Studio or an OpenAI-compatible third-party image API.",
    activeImageProvider: "Active Image Provider",
    googleAiStudio: "Google AI Studio",
    openaiCompatible: "Third-party OpenAI-compatible",
    addModel: "Add Model",
    model: "Model",
    provider: "Provider",
    apiKey: "API Key",
    baseUrl: "Base URL",
    testConnection: "Test",
    testToolKey: "Test key",
    testImageProvider: "Test image model",
    activeProviderBadge: "Active",
    imageGenerationMissingFields: "Missing required fields for the active image provider:",
    saveAll: "Save Configuration",
    saveSuccess: "Configuration saved successfully.",
    noChanges: "No unsaved changes.",
    loadingSlow: "Loading is taking longer than expected",
    loadingSlowHint: "The backend service may still be starting up. You can wait or try again.",
    retry: "Retry",
    noModelsConfigured: "No models configured",
    noModelsConfiguredHint: "Please configure at least one chat model in settings to start chatting.",
    openSettings: "Open Settings",
  },
};
