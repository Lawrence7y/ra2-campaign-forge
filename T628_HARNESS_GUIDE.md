# t628 Harness 远程状态检测与协作派单指南

> **适用对象**：本机（Windows）或其他环境中的 Harness、AI Agent 与运维开发者。
> **文档目的**：说明部署在独立 Linux 节点 **`t628`（`192.168.1.68`）** 上的 `t628-harness` 与 `t628-re-guardian` 自治中枢的权威边界、实时进度检测方法、防护机制以及跨节点派单策略。

---

## 1. 核心前提与权威数据源边界（必读）

1. **R17 逆向唯一权威运行态在 `t628`**：
   - 自 `2026-11-22 21:22` 起，R17 静态逆向任务的持续推进已迁移至 **`t628`（`192.168.1.68`）** 独立闭环运行，权威目录为：
     ```text
     /home/t628/projects/ra2-campaign-forge
     ```
   - `t628` 上由 `t628-re-guardian` 驱动主会话（`re-main`）与子代理（`subagent`） 7×24 自动推进轮次并压缩接力。
2. **本机 `lead/` 目录为迁移前历史快照**：
   - 本机 `D:\Project\ra2-campaign-forge\lead\` 仅保留到迁移前快照（R66/R67），**不是当前最新逆向进度**。
   - **严禁**将本机旧五件套（`R14_COMMON.md`、`LEAD_LOCK`、`GOAL_THREE_TARGETS_20261018.md`、`STATUS_BOARD.md`、`BOARD_ARCHIVE.md`）直接推送覆盖 `t628`。
3. **双执行节点职责分工**：

| 节点 ID | 宿主机 / IP | 定位与工作区 | 适用任务 |
|---|---|---|---|
| `t628` | Debian 13 · `192.168.1.68`<br>（Tailscale `100.69.178.8`，3.35 GB RAM） | `/home/t628/projects/ra2-campaign-forge` | 7×24 静态二进制逆向（`gamemd.exe`）、门禁校验、FACT_INDEX 审计、轮次自治接力 |
| `win-main` | Windows 主力机 · `192.168.1.30`<br>（由 `D:\Project\t628\harness_win_worker.py` 接入） | `D:\Project\ra2-campaign-forge` | 副屏 `\\.\DISPLAY1` 真机 `gamemd.exe` 对局与动态逆向验证（不占用 `t628` 静态队列与内存） |

---

## 2. 服务拓扑、入口与认证方式

### 2.1 服务清单

| 服务 / 端口 | 访问地址（局域网 / Tailscale） | 作用与关键约束 |
|---|---|---|
| **`t628-harness`** (`:8897`) | `http://192.168.1.68:8897`<br>`http://100.69.178.8:8897` | Claude Code `2.1.330` 任务调度与 SSE 实时流中枢；数据库 `/home/t628/apps/harness/data/harness.db`；cgroup 限额 `MemoryHigh=1600M` / `MemoryMax=1800M` / `MemorySwapMax=768M`；允许 `cwd` 白名单：`/home/t628`、`/mnt/xiaomi`、`/opt`、`/etc`、`/tmp` |
| **`t628-re-guardian`** (`:8896`) | `http://192.168.1.68:8896`<br>`http://100.69.178.8:8896` | 独立 R17 自治监控与守护中枢（`MemoryMax=128M`）；网段白名单（`127.0.0.0/8`、`192.168.1.0/24`、`100.64.0.0/10`）内免 Token 访问；接口：`/healthz`、`/api/overview`、`/api/goal` |
| **`workbuddy2api`** (`:7863`) | `t628` 本机 `127.0.0.1:7863`（Docker） | 大模型网关；可用模型：`cn:deepseek-v4.1-flash`（默认）、`cn:hy4flash`、`cn:hy4flash-free` |
| **`t628-stats`** (`:8899`) | `http://192.168.1.68:8899/stats` | 宿主机 CPU、内存、Swap、磁盘、容器状态、挂载检查与 `win-main` WOL 唤醒接口 |

