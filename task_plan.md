# 任务计划：MedrixFlow Upstream Catch-Up Plan

## 目标
在不改写现有 thread-based chat UX 的前提下，为 MedrixFlow 落地单机优先的 runtime/persistence/runs/feedback、最小前端 run awareness、测试与开发运维能力，并补齐 skills 生命周期与 upstream drift guard。

## 当前阶段
阶段 6

## 各阶段

### 阶段 1：需求与发现
- [x] 理解用户意图
- [x] 确定约束条件和需求
- [x] 将发现记录到 findings.md
- **状态：** completed

### 阶段 2：P0 后端 Runtime / Persistence / Gateway
- [x] 实现 RunManager、RunStore、RunEventStore、FeedbackRepo
- [x] 接入 gateway lifespan / deps / services / runs endpoints
- [x] 锁定 checkpoint diff 持久化策略，保证 best-effort
- **状态：** completed

### 阶段 3：P1 前端 Run Awareness / Feedback
- [x] 扩展 stream lifecycle 捕获 run_id
- [x] 增加 feedback client 与消息工具栏接线
- [x] 保持历史消息与现有线程流不变
- **状态：** completed

### 阶段 4：测试、CI、Setup / Doctor
- [x] 补 backend/frontend 测试
- [x] 切 frontend unit tests 到 vitest
- [x] 增加 CI、make setup、make doctor
- **状态：** completed

### 阶段 5：P2 Skills Lifecycle / Upstream Drift Guard
- [x] 将 custom skill 生命周期抽离到 storage/service
- [x] 增加 scan/history/rollback/cache refresh
- [x] 增加非破坏性 upstream drift workflow
- **状态：** completed

### 阶段 6：验证与交付
- [x] 跑关键测试并记录结果
- [x] 汇总变更、风险与后续建议
- **状态：** completed

## 关键问题
1. 现有前端直接连 LangGraph server，run persistence 需要 sideband register，而不是重写流入口。
2. Skills 生命周期需要避开 `prompt -> skills.__init__ -> service -> prompt` 的循环依赖，因此 `skills.__init__` 保持轻量导出，service/storage 走显式模块导入。

## 已做决策
| 决策 | 理由 |
|------|------|
| 保持 `useStream` 主链路不变，采用 `run_id` sideband 注册 | 最小侵入地补齐 runs/feedback，不打断现有 UX |
| 先用 `aiosqlite` 和单文件库 `runtime.sqlite3` | 满足单机优先目标，避免过早引入 SQLAlchemy/Alembic |
| skills 扫描先采用确定性规则，不依赖外部 moderation 模型 | 保证安装/编辑流程离线可用，降低部署和测试耦合 |
| upstream drift 仅报告、不自动 merge/reset | 满足“非破坏性 guard”的要求，避免 automation 改写主分支 |

## 备注
- 本轮实现已经覆盖 P0、P1、P2 和配套验证。
- 后续若继续追上游参考实现，可优先看 runtime/runs、skills storage/service、frontend e2e 三条线。
