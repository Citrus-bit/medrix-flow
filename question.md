# MedrixFlow 代码审查与改进清单（给 GPT 改代码用）

> 扫描范围：`/Users/tampouseng/Desktop/Anaxa`
> 扫描时间：2026-05-12
> 扫描维度：Skill 系统、Agent / Middleware / Subagent、前后端链路（nginx + gateway + frontend）
> 产物目的：作为 GPT 的修改任务单，每条都给出文件路径 + 行号 + 现状 + 期望；GPT 不需要重新探索

## 0. 阅读说明

- 每个条目编号 `X.Y`，其中 `X` 为优先级段（1=High, 2=Medium, 3=Low），`Y` 为序号。
- 每条包含四部分：**位置**（文件:行号）、**现状**（当前逻辑）、**问题**（为什么不好）、**期望**（怎么改 / 验收）。
- 对涉及多文件的改动，会额外标注 **关联文件**。
- 所有"行号"基于本次扫描快照，GPT 动手前请以 Read 读到的最新行号为准（行号仅作锚点）。
- 改代码后**必须**跑末尾第 4 节里的验收命令；不跑视为未完成。
- 第 5 节列出"不要顺手改"的地方，避免过度重构。

---

## 1. 高优先级（建议立即处理）

### 1.1  `PUT /api/skills/{name}` 启用开关缺 admin 守护

- **位置**：`backend/app/gateway/routers/skills.py:241-258`（`update_skill` 路由）
- **现状**：`install / custom write / delete / rollback` 都带 `Depends(require_admin_access)`，但 **enable/disable 开关** 的 `PUT /api/skills/{name}` 没有。
- **问题**：任何能访问 Gateway 的账号都可以修改 agent 能力面（开/关视觉、研究、沙箱相关 skill），等价于能力提权；与同 router 其他写路径的权限模型严重不一致。
- **期望**：
  1. 给 `update_skill` 加 `admin: Annotated[..., Depends(require_admin_access)]`。
  2. 确认前端 `frontend/src/core/skills/api.ts:enableSkill` 调用路径不会被普通用户触发，若前端 UI 需要给非 admin 展示只读态，补一个 403 的 UX fallback。
  3. 新增或补充 `backend/tests/test_skills_api.py` 中的一个权限测试：非 admin 调用 `PUT /api/skills/{name}` 预期 403。

### 1.2  子代理线程池大小与并发上限不一致

- **位置**：
  - `backend/packages/harness/medrix_flow/subagents/executor.py:71-75`（两个 `ThreadPoolExecutor(max_workers=3)`）
  - `backend/packages/harness/medrix_flow/subagents/executor.py:456`（`MAX_CONCURRENT_SUBAGENTS = 3`）
  - `backend/packages/harness/medrix_flow/agents/middlewares/subagent_limit_middleware.py:15-21`（clamp 到 `[2, 4]`，默认 `MAX_SUBAGENT_LIMIT = 4`）
- **现状**：middleware 允许单轮最多 4 个并发 `task()`，但底层 `_scheduler_pool` / `_execution_pool` 都只有 3 个 worker；而 `MAX_CONCURRENT_SUBAGENTS = 3` 的常量也只是文档性描述。
- **问题**：
  - 第 4 个 subagent 会在 `_execution_pool` 上排队；此时 `task_tool` 的 `max_poll_count = (timeout + 60) // 5` 是以提交时刻起算，PENDING 期就已经吃掉预算。
  - 口径分裂（3 vs 4）使后续运维和性能调优判断错误。
- **期望**：
  1. 把 `MAX_SUBAGENT_LIMIT` / `MAX_CONCURRENT_SUBAGENTS` / 两个 `max_workers` **统一成一个常量**（建议 `SUBAGENT_POOL_SIZE`），并从 `config.yaml` 的 `subagents.pool_size` 可选覆盖。
  2. clamp 范围同步到 `[1, SUBAGENT_POOL_SIZE]`。
  3. `task_tool` 的 poll 计时改为以"开始执行时间（`started_at`）"而非"提交时间"起算；PENDING 期不计入超时。
  4. 单元测试：提交 `SUBAGENT_POOL_SIZE + 1` 个任务，确认第 N+1 个排队、不超时被错杀。

### 1.3  `execution_future.cancel()` 对已启动线程无效，产生孤儿线程