### 2.2 认证与工具位置（严禁向本仓库写入明文凭据）

- **CLI 工具（推荐）**：`python D:\Project\t628\harness.py <子命令>`
  - 已在本机配置文件 `C:\Users\Administrator\.config\harness\config.json` 中保存 `url` 与 `token`，无需手工传参。
- **直接调用 `:8897` HTTP API**：
  - 从 `C:\Users\Administrator\.config\harness\config.json` 读取 `token` 字段，放入请求头 `Authorization: Bearer <token>`。
  - 若需 Web 口令、SSH/API 完整凭据，请参阅本机运维目录 `D:\Project\t628\01-凭据.md`（切勿复制到本仓库）。
- **SSH 只读查看 / 排障兜底**：
  ```powershell
  ssh -i C:\Users\Administrator\.ssh\t628_ed25519 t628@192.168.1.68 "<command>"
  # 若 Windows 开启了 FlClash TUN 等虚拟网卡，请显式指定源地址：
  ssh -i C:\Users\Administrator\.ssh\t628_ed25519 -b 192.168.1.30 t628@192.168.1.68 "<command>"
  ```

---

## 3. 标准状态检测流程（其他 Harness 开局必跑）

在向 `t628` 派发任务或读取进度前，**务必先执行第 3.1 节与第 3.2 节检测**。

### 3.1 一步免 Token 总览（首选：`:8896/api/overview`）

直接在 PowerShell 运行以下只读命令，即可一次获取 R17 轮次、五项 CR 不变量、动态内存配额、`harness` cgroup 负载、主/子会话列表、最近告警以及压缩摘要：

```powershell
$ov = Invoke-RestMethod -Uri "http://192.168.1.68:8896/api/overview" -TimeoutSec 6
[PSCustomObject]@{
  ok                = $ov.ok
  goal_active       = $ov.goal.active
  current_round     = "R$($ov.goal.current_round)"
  compactions       = $ov.goal.compaction_count
  all_invariants_ok = $ov.all_invariants_ok
  board_lines       = $ov.board_lines
  avail_mb          = $ov.subagent_budget.avail_mb
  max_subagents     = $ov.subagent_budget.max_subagents
  cg_mem_mb         = $ov.harness_cgroup.memory_current_mb
  cg_swap_mb        = $ov.harness_cgroup.swap_current_mb
  cg_procs          = ($ov.harness_cgroup.procs).Count
} | Format-List
$ov.main_sessions | Select-Object -First 5 id, status, model, num_turns, max_turns, title | Format-Table -AutoSize
$ov.subagent_sessions | Select-Object -First 5 id, parent_id, status, model, num_turns, max_turns, title | Format-Table -AutoSize
$ov.incidents | Select-Object -First 5 ts, level, msg | Format-Table -AutoSize
$ov.compact_state.Substring(0, [Math]::Min(1200, $ov.compact_state.Length))
```

### 3.2 CLI 快速检查命令

```powershell
python D:\Project\t628\harness.py status      # 宿主机 CPU / 内存 / 磁盘 / 队列并发
python D:\Project\t628\harness.py nodes       # 检查 t628 与 win-main 在线状态、当前 running_task_id
python D:\Project\t628\harness.py models      # 列出可用模型
python D:\Project\t628\harness.py ls -n 20    # 最近 20 条任务
python D:\Project\t628\harness.py show <id>   # 查看指定任务详情与输出摘要
python D:\Project\t628\harness.py logs <id>   # 查看任务事件流（加 -f 实时跟踪）
```

### 3.3 健康度判据与异常处置

