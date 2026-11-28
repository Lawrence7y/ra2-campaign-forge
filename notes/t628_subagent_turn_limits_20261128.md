# t628 子代理轮次上限调整（2026-11-28 16:2x）

## 裁定
用户要求「适当放开 t628 上的子代理轮次限制」。只调审计侧，执行侧不动。

## 实测依据（t628 harness.db，最近 40 条 subagent）

| 家族 | 上限 | 实际用量 | 撞顶情况 |
|---|---|---|---|
| deepseek（审计） | 35 | 最高 36；中位约 20 | **3/17 在 36/35 失败**（#540、#535、#519），另 3 条收在 28~33 轮（余量 2~7） |
| hy4（执行） | 60 | 最高 40（#498）；多数 1~16 | 0 条撞顶；`(60,80)` 区间从未成为瓶颈 |

deepseek 审计时长：n=17，最短 0.9 min、中位 6.4 min、最长 17.4 min；**无一条接近**
`SUBAGENT_MAX_RUNTIME_SEC = 2100`（35 min），所以放宽轮次不会被运行时看门狗先杀掉。

## 变更

`/home/t628/apps/harness/re_tool.py`

```
- DEEPSEEK_MAX_TURNS = 35
+ DEEPSEEK_MAX_TURNS = 50
  PRIMARY_MAX_TURNS_RANGE = (60, 80)   # 不变
```

派单钳制逻辑（未改动，仅上限被抬高）：

```python
# 审计：min(DEEPSEEK_MAX_TURNS, max(20, requested))  -> 现为 min(50, max(20, requested))
# 执行：max(60, min(80, requested or 60))
```

goal_text 同步：`跨家族审计仍由 deepseek 只读复核（<=35 轮）` → `（<=50 轮…）`，
否则主会话仍按 35 自我设限。

## 未改动的项及理由

- `PRIMARY_MAX_TURNS_RANGE = (60, 80)`：执行类从未撞顶，抬高没有收益，只增加失控面。
- `SUBAGENT_MAX_RUNTIME_SEC = 2100`：实测最长 17.4 min，留足余量；不动。
- `SUBAGENT_STALL_TIMEOUT_SEC = 900`：900s 无事件是真卡死的合理判据，与会话总轮次无关。
- `DEFAULT_MAIN_MAX_TURNS = 240` / `DEFAULT_FOLLOWUP_MAX_TURNS = 120`：主会话不在本次范围内。
- `MAX_SUBAGENTS_CAP = 3`、`PER_SUBAGENT_MB = 250`：受 t628 物理内存（3.35 GB）约束，
  轮次与并发是两回事，不放开。

## 验证（无副作用端到端）

加载 `re_tool.py`，把 `_http_json` 换成捕获桩，直接调真实的 `cmd_dispatch_subagent`：

| 角色 | 主会话请求 | 实际提交 max_turns | 说明 |
|---|---|---|---|
| audit/deepseek | 60（默认） | **50** | 原来会被压到 35 |
| audit/deepseek | 35 | 35 | 显式设低仍尊重请求值 |
| exec/hy4 | 60 | 60 | 未变 |

**重要（非对称语义）**：审计侧是「上限」不是「固定值」——
`min(50, max(20, requested))`。所以 50 以上的请求被压到 50，但主会话若只派 20/30
仍会按 20/30 执行。要 50 成为常态，靠的是 goal_text 的措辞，不是这一行常量。

另：常量加载 + 钳制算术（含边界）逐条对照全部 OK；`ast.parse` 语法通过；
`goal_text` 回读逐字一致，五 CR 不变量全绿，goal 保持 active。
`re-tool` 是每次调用时执行的脚本，改完即生效，**不需要重启 harness**
（重启会连带杀掉在跑会话，见 `_try_restart_harness` 的历史事故注释）。

## 备份

`/home/t628/apps/harness/re_tool.py.bak_turnlimits_20261128_162815`
（同批次另备份 `re_guardian.py`，但该文件本次未修改，md5 保持 `4ddbb1f8…`）

## 回滚

```bash
cd /home/t628/apps/harness
cp -p re_tool.py.bak_turnlimits_20261128_162815 re_tool.py
# 并把 goal_text 的 <=50 轮 改回 <=35 轮
```