- **位置**：`backend/packages/harness/medrix_flow/subagents/executor.py:437-444`（`FuturesTimeoutError` 分支）、`:340-347`（`_aexecute` 回写 `result_holder`）
- **现状**：超时后只调用 `execution_future.cancel()` 并把状态写成 `TIMED_OUT`。但 Python `ThreadPoolExecutor.cancel()` 对 **已经开始** 的 future 恒返回 False；底层 `asyncio.run(self._aexecute(...))` 会继续跑，且结束后还会把 `result` 字段覆盖为 `COMPLETED/FAILED`。
- **问题**：
  - 孤儿线程无法被真正中断，长时间占着 `_execution_pool` 的 slot，进一步放大 1.2 的问题。
  - `_background_tasks[task_id]` 的状态可能在 TIMED_OUT 之后被竞争回写，观测数据失真。
- **期望**：
  1. 在 `_aexecute` 内部传入一个 `asyncio.Event`（或 `threading.Event`）`cancel_token`，外层超时时 `set()`，`_aexecute` 的 astream 循环在每次迭代前检查并 `break`。
  2. 回写 `result_holder` 前检查 `status == TIMED_OUT`，若是则不覆盖。
  3. 若 agent 框架支持，优先使用 `asyncio.wait_for` 在事件循环内部超时，而不是 `future.result(timeout=...)`。
  4. 测试：构造一个会 sleep 远大于 timeout 的 subagent，验证最终 `_background_tasks` 里状态是 `TIMED_OUT`，且不会被 COMPLETED 覆盖。

### 1.4  `SandboxMiddleware.after_agent` 每轮 release 与注释 / Aio 语义矛盾

- **位置**：`backend/packages/harness/medrix_flow/sandbox/middleware.py:65-81`
- **现状**：注释声明"Sandbox is NOT released after each agent call to avoid wasteful recreation"，但 `after_agent` 里实际调用了 `provider.release(sandbox_id)`。
- **问题**：
  - 对 `LocalSandboxProvider` 是 no-op，表面看不出问题；但切到 `AioSandboxProvider` / Docker 容器 provider 时，每轮 agent 调用都会销毁并重建容器，性能退化严重。
  - 代码意图与实现背离，后来者难以判断哪个是"正确语义"。
- **期望**：
  1. 明确语义：**agent 执行期间 sandbox 持久化，仅在 thread 结束时释放**。
  2. 删除 `after_agent` 中的 `release` 调用；改到 thread-level 钩子（例如 `ThreadDataMiddleware` 的关闭回调或 LangGraph 的 checkpoint finalize）。
  3. 如果当前没有 thread-level hook，可加一个 `finalize_thread(thread_id)` API，由 gateway 在 thread 关闭/归档时调用。
  4. 加一条 integration 测试：连续两轮 agent 调用，`provider.acquire` 只在首轮触发一次。

### 1.5  `auth-guard` 仅用 `X-Original-URI` 判定 nginx 子请求，缺来源校验

- **位置**：`frontend/src/app/api/internal/auth-guard/route.ts`
- **现状**：只要请求带 `X-Original-URI` header 就被视作 nginx 的 `auth_request` 子请求，随即签发代理 token（`X-Medrix-Proxy-Authorized`）。
- **问题**：如果 `:6201` 被直接暴露到公网（或同机其他用户），攻击者可直接构造带该 header 的请求获得 proxy token，从而绕过 Gateway 的 `X-Medrix-Proxy-Authorized` 校验访问所有 `/api/*`。
- **期望**：
  1. 新增双重校验：
     - 要求请求 remote addr 是 `127.0.0.1` / `::1`（或可配置白名单），可通过 `x-forwarded-for` / `request.headers.get('host')` 与 `NEXT_PUBLIC_ALLOWED_AUTH_GUARD_HOSTS` 联合判断。
     - 或 nginx 在 `auth_request` 子请求里主动注入一个与 `BETTER_AUTH_SECRET` 派生的 HMAC header，route handler 校验该 HMAC 再签发代理 token。推荐后者（更稳，不依赖网络拓扑）。
  2. 在 `docker/nginx/nginx.local.conf` 和 `nginx.conf` 的 `location = /_auth_check` 里注入该 HMAC header（`proxy_set_header X-Medrix-Guard-HMAC <hmac>;`）。
  3. 加一条测试：直接 `curl :6201/api/internal/auth-guard -H 'X-Original-URI: /api/whatever'` 预期 403。

### 1.6  Upload 返回 `size` 类型与前端不一致