| 观测指标 | 健康区间 | 异常表现 | 建议动作 / 排查命令 |
|---|---|---|---|
| `:8896/api/overview` | HTTP 200，`ok=true` | 超时或返回 HTTP 503（`ok=false`） | 说明 `:8897` 可能卡死或 cgroup 内存顶满；检查返回体 `harness_cgroup` 与 `incidents`，等待 `Harness-Watchdog` 自动自愈，或 SSH 查 `sudo journalctl -u t628-re-guardian -n 30` 与 `sudo journalctl -u t628-harness -n 30` |
| `all_invariants_ok` | `true`（`1081/137/337/0/2952`） | `false` | **立即停止所有写派单**；guardian 会尝试从 `R17_LEAD_BASELINE` 自动回滚，SSH 执行 `re-tool get_goal` 核验具体文件 |
| `harness_cgroup.memory_current_mb` | `< 1200 MB` 且 `swap_current_mb < 300 MB` | `>= 1440 MB`（达到 `MemoryHigh` 90%） | 暂缓派重型任务，观察 `Mem-Guard` 是否触发清杀失控子进程 |
| `subagent_budget.avail_mb` | `>= 500 MB` | `< 300 MB` | 检查是否有 `ddl` Playwright 抓取瞬时峰值或高内存脚本，勿并发派发多个任务 |
| `nodes` 中 `win-main` | `online=True` | `OFFLINE` | 如需真机验证，可先调用 `POST http://192.168.1.68:8897/api/nodes/win-main/wake` 发 WOL 唤醒，或确认本机 `D:\Project\t628\harness_win_worker.py` 是否运行 |

---

## 4. `t628-re-guardian` 自治接力与保护机制说明

`t628-re-guardian` 是部署在 `t628` 的独立 systemd 守护服务，核心行为如下：

1. **自治推进与接力**：
   - 当 `goal.active == true` 且五项 CR 不变量全绿时，自动按 `COMPACT_STATE.md` 与 `re_goal.json` 的当前轮次拉起下一轮 `re-main` 主会话。
   - 若主会话因 `max_turns` 截断，自动调用 `/api/tasks/<id>/followup` 注入 `[自动续跑接管]` 完成收口。
   - 若主会话因其他异常退出，按指数退避（15s → 300s）注入 `[自动故障接管]` 重新拉起。
2. **四重自动化防护**：
   - **CR 不变量守护**：持续校验 `R14_COMMON.md`（CR=1081）、`LEAD_LOCK`（CR=137）、`GOAL_THREE_TARGETS_20261018.md`（CR=337）、`STATUS_BOARD.md`（CR=0 且行数 `<= 300`）、`BOARD_ARCHIVE.md`（CR=2952）；破坏时备份现场 `.broken_<ts>` 并从 `R17_LEAD_BASELINE/` 最新合格快照自动恢复。
   - **`Mem-Guard` 内存护栏**：每轮巡检当 cgroup 达到 `MemoryHigh`（1600M）的 90% 或系统 `MemAvailable < 180 MB` 时，自动 `SIGKILL` 掉非 `server.py` / `claude` 主体的失控子进程（RSS `>= 900 MB`）或大内存孤儿进程（`PPid == 1` 且 RSS `>= 250 MB`）。
   - **`Stall-Watchdog` 停滞看门狗**：子代理超过 `900s` 无新事件或总运行时长超过 `2100s` 自动取消；主会话在无存活子代理时 `1080s` 无事件自动取消，有存活子代理时 `2400s` 无事件自动取消。
   - **`Harness-Watchdog` 假死恢复**：连续 6 次请求 `:8897` 超时先强制清理高内存子进程；若仍无响应则在 300s 冷却期内自动重启 `t628-harness.service`。

---

## 5. 跨 Harness 派单策略与协作协议

### 5.1 派单前 Pre-flight 检查清单（5 项）

1. `:8896/api/overview` 返回 `ok == true`。
2. `all_invariants_ok == true`（五项 CR 不变量全绿）。
3. `avail_mb >= 500` 且确认 `harness_cgroup.memory_current_mb < 1200`。
4. 明确本次任务**是否会修改 R17 五件套或影响 `_r<N>/`**。
5. 明确目标节点：`t628`（静态分析）或 `win-main`（真机运行），且目标节点 `online == true`。

