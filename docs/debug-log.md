# MedrixFlow 调试与审查日志

> 按时间倒序排列，最新记录在前。

---

## 2026-04-02 — 项目审查：冗余代码识别

**问题描述**: 全面审查项目，识别可清理的冗余文件/代码以减轻项目体积。

**发现**:

1. `docs/CODE_CHANGE_SUMMARY_BY_FILE.md` (939 行) — 一次性 diff 记录文档，记录 citations 系统移除的完整 diff。代码已合并后此文件不再有维护价值。
2. `docs/SKILL_NAME_CONFLICT_FIX.md` (865 行) — 技能名称冲突修复的完整改动文档，作为一次性改动说明已完成使命。
3. `frontend/public/demo/threads/` (13 个演示线程) — 原 DeerFlow 的演示数据，MedrixFlow 上下文中无使用场景。
4. `.context-handoff.md` (372 行) — AI 上下文交接文件，属于开发过程产物，不应随仓库分发。
5. `frontend/src/app/mock/` — Mock 页面目录，仅开发调试用。
6. `README_en.md` — 英文 README 与中文 README.md 内容高度重复。
7. `medrix-flow.code-workspace` — VS Code workspace 文件，个人偏好配置。
8. `.hintrc` — 开发提示配置文件。

**已执行清理** (68 文件, -26,262 行, ~13MB 二进制资产):

已删除文件:
- `docs/CODE_CHANGE_SUMMARY_BY_FILE.md` — 一次性 diff 记录
- `docs/SKILL_NAME_CONFLICT_FIX.md` — 一次性改动文档
- `.context-handoff.md` — AI 上下文交接产物
- `medrix-flow.code-workspace` — VS Code workspace 配置
- `.hintrc` — 开发提示配置
- `frontend/public/demo/threads/` (13 个演示线程, ~13MB) — DeerFlow 演示数据
- `frontend/src/app/mock/` (6 个 mock API 路由) — 静态网站模式 mock
- `frontend/scripts/save-demo.js` — demo 数据保存脚本
- `scripts/tool-error-degradation-detection.sh` — 未被引用的诊断脚本
- `backend/debug.py` — 开发调试入口

已修改文件:
- `frontend/src/app/workspace/page.tsx` — 移除 STATIC_WEBSITE_ONLY 分支（demo 数据已删除）
- `frontend/package.json` — 移除 `demo:save` 脚本

验证: `pnpm typecheck` 通过，后端 lint 无新增错误（2 个预存 ruff UP041 警告）。

**状态**: ✅ 已清理

---

## 2026-03-XX — Citations 系统完整移除

**问题描述**: 移除继承自 DeerFlow 的 citations（引用）系统，简化前后端代码。

**根因分析**: citations 系统在 MedrixFlow 场景中维护成本高但使用价值低。包含前端解析/渲染组件、后端 prompt 注入和 artifact 下载处理等多层耦合代码。

**解决方案**:
- 删除 `frontend/src/core/citations/` 目录 (3 文件，~267 行)
- 删除 `frontend/src/components/ai-elements/inline-citation.tsx` (~289 行)
- 删除 `frontend/src/components/workspace/messages/safe-citation-content.tsx` (~85 行)
- 新增 `markdown-content.tsx` 替代（纯 Markdown 渲染，无引用逻辑）
- 清理后端 prompt 中的 `<citations_format>` 段
- 清理 `artifacts.py` 中的 `remove_citations_block` 逻辑
- 清理 i18n 中的 `citations` 命名空间
- 清理 skills 中的 citations 引用格式要求

**影响**: +62 / -894 行，涉及 18 文件修改 + 1 新增 + 5 删除

**状态**: ✅ 已修复

---

## 2026-02-10 — 技能名称冲突问题

**问题描述**: public skill 和 custom skill 同名时，打开/关闭/配置互相影响。

**根因分析**: 配置文件仅用 `skill_name` 作为键，同名不同类别技能无法区分。

**解决方案**: 使用 `{category}:{name}` 组合键，向后兼容旧格式。详见 `docs/SKILL_NAME_CONFLICT_FIX.md`。

**状态**: ✅ 已修复（UI 区分问题暂时保留）

---

## 2026-02-XX — max_tokens 配置错误

**问题描述**: GLM-5 通过华为 ModelArts 调用报 400 BadRequest，前端静默吞掉错误。

**根因分析**: 原 `max_tokens: 200000` 超出 ModelArts 上限 131072。

**解决方案**: 修正为 `max_tokens: 131072`。

**状态**: ✅ 已修复

---

## 2026-02-XX — 消息发送期间追加导致 UI 卡死

**问题描述**: 快速连续发送两条消息时，第二条被丢弃，UI 卡在 loading 状态。

**根因分析**: `sendMessage()` 中 `sendInFlightRef.current` 为 true 时直接 return。

**解决方案**: 改为先 `await thread.stop()` 取消当前运行，再发送新消息。

**改动文件**: `frontend/src/core/threads/hooks.ts`

**状态**: ✅ 已修复

---

## 2026-02-XX — 线程列表消失 (Safari)

**问题描述**: Safari 中切换 tab 后线程列表消失。

**根因分析**: `useThreads` 缺少 refetch 策略，tab 切换后缓存过期未刷新。

**解决方案**: 
- 添加 `refetchOnWindowFocus`、`staleTime: 30s`
- 添加 `visibilitychange` 监听器
- `onCreated` optimistic 插入
- `titleOfThread` 防空处理

**状态**: ✅ 已修复

---

## 2026-02-XX — Thinking 状态显示异常

**问题描述**: 乐观 thinking 占位消息使用静态 spinner，与实际推理内容切换时闪烁。

**根因分析**: 占位消息与实际 Reasoning 组件样式不一致。

**解决方案**: 改用 `<Reasoning isStreaming>` 组件（脑图标 + shimmer 动画 + 实时计秒器）。

**状态**: ✅ 已修复

---

## 2026-02-XX — 对话首条消息被 header 遮挡

**问题描述**: 聊天页滚动到顶部看不到用户第一条提问。

**根因分析**: header `h-12` (48px) 但消息列表 `pt-10` (40px)，差 8px。

**解决方案**: `pt-10` → `pt-12`。

**改动文件**: `frontend/src/app/workspace/chats/[thread_id]/page.tsx`

**状态**: ✅ 已修复