- **位置**：
  - 后端：`backend/app/gateway/routers/uploads.py`（搜 `str(len(content))`）
  - 前端：`frontend/src/core/uploads/types.ts` 的 `UploadedFileInfo.size: number`
- **现状**：后端返回 `size: str`，前端类型声明为 `number`。
- **问题**：TypeScript 类型对齐失败；任何对 `size` 的数值比较（例如 `> MAX_UPLOAD_BYTES`）会做字符串字典序比较，"9" > "10" 这种错比。
- **期望**：
  1. 后端改成 `size: int`（`len(content)`），并在响应 model / Pydantic schema 中声明类型。
  2. 搜索前端所有 `UploadedFileInfo.size` 的使用点（`frontend/src/core/uploads/`、`frontend/src/components/workspace/`），确认改成 number 后没有字符串拼接依赖；必要时加 `toString()` 显式转换。
  3. 加一条 backend 单元测试断言响应里 `size` 是 `int`。

---

## 2. 中优先级（下一批处理）

### 2.1  Skill 读 / 写校验不对称（loader 接受任意字段）

- **位置**：
  - 读路径：`backend/packages/harness/medrix_flow/skills/parser.py:9`（`parse_skill_file` 只要 `name + description` 非空）
  - 写路径：`backend/packages/harness/medrix_flow/skills/validation.py:12-95`（`_validate_skill_frontmatter` 严格：allowed keys / hyphen-case / 长度）
- **现状**：经 install/edit 进来的 skill 会被严格校验；但用户手工 `cp` 到 `skills/custom/<name>/SKILL.md` 的文件只走 loader，任何非法字段 / 超长描述 / 特殊符号都能进入 prompt。
- **期望**：
  1. 在 `load_skills` 内每个 skill 解析后调用同一份 `_validate_skill_frontmatter(strict=False)`，违规时记录 warning 并**跳过**该 skill（不进入 `available_skills` 列表）。
  2. 错误信息写入 gateway `logger.warning`，同时通过 `/api/skills` 返回里附一个 `invalid_skills: [{path, reason}]` 字段供前端 debug（可选）。
  3. 测试：放一个非法 SKILL.md 到 `skills/custom/bad_skill/SKILL.md`，断言 `load_skills()` 不会抛、不会把它加入结果。

### 2.2  public / custom 同名冲突静默 + enabled 开关不区分 category

- **位置**：
  - 遍历顺序：`backend/packages/harness/medrix_flow/skills/loader.py:125`（`["public", "custom"]`）
  - 排序：同文件 `skills.sort(key=lambda s: s.name)`
  - enable 查询：`backend/packages/harness/medrix_flow/config/extensions_config.py:189` `is_skill_enabled(name, category)` 只按 name 查 `skills{}` map
- **现状**：public 与 custom 同名 skill 会同时出现在列表中；`get_skill(name)` 用 `next(...)` 找第一个匹配；enabled 开关一把全开全关。
- **期望**：
  1. **明确优先级**：同名时 **custom 覆盖 public**（和常见的"本地覆盖内建"心智模型对齐）。在 `load_skills` 里 dedupe，相同 name 保留 category=custom 的那份；同时在返回的 `Skill` 对象上标 `override_origin: "public"`。
  2. 若不 dedupe（保留双份），则 `is_skill_enabled` 改为 `(name, category)` 联合 key；`extensions_config.json` 的 `skills{}` schema 升级为 `{"<category>/<name>": {...}}`，旧配置做一次迁移。
  3. `get_skill(name, category=None)` 接受可选 category 参数，明确命中语义。
  4. 测试：放同名 public + custom，断言 custom 被选中；分别 enable/disable 不互相影响（若采用方案 2）。

### 2.3  Skill 根路径解析双源

- **位置**：
  - `backend/packages/harness/medrix_flow/skills/loader.py:8-19`（`get_skills_root_path` 硬编码 5 级 `.parent`）
  - `backend/packages/harness/medrix_flow/config/skills_config.py`（`SkillsConfig.get_skills_path()`）
- **现状**：两处路径解析逻辑不一致。`loader.py` 在 `skills_path=None` 时回落到硬编码，若 backend 目录层级变更或 docker 部署路径漂移，会静默指向空目录（`skills_path.exists()` 返回 False → 空列表）。
- **期望**：
  1. `get_skills_root_path` 改为优先读 `SkillsConfig.get_skills_path()`，失败再回落到硬编码。
  2. 回落时打 `logger.error`，在 gateway 启动时暴露 `/health` 里一个 `skills_root_missing: bool` 字段。
  3. 硬编码路径加单元测试 `test_skills_root_path_exists`，防止目录结构变更静默破坏。

