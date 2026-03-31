# Notepad
<!-- Auto-managed by OMC. Manual edits preserved in MANUAL section. -->

## Priority Context
<!-- ALWAYS loaded. Keep under 500 chars. Critical discoveries only. -->
Phase 1 DONE: thread disappear fix (hooks.ts + utils.ts). Typecheck passed.
NOW: Phase 2 - show thinking/subagent status in frontend during streaming.
Key insight: current optimistic "Thinking..." msg is static text (hooks.ts ~L254). Subagent tasks render via SubtaskCard but only after tool_calls appear in stream. Gap: between send and first stream event, user sees nothing useful.

## Working Memory
<!-- Session notes. Auto-pruned after 7 days. -->
### 2026-03-31 09:23
## MedrixFlow Phase 1 Fixes COMPLETED (thread disappearing + Safari)

### Changes made (2 files):
1. `frontend/src/core/threads/hooks.ts`:
   - useThreads: select added "status", refetchOnWindowFocus: true, staleTime: 30_000
   - onCreated: optimistic thread insertion into sidebar query cache
   - visibilitychange listener: invalidates threads cache when tab becomes visible
2. `frontend/src/core/threads/utils.ts`:
   - titleOfThread: handles null values and empty title strings

### TypeScript typecheck: PASSED (zero errors)

### Root cause found:
- LangGraph dev server uses `langgraph_runtime_inmem` (in-memory + pickle persistence)
- Threads metadata stored in memory, flushed to `.langgraph_api/.langgraph_ops.pckl` every 10s
- Server restart or pickle corruption = permanent thread loss
- This is architectural limitation of dev server, not fixable from frontend

### Phase 2 TODO: Show thinking/reasoning + subagent status in frontend
Key files for Phase 2:
- Thinking UI: message-list-item.tsx (line 174-183), reasoning.tsx, core/messages/utils.ts
- Subagent UI: message-list.tsx (line 100-116), subtask-card.tsx, core/tasks/context.tsx
- Streaming: streaming-indicator.tsx, useStream from @langchain/langgraph-sdk
- Optimistic thinking msg: hooks.ts line 254-261 (current static "Thinking..." text)
- useStream reconnect: uses sessionStorage for lg:stream:{threadId}->runId mapping
- streamResumable:true + onDisconnect:"continue" = backend continues on disconnect


## MANUAL
<!-- User content. Never auto-pruned. -->

