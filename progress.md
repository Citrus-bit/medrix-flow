# 进度日志

## 会话：2026-05-07

### 阶段 1：需求与发现
- **状态：** completed
- 执行的操作：
  - 审查 gateway、thread stream、message list、skills 相关入口
  - 对比上游参考实现的 runtime/gateway/frontend/CI 设计
  - 确认 run persistence 采用 sideband register，而不是重写 stream 入口

### 阶段 2：P0 后端 Runtime / Persistence / Gateway
- **状态：** completed
- 执行的操作：
  - 新增 runtime DB、RunManager、RunStore、RunEventStore、FeedbackRepo
  - 新增 gateway `deps.py`、`services.py`、`runs.py`
  - 在 FastAPI lifespan 中初始化 runtime 依赖
  - 以 checkpoint diff 方式持久化 run 期间新增消息

### 阶段 3：P1 前端 Run Awareness / Feedback
- **状态：** completed
- 执行的操作：
  - `useThreadStream` 捕获 `run_id`
  - 增加 run sideband client 和 feedback client
  - 仅为当前活跃会话最后一条 assistant 消息接 feedback controls
  - 保持现有 thread history / stream UX 不变

### 阶段 4：测试、CI、Setup / Doctor
- **状态：** completed
- 执行的操作：
  - 前端单测迁移到 Vitest
  - 新增 run/feedback/hooks/visibility 单测
  - 新增 Playwright smoke 配置与聊天/feedback/sidebar 用例
  - 新增 `frontend-unit-tests.yml`、`e2e-tests.yml`
  - 落地共享 setup service、`make setup`、`make doctor`

### 阶段 5：P2 Skills Lifecycle / Upstream Drift Guard
- **状态：** completed
- 执行的操作：
  - 新增 `skills/storage`、`skills/service`、`skills/security_scanner`、`skills/installer`
  - router 改走 service，支持 install / custom read / update / delete / history / rollback
  - 增加 custom skill lifecycle 测试
  - 新增 `upstream-drift-report.yml`

### 阶段 6：验证与交付
- **状态：** completed
- 执行的操作：
  - 跑 backend ruff/pytest/compileall
  - 跑 frontend lint/typecheck/vitest/playwright
  - 回填 planning files

## 测试结果
| 测试 | 结果 | 状态 |
|------|------|------|
| backend ruff | 通过 | passed |
| backend targeted pytest | 18 passed | passed |
| backend compileall | 通过 | passed |
| frontend lint | 通过 | passed |
| frontend typecheck | 通过 | passed |
| frontend unit tests | 19 passed | passed |
| frontend e2e smoke | 1 passed | passed |

## 关键修复记录
| 问题 | 处理 |
|------|------|
| `prompt -> skills.__init__ -> service -> prompt` 循环依赖 | 收窄 `skills.__init__` 导出，service/storage 使用显式模块导入 |
| Playwright 首轮 smoke 未触发真实提交 | 对齐 thread create 返回值、改为 `Enter` 提交、等待 stream 请求命中 |
| Next 16 dev origin 警告 | Playwright base URL 改为 `http://localhost:3000` |