### 2.4  Skill 安全扫描仅覆盖写路径 + 黑名单易绕过

- **位置**：`backend/packages/harness/medrix_flow/skills/security_scanner.py:38-67`
- **现状**：`scan_skill_content` 只在 `install_skill_from_archive / update_custom_skill / rollback_custom_skill` 调用；直接手工替换 `skills/custom/<name>/SKILL.md` 完全绕过。且正则黑名单对 base64 / 编码拼接 / 空格变形无效。
- **期望**：
  1. 在 `load_skills` 里对每个加载到的 skill 做"启动时扫描"（一次，结果缓存），发现 `block` 级别问题则跳过该 skill 并写告警 log。
  2. 补齐规则：`rm\s+-[rfvRFV]*\s+/`、`curl\s+.*\|\s*sh`、`$(curl ... |\s*(sh|bash))`、eval 常用变形（`$'...'`、`echo ... | base64 -d | sh`）。
  3. 保留 `warn` 级别不拦截但记录到 audit log，前端 settings 页里标红。

### 2.5  `ensure_sandbox_initialized` 直接写 `runtime.state` 绕过 reducer

- **位置**：`backend/packages/harness/medrix_flow/sandbox/tools.py:494, 526-539`
- **现状**：直接 `runtime.state["sandbox"] = ...`、`runtime.state["thread_directories_created"] = True`；ThreadState schema 未声明这些键，并发工具调用无锁。
- **期望**：
  1. 扩展 `ThreadState`（搜索 state schema 定义位置）声明这两个字段，使用 LangGraph 的 reducer 语义更新。
  2. 若 schema 不方便扩展，改为从 `runtime.context` / `runtime.store` 读写（后者是线程安全的）。
  3. 并发保护：给 acquire 加一个 `asyncio.Lock()`，同一 thread 内重复调用幂等。
  4. 测试：并发 5 次 `bash_tool(...)` 调用，断言 `provider.acquire` 只执行一次。

### 2.6  `SandboxAuditMiddleware` shlex 失败即 block + 黑名单偏窄

- **位置**：`backend/packages/harness/medrix_flow/agents/middlewares/sandbox_audit_middleware.py:37-58`
- **现状**：`shlex.split` 抛 `ValueError` 就判定 block；heredoc / 多行引号等合法但解析失败的情况被无差别拒绝。规则集覆盖窄。
- **期望**：
  1. `shlex.split` 失败时：尝试回退 `shlex.split(cmd, posix=False)`；仍失败则只告警并在 ToolMessage 里附上"命令解析失败，已放行但请注意安全"之类提示，不阻断（或由 config.yaml 开关控制严格度）。
  2. 补齐规则（见 2.4 的清单）。
  3. 把错误信息里的 `ValueError` 详情透传给模型（`parse_error: str`），便于 agent 自己修复。
  4. 单元测试：`bash -lc "cat <<'EOF'\nhello\nEOF"` 这种合法 heredoc 不被 block。

### 2.7  `get_available_tools` 每次 reset deferred registry 无锁

- **位置**：`backend/packages/harness/medrix_flow/tools/tools.py:111-141`
- **现状**：每次 `make_lead_agent` 都 `reset_deferred_registry()` 后重建。多 thread 并发工厂化会和 `DeferredToolFilterMiddleware._filter_tools` 产生 race，可能读到 None / 中间态。
- **期望**：
  1. 把 deferred registry 从"全局 mutable"改成"per-invocation immutable"：`get_available_tools` 返回 `(tools, deferred_registry)` 二元组，由 agent 通过 `runtime.context["deferred_registry"]` 或类似通道传给 middleware。
  2. 若改造成本高，最小修复：在 `reset_deferred_registry / set_deferred_registry / get_deferred_registry` 上加 `threading.RLock`，并保证 `DeferredToolFilterMiddleware` 拿到的是一个不可变快照。

### 2.8  `LoopDetection` strip tool_calls 依赖隐式 message id 语义