### 5.2 四类场景决策矩阵

| 场景 | 是否需要暂停 Goal | 推荐节点与工作目录 | 派单策略与注意事项 |
|---|---|---|---|
| **A. 独立静态调研 / 交叉复算**（不改 R17 五件套） | **否**（保持自治运行） | `--node t628 --ra2`（或默认 `/home/t628/harness-work/task-<id>/`） | 将输出写入独立目录（如 `_ext/<tag>/` 或任务工作区）；`t628` 主队列 `max_concurrency=1`，若当前有 `re-main` 正在运行，新任务会自动排队并在该轮收口间隙执行 |
| **B. 需要立即插队或修改 R17 五件套 / 核心代码** | **是（必须先暂停）** | `--node t628 --ra2` | 1) 先 `POST :8896/api/goal {"action":"pause"}`；<br>2) 等待当前 `re-main` 自然收口（或确认需要中断时 `harness.py cancel <id>`）；<br>3) 执行任务并验证 `re-tool get_goal` 显示 `all_invariants_ok: true`；<br>4) 完成后 `POST :8896/api/goal {"action":"resume"}` 恢复自治 |
| **C. 真机 `gamemd.exe` 对局 / 动态逆向** | **否** | `--node win-main --ra2` | 不占用 `t628` 静态队列与 3.35 GB 内存；通过 `harness_win_worker.py` 在本机副屏 `\\.\DISPLAY1` 运行验证 |
| **D. 调整自治方向 / 触发手动压缩** | **否** | 直接调用 `:8896/api/goal` | 传 `{"goal_text": "..."}` 动态更新后续轮次目标，或传 `{"action": "compact_next"}` 请求下一轮优先压缩 |

### 5.3 派单 Prompt 强制红线（必须写入下发给 `t628` 的任务指令中）

1. **防 OOM 内存硬红线（`t628` 物理内存仅 3.35 GB）**：
   - 严禁对 `gamemd.exe` 整段 `.text`（4 MB）开启 Capstone `md.detail = True` 后一次性调用 `md.disasm()`（堆对象会暴涨至 >1.5 GB 并触发 `Mem-Guard` 或 cgroup OOM）。
   - 全段线性扫描必须使用 `md.disasm_lite()` 或 `<= 64 KB` 分块流式迭代并及时释放对象，仅对命中的少数目标地址单独开启 `detail = True`。
   - 后台命令必须带 `timeout`，收口前确认无孤儿残留进程；**严禁使用 `pkill -f` 或 `kill $(pgrep -f ...)`**（易误杀自身 `claude -p` 命令行）。
2. **防越界红线**：
   - 严禁任务修改或重启 `t628-harness`、`t628-re-guardian`、`workbuddy2api` 服务本体。
   - 非 `re-main` 外部任务严禁直接修改 `R14_COMMON.md`、`LEAD_LOCK`、`GOAL_THREE_TARGETS_20261018.md`、`STATUS_BOARD.md`、`BOARD_ARCHIVE.md`。
3. **模型与轮次建议**：
   - 深度逆向 / 审计：`cn:deepseek-v4.1-flash`（默认），`--max-turns 80` ~ `120`。
   - 快速检索 / 轻量脚本验证：`cn:hy4flash`，`--max-turns 40` ~ `60`。

---

## 6. 常用 CLI / HTTP API 派单与结果回收模板

### 6.1 使用 `harness.py` CLI

