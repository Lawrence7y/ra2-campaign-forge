# W10 RUNLOG —— 单变量验证执行日志（时间均为 UTC；本地 = +08:00）

- run_id：`NEXT_RE_20261112_R02`；卡：W10 CRLF 单变量验证（只到地图列表，不开局）
- 探针：`crlf_verify.py`（复用 `W9_h1_layering\h1_probe.py` 的 read_map_names_diag /
  ui_summary 与 `W7_load_baseline\load_baseline_probe.py` 全部底层）。
- 原始流：`out\run_stdout.txt`、`out\run.ndjson`、`out\meta.json`。

## 时间线（run，2026-11-12T18:14 → 18:15 UTC）

| 时刻(UTC) | 阶段 | 事件 |
|---|---|---|
| 18:14:56 | S0 | 锁 owner=lead(lead_free) → w10_crlf_verify_subagent；gamemd 残留 0 |
| 18:14:56 | S0 | 五文件基线哈希全 match；H1 载体 315,706 B / `afb18a33…` match |
| 18:14:56 | S0 | ra2youli 清单 648 项（before） |
| 18:14:57 | S1 | WMI 启动：launcher=31456 → pid=7568（wmi_child_parent_pid） |
| 18:14:58 | S1 | is32=True；代码签名@0x55DE4F ok |
| 18:15:18 | S1 | 主菜单就绪（20.0s）；游戏窗口 hwnd=25560336 |
| 18:15:18–24 | S2 | 点击 GUI:SinglePlayer → GUI:Skirmish → GUI:ChooseMap（全 True） |
| 18:15:27 | S2 | ListBox=29497018，条目=269（基线 268，Δ+1，符合预期） |
| 18:15:27 | S2 | 269 条全量读取：diag 全 ok；**字面 No Name = [91, 97]**；读失败 0；空串 0；目标显示名命中 0（完整名/子串1 `loadbench u0800 h1`/子串2 `0loadbench_u0800_h1` 均无） |
| 18:15:27 | S3 | itemdata 768B 审计：[91] No Name/prm.yrm/MAYV…9M=；[96] [2] 0LoadBench U800/[2]0LoadBench_U0800.yrm/aAH…Nc=；**[97] No Name/[2]0LoadBench_U0800_H1.yrm/No Digest** |
| 18:15:29 | S4 | 面板快照（对照 [96]）：statics 为对话框级标签（GUI:ChooseMap 等）；无目标条目面板（无显示名命中） |
| 18:15:42 | P1 | WM_CLOSE → 6s 未退 → taskkill(无/F) → taskkill /F → 存活=False |
| 18:15:42 | P1 | 残留 0；清单 648 项（after，diff 全空）；配置还原 3 文件 byte_identical；exe/dll unchanged |
| 18:15:42 | P1 | H1 载体 hash_after = `afb18a33…`（untouched=true）；锁恢复 owner=lead |

## 分析（--analyze，可重跑）

- 18:16:35 首跑：verdict=`crlf_not_the_cause`；修正目标钉身份回退（显示名 0 命中时
  按内嵌文件名 `0loadbench_u0800_h1` 钉，不再误取 [91]）。
- 18:18:43 复跑（最终）：verdict=`crlf_not_the_cause`；target_basis=
  `embedded_filename:0loadbench_u0800_h1`；列表逐索引 diff = 0 差异；目标缓冲
  逐字节 diff = 7/768（散落单字节，名称槽/文件名/digest 区全等）；
  `out\itemdata_audit.hex` 由 `itemdata_audit_97.hex` 复出（目标条目 hex 交付）。

## 判定（详见 VERDICT.md）

**行尾不是主因 [否证]**：仅把行尾改为 CRLF（5,884 处）后，条目仍进列表（269），
[97] 仍为字面 `No Name`，digest 仍 `No Digest`，与 W9（裸 LF 原件）逐字段全同。
下一变量 = 节顺序（`[Preview]` 打头），本卡未改动、未推断，交回 Lead。