- **位置**：`backend/packages/harness/medrix_flow/agents/middlewares/loop_detection_middleware.py:197-203`
- **现状**：用 `model_copy(update={"tool_calls": []})` 替换最后一条 AIMessage，依赖 LangChain 在 `model_copy` 里保留 message id（以便 `add_messages` reducer 覆盖而非追加）。这是隐式契约，LangChain 升级后可能破坏。
- **期望**：
  1. 显式设置 `model_copy(update={"tool_calls": [], "id": original_msg.id})` 保留 id。
  2. 在该文件顶部加一条注释，说明"依赖 `add_messages` 基于 id 覆盖"。
  3. 加一条 unit 测试：构造两条同 id 的 AIMessage 通过 `add_messages`，断言后者覆盖前者。

### 2.9  MCP cache 以 mtime 秒级失效，同秒多次写会错过刷新

- **位置**：`backend/packages/harness/medrix_flow/mcp/cache.py:31-53`
- **现状**：缓存 key 仅用 `mtime`；同一秒内多次 `extensions_config.json` / MCP 配置写入，mtime 可能不变，LangGraph 端读不到新配置。
- **期望**：
  1. 缓存 key 改成 `(mtime_ns, size, hash(content))` 三元组。`os.stat` 可拿到 `st_mtime_ns`；`size` 对零成本；`hash` 首次即算并缓存。
  2. 或在每次 gateway 侧写入后通过 LangGraph server 的一个内部 `/admin/reset-mcp-cache` 端点显式让 cache 过期（更稳但需要内部鉴权）。

### 2.10  流式运行状态永不回收（janitor 缺失）

- **位置**：
  - 前端完成回调：`frontend/src/core/threads/hooks.ts`（搜 `completeThreadRun`）
  - runtime DB：`backend/app/gateway/routers/runs.py`
- **现状**：`completeThreadRun` 依赖 `onFinish / onError`；关窗 / 断网后，Gateway runtime DB 里 run 永远 `running`，无定时回收。
- **期望**：
  1. Gateway 侧加一个后台 janitor：
     - 每 60s 扫描 runtime DB 中状态 `running` 且 `updated_at > N 分钟前` 的 run，标记为 `stale` 并写入一条 `run_event`（`type=system_timeout`）。
     - N 建议 = `recursion_limit=1000` × 每步平均 2s + 缓冲，默认 15 分钟即可；从 config.yaml 读 `runs.janitor_timeout_minutes`。
  2. 启动 janitor 的位置：`backend/app/gateway/app.py` 的 lifespan 中用 `asyncio.create_task(...)`，shutdown 时 cancel。
  3. 前端 `frontend/src/core/api/runs.ts` 若收到 `stale` 状态需要在 UI 上以"已超时"呈现，而非无限 spinner。
  4. 测试：主动不调 `completeThreadRun`，等待 janitor 周期后断言状态变 `stale`。

### 2.11  Gateway 自研 SSE 路径未关 nginx buffering

- **位置**：
  - nginx 路由：`docker/nginx/nginx.local.conf`、`docker/nginx/nginx.conf`（找 `/api/` 通用 location）
  - Gateway SSE：`backend/app/gateway/routers/runs.py` 的 `/api/threads/*/runs/stream`
- **现状**：`/api/langgraph/*` 单独配置了 `proxy_buffering off`、`X-Accel-Buffering: no`、600s；但 gateway 自研 SSE 落在 `/api/` 通用块，默认 buffering 开启，首字节延迟高。
- **期望**：
  1. 在 `nginx.local.conf` 和 `nginx.conf` 中为 `location ~ ^/api/threads/[^/]+/runs/stream$` 增加独立块：`proxy_buffering off;`、`proxy_read_timeout 600s;`、`add_header X-Accel-Buffering no always;`。
  2. 同时确认 gateway 侧的 `StreamingResponse` 设置了 `media_type="text/event-stream"` 和 `headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache, no-transform"}`（双保险）。
  3. 手测：`curl -N http://localhost:6200/api/threads/<tid>/runs/stream`，观察首字节在 1s 内到达。

### 2.12  `/api/` 通用 timeout 偏紧 + 前端 `fetchWithTimeout` 默认 15s

- **位置**：
  - nginx 通用块：`docker/nginx/*.conf`（`proxy_read_timeout 180s` 一类）
  - 前端：`frontend/src/core/api/fetch.ts`（`fetchWithTimeout` 默认 15000ms）、`frontend/src/core/mcp/api.ts:testMCPServer`