```powershell
# 1. 在 t628 上派发只读静态分析任务并实时跟踪输出
python D:\Project\t628\harness.py run --node t628 --ra2 --model cn:deepseek-v4.1-flash --max-turns 80 --title "外部核验: 检查虚表偏移" "只读分析 ra2bench/gamemd.exe 某偏移，产物写进 _ext/check_vt/，禁止修改 R17 五件套；扫描全段禁止对整段 .text 开启 md.detail=True。" -f

# 2. 在 Windows 副屏派发真机动态验证任务
python D:\Project\t628\harness.py run --node win-main --ra2 --model cn:deepseek-v4.1-flash --max-turns 60 --title "win-main 真机验证" "在副屏验证..." -f

# 3. 追踪 / 追问 / 取消 / 重试
python D:\Project\t628\harness.py show <task_id>
python D:\Project\t628\harness.py logs <task_id> -f
python D:\Project\t628\harness.py followup <task_id> "补充反控自测输出" -f
python D:\Project\t628\harness.py cancel <task_id>
python D:\Project\t628\harness.py retry <task_id>
```

### 6.2 直接调用 HTTP API（PowerShell 示例）

```powershell
$cfg = Get-Content "$env:USERPROFILE\.config\harness\config.json" | ConvertFrom-Json
$headers = @{ Authorization = "Bearer $($cfg.token)" }

# 提交任务
$body = @{
  title     = "外部调研任务"
  prompt    = "你的提示词（遵守第 5.3 节防 OOM 与防越界红线）"
  node      = "t628"
  cwd       = "/home/t628/projects/ra2-campaign-forge"
  model     = "cn:deepseek-v4.1-flash"
  max_turns = 80
} | ConvertTo-Json -Depth 4
$resp = Invoke-RestMethod -Uri "$($cfg.url)/api/tasks" -Method Post -Headers $headers -ContentType "application/json; charset=utf-8" -Body $body
$tid = $resp.task_id

# 增量轮询事件 / 取消任务
Invoke-RestMethod -Uri "$($cfg.url)/api/tasks/$tid/events?after=0" -Headers $headers
# Invoke-RestMethod -Uri "$($cfg.url)/api/tasks/$tid/cancel" -Method Post -Headers $headers -ContentType "application/json" -Body "{}"

# 暂停 / 恢复 :8896 自治 Goal（局域网白名单免 Token）
Invoke-RestMethod -Uri "http://192.168.1.68:8896/api/goal" -Method Post -ContentType "application/json" -Body '{"action":"pause"}'
Invoke-RestMethod -Uri "http://192.168.1.68:8896/api/goal" -Method Post -ContentType "application/json" -Body '{"action":"resume"}'
```

### 6.3 只读查看 `t628` 最新逆向结论与产物

```powershell
# 查看最新自动压缩摘要与下轮待办
ssh -i C:\Users\Administrator\.ssh\t628_ed25519 t628@192.168.1.68 "head -n 60 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/COMPACT_STATE.md"

# 查看运行看板末尾最近轮次
ssh -i C:\Users\Administrator\.ssh\t628_ed25519 t628@192.168.1.68 "tail -n 60 /home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/STATUS_BOARD.md"

# 列出最近轮次产物目录
ssh -i C:\Users\Administrator\.ssh\t628_ed25519 t628@192.168.1.68 "ls -lt /home/t628/projects/ra2-campaign-forge/ | grep '^d' | head -n 15"
```

---

## 7. 关键运行事实快照（编写时采样：`2026-11-24 11:49`）

> ⚠️ 本节仅作背景参考，**调度与判断请一律以第 3 节实时查询输出为准**。

- **R17 进度**：已完成至 **R108**（累计自动压缩 39 次），五项 CR 不变量 **5/5 PASS**（看板 256/300 行），当时正在执行 **R109**（`#183` 主会话）。
- **节点状态**：`t628`（`online`）与 `win-main`（`online`，`WIN-B7KIC1TNL6R`）均在线。
- **后台优化基线**：`t628-re-guardian` 已集成 `Mem-Guard`、`Stall-Watchdog` 与 `Harness-Watchdog`；Jellyfin 已关闭 Trickplay / 章节图提取与 SMB 实时监控，日常待机占用约 54 MB，不与 `t628-harness` 争抢资源。