- **现状**：`setup/test-model`、`mcp/test-server`、长 MCP 握手常常超过 15s 甚至 30s；被前端 timeout 误杀。
- **期望**：
  1. `fetchWithTimeout` 支持 per-call 覆盖（已实现就显式传入）。给 `testMCPServer / setupTestModel / installSkill` 各自传 `timeout: 60000` 以上。
  2. Nginx 通用 `/api/` 块把 `proxy_read_timeout` 提到 `300s`；给显式长耗时路由（`/api/mcp/test-server`、`/api/setup/test-model`）单独开到 `600s`。
  3. 代码层面在这些路由的 FastAPI handler 上也加 `asyncio.wait_for(..., timeout=300)` 防后端自己挂死。

### 2.13  `BETTER_AUTH_SECRET` 一秘多用 + `local-auth.ts` 回落策略不一致

- **位置**：
  - `frontend/src/server/local-auth.ts`（缺 `BETTER_AUTH_SECRET` 时回落 `password:password`）
  - `getProxyAuthSigningSecret`（拒绝回落，直接抛错）
  - `frontend/src/server/better-auth/config.ts`（better-auth 使用同一 secret）
- **现状**：同一个 `BETTER_AUTH_SECRET` 承担 (a) better-auth session (b) 浏览器 cookie 派生 (c) 代理 token 签名。且在缺失时，`local-auth.ts` 静默回落而 `getProxyAuthSigningSecret` 硬报错，同文件两种策略。
- **期望**：
  1. 拆成至少两个独立 secret：`BETTER_AUTH_SECRET`（只给 better-auth）、`MEDRIX_PROXY_AUTH_SECRET`（代理 token 专用）。旧部署兼容：两个都没配置时才回落到 `BETTER_AUTH_SECRET`。
  2. 统一回落策略：**prod** 必须配置，缺失抛错；**dev** 允许回落但打红色警告（通过 `NODE_ENV` 判断）。
  3. 更新 `README.md` 或 `config.yaml` 模板里相关 env 说明。

---

## 3. 低优先级（有空再处理）

### 3.1  `extensions_config` 缺失时默认全部启用 + 用 `print` 而非 logger

- **位置**：`backend/packages/harness/medrix_flow/skills/loader.py:154-156`
- **现状**：读 `extensions_config.json` 失败时 `print("Warning: ...")` 并默认所有 skill 启用。
- **期望**：
  1. 改用 `logger.warning`（模块级 `logger = logging.getLogger(__name__)`）。
  2. 默认策略由 config 决定：新增 `config.yaml -> skills.default_enabled: bool`，默认 `False`，避免意外把实验性 skill 全开。
  3. 同时把 loader 里其他 `print` 调用一并迁移到 logger（`parser.py:60` 也是 print）。

### 3.2  `prompt.py` 硬编码 skill 路径

- **位置**：`backend/packages/harness/medrix_flow/agents/lead_agent/prompt.py:370`
- **现状**：prompt 模板里直接写 `/mnt/skills/public/empirical-research-methods/SKILL.md`。
- **期望**：
  1. 改为占位符 `{empirical_research_skill_path}`，在 `apply_prompt_template` 注入时根据 `available_skills` 查找。
  2. 若该 skill 不在 available 列表，整段指引不注入（不会让 agent 去读不存在的文件）。
  3. 测试：禁用 `empirical-research-methods`，断言 system_prompt 里不再出现该路径。

### 3.3  `LocalSandboxProvider.get` 调 `acquire()` 未传 `thread_id`

- **位置**：`backend/packages/harness/medrix_flow/sandbox/local/local_sandbox_provider.py:15-20`
- **现状**：`if _singleton is None: self.acquire()`，未传请求的 `thread_id`。
- **期望**：签名改成 `def get(self, thread_id: str | None = None)`，内部 `self.acquire(thread_id)`；保持对 Aio/Docker provider 的语义一致。

### 3.4  Title 抛错会吞掉 Memory 入队

- **位置**：`backend/packages/harness/medrix_flow/agents/lead_agent/agent.py:252-255`（TitleMiddleware / MemoryMiddleware 都挂 `after_agent`）
- **现状**：注册顺序决定 `after_agent` 调用序；TitleMiddleware 抛错会使后续的 MemoryMiddleware 不执行，导致该轮 memory 丢失。
- **期望**：
  1. 给每个 `after_agent` 钩子包一层 `try/except Exception as e: logger.exception(...)`，不向外冒泡。
  2. 或调整注册顺序，把 Memory 放 Title 前面（memory 更关键，Title 只是 UX 优化）。
  3. 加一条集成测试：模拟 TitleMiddleware 抛错，断言 memory 仍然入队。

### 3.5  `parent_model` 经 metadata 传递脆弱

- **位置**：`backend/packages/harness/medrix_flow/tools/builtins/task_tool.py`（搜 `parent_model`）
- **现状**：从 `runtime.config.get("metadata", {})` 取 `model_name`，一旦中间层剥离 metadata 就丢失父模型，subagent 回退到默认。
- **期望**：
  1. 优先从 `runtime.context` 取（context 不会被 LangChain 中间层剥离）；`make_lead_agent` 在构造时同步写入 `config["context"]["parent_model"] = model_name`。
  2. 取不到时打 `logger.warning`，并用 config.yaml 的 `subagents.default_model` 作为兜底。

### 3.6  `env.js` 中 `GITHUB_OAUTH_TOKEN` 未进 zod server schema

- **位置**：`frontend/src/env.js`
- **现状**：`GITHUB_OAUTH_TOKEN` 只进了 `runtimeEnv`，没有在 `server` schema 里用 zod 声明，导致拼写错误/缺失无 validation。
- **期望**：在 `server: { ... }` 段加 `GITHUB_OAUTH_TOKEN: z.string().optional()`（或 required，根据业务决定）。同步检查 `runtimeEnv` 里其他 env 是否有漏声明的。

### 3.7  `backend/app/gateway/config.py` 的 `cors_origins` 是死代码

- **位置**：`backend/app/gateway/config.py`（`cors_origins` 字段 / env var）
- **现状**：字段定义但没人消费，CORS 完全由 nginx 接管。
- **期望**：直接删除该字段和相关 env 读取；在 `backend/app/gateway/app.py` 顶部加一行注释 `# CORS handled by nginx; do NOT add CORSMiddleware here.`。

### 3.8  错误响应格式不统一

- **位置**：
  - `backend/app/gateway/routers/suggestions.py`（失败静默 `return {"suggestions": []}` 200）
  - `backend/app/gateway/routers/uploads.py / channels.py / mcp.py / setup.py`（用 `{success, message}` 风格）
  - 其余 router：标准 `HTTPException`（`{detail: ...}` 形式）
- **期望**：
  1. 统一成 `HTTPException`（`{detail: str}`）风格。
  2. 对"可预期失败"（例如 suggestions 生成失败）改为返回 422 + `{detail: "suggestion_failed", reason: ...}`，前端决定是否降级展示。
  3. 添加一份 `docs/api-error-format.md` 作为契约文档（若用户同意），没同意就只改代码、保留风格注释。

### 3.9  `nginx.local.conf` 里 `provisioner:6204` 缺 resolver

- **位置**：`docker/nginx/nginx.local.conf`（`/api/sandboxes` location）
- **现状**：上游写死为 `provisioner:6204` 但本地版没有配 `resolver`，服务未启时返回 502 而非 404。
- **期望**：
  1. 改为 `http://127.0.0.1:6204`（本地版）保持与其他 upstream 一致。
  2. 或在 nginx.local.conf 顶部加 `resolver 127.0.0.1 valid=10s ipv6=off;` 并用变量化的 `set $sandboxes_upstream "http://provisioner:6204"; proxy_pass $sandboxes_upstream;`，未启时直接 503 + 明确错误体。

### 3.10  `DanglingToolCallMiddleware` 匹配规则对缺失 `tool_call_id` 不鲁棒

- **位置**：`backend/packages/harness/medrix_flow/agents/middlewares/dangling_tool_call_middleware.py`（搜 `_MISSING_TOOL_CALL_ID`）
- **现状**：当 ToolMessage 的 `tool_call_id` 缺失被兜底成 `_MISSING_TOOL_CALL_ID` 时，可能"匹配"所有缺 id 的 AIMessage tool_calls，导致错误配对（概率低但存在）。
- **期望**：
  1. 缺 id 的 ToolMessage 用 `uuid4()` 生成唯一占位 id，避免全部落到同一个 sentinel 值。
  2. 或在 `_build_patched_messages` 里对 `_MISSING_TOOL_CALL_ID` 显式拒绝配对。

---

## 4. 建议修复顺序 & 验收命令

### 4.1  建议修复顺序

建议 GPT 按下面批次推进，每批推一个 PR（或独立 commit 集）：

1. **批次 A（高优先级 / 安全）**：1.1 → 1.5 → 1.6
   - 属于权限与数据正确性，风险低且独立。
2. **批次 B（高优先级 / 运行时）**：1.2 → 1.3 → 1.4
   - 需要一起改才能让 subagent + sandbox 的 runtime 稳定。
3. **批次 C（Skill 系统）**：2.1 → 2.2 → 2.3 → 2.4 → 3.1 → 3.2
   - 读写校验对称化、冲突与路径、默认启用策略一并处理。
4. **批次 D（Middleware 质量）**：2.5 → 2.6 → 2.7 → 2.8 → 3.3 → 3.4 → 3.5 → 3.10
   - 一次性修掉 sandbox/middleware 层面的小坑。
5. **批次 E（链路 / 运维）**：2.9 → 2.10 → 2.11 → 2.12 → 2.13 → 3.6 → 3.7 → 3.8 → 3.9
   - 前后端契约、SSE、timeout、secret 管理、格式统一。

### 4.2  每批次通用验收命令

backend（必跑）：

```bash
cd backend && make lint && make test
```

frontend（涉及 `frontend/**` 时）：

```bash
cd frontend && pnpm lint && pnpm typecheck
```

env/auth/routing/build 敏感改动后（见 CLAUDE.md 定义）：

```bash
cd frontend && BETTER_AUTH_SECRET=local-dev-secret pnpm build
```

涉及 nginx / Makefile / docker / config*.yaml 时，跑一次冒烟：

```bash
make dev   # 验证 6200/6201/6202/6203 四个端口全部起来，/health 200
make stop
```

### 4.3  批次专属验收

- 批次 A：
  - `curl -X PUT http://localhost:6200/api/skills/<name> -H 'content-type: application/json' -d '{"enabled":false}'` 不带 admin token 期望 403（1.1）。
  - `curl -F "file=@/tmp/a.txt" http://localhost:6200/api/threads/<tid>/uploads` 返回体中 `files[*].size` 是数字（1.6）。
- 批次 B：
  - 在一个 chat thread 里连续启动 5 个并行 `task(...)`，观察 `_background_tasks` 无孤儿（1.2, 1.3）。
  - Aio 模式下（若接入）连续两轮 agent 调用，`sandbox_provider.acquire` 只记录一次（1.4）。
- 批次 C：
  - 往 `skills/custom/bad_skill/SKILL.md` 放无效 frontmatter，`/api/skills` 不崩且不返回 bad_skill（2.1）。
  - 同名 public + custom 同时存在，`get_skill(name)` 命中 custom（2.2）。
- 批次 D：
  - 并发 5 次 `bash_tool` 调用，日志中 `sandbox provider acquire` 只一次（2.5）。
  - `bash -lc "cat <<'EOF'\nhello\nEOF"` 不被 SandboxAudit 拦截（2.6）。
- 批次 E：
  - `curl -N http://localhost:6200/api/threads/<tid>/runs/stream` 首字节 < 1s（2.11）。
  - 主动断网关窗后，15 min 后 `GET /api/threads/<tid>/runs` 状态为 `stale`（2.10）。

---

## 5. 不要顺手改的地方（避免过度重构）

- **不要**重写 `backend/packages/harness/medrix_flow/agents/lead_agent/prompt.py` 的整体结构；只替换硬编码 skill 路径（3.2），其他 prompt 文案保持不动。
- **不要**把 `LocalSandbox` 改为更复杂的隔离方案（容器/chroot），本轮只改并发与 state 语义。
- **不要**替换 `better-auth`；2.13 只拆 secret，不动 better-auth 的 session adapter。
- **不要**重构 `extensions_config.json` 的 schema（除非实现 2.2 的方案 2 并提供迁移脚本）。
- **不要**改 LangGraph 图结构、LangChain 版本；所有修复都在 middleware / tool 层面完成。
- **不要**动 `frontend/src/core/threads/hooks.ts` 的流式 submit 逻辑；janitor（2.10）在后端实现即可。
- **不要**给 nginx 加 `add_header Access-Control-Allow-Origin *`；保持现在反射 `$scheme://$host` 的策略。
- **不要**在本轮新增大段文档（README、AGENTS.md 除外，见 3.8）；本任务目标是代码修复。

---

> 完成后请回写一份"修复总结"到本 repo `docs/` 或 PR 描述里，列出：哪些 item 已修、哪些被推迟、哪些改动偏离了本文档期望（并说明原因）。
