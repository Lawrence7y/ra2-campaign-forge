# RUNLOG.md —— W9 H1 载体装入后分层复测

run_id：`NEXT_RE_20261112_R02`　执行者：`w9_h1_layering_subagent`　全部时间为本地 +08:00（脚本日志内为 UTC ISO）。

## 时间线

| 时刻 | 事件 |
|---|---|
| 01:42:49 | 接卡。锁 `owner=lead`，无 gamemd 残留；`[2]0LoadBench_U0800_H1.yrm` 哈希核对一致（309,822 B / `e3acc130…`，`-LiteralPath`） |
| 01:43:28 | 抢锁 → `owner=w9_h1_layering_subagent` |
| 01:43–01:48 | 离线读 H1 `[Basic]Name=` = `[2] 0LoadBench U0800 H1 fp:1189b6b550ff`（及 GameMode/MaxPlayer 等原值）；研读并复用 W7 探针实现；写 `h1_probe.py`（py_compile 通过） |
| 01:49:59 | **第一趟**启动：守卫全过（5 文件哈希 + H1 哈希 + 残留 0 + 锁 self_held），pid=42396，代码签名 ok，主菜单 20.0s |
| 01:50:20–30 | 导航 SinglePlayer→Skirmish→ChooseMap；列表 **269 条**；目标 0 命中；读取失败口径空名 0；发现字面 `No Name` ×2（[91]、[97]）；写 `maplist.json`；按预设守卫 GuardStop（无目标名，不开局），优雅收尾 |
| 01:50:43 | 第一趟收尾：WM_CLOSE→taskkill→taskkill /F，残留 0；配置还原自证全过；H1 未动（changed=0） |
| 01:51–01:55 | 证据分析：ra2youli 6 个 LoadBench 文件 `[Basic]Name` 普查（U0050/U0200/U0400 → `[Pro] [2] Urban Rush`，映射自洽）；W7 三趟基线 268/0 空名核对；向 parent 发中期进展 |
| 01:56:40 | **第二趟**启动：守卫全过，pid=7568，签名 ok，主菜单 20.0s |
| 01:57:11 | 列表复核 269 条、No Name 仍为 [91]/[97]；itemdata 缓冲 768B 审计：**[97] 内嵌 ASCII `[2]0LoadBench_U0800_H1.yrm` + UTF-16 "No Name" + "No Digest"**；[91]=`prm.yrm`；[96] 对照正常（名称+digest）。hex 存 `out\nn_audit_*.hex` |
| 01:57:13–17 | 面板证据：分别选中 [91]/[97]/[96]，信息面板 statics 仅控件标题（自绘面板，无地图信息文本） |
| 01:57:17–29 | 选中 **[97]**（选图依据：No Name 条目=H1 载体候选，身份已由缓冲钉死）→ UseMap → StartGame，置前成功 |
| 01:57:30–01:58:35 | 逐拍采样 70s@30ms：**4.95–20s 区间速率 31.12/31.28/30.71（≈31/s 局内签名）**；21.0s 起 frame 停推（mode=5、fg=True，仅记录未抓栈）；**~25s 起结算屏 `GUI:Continue` 持续至 70s**；2129 拍、读失败 0 |
| 01:58:47 | 第二趟收尾：优雅关闭，残留 0；配置还原自证全过（游戏写回 RA2MD.INI 已还原，逐字节一致）；H1 未动 |
| 02:00–02:04 | 离线分析（`--analyze --in run2.ndjson`）；H1 文件段名普查：**无 [Triggers] 等结束机制**；exitstate 全程 0 |
| 02:04–02:07 | 写五类判定文档；恢复锁 `owner=lead` |

## 脚本与产物

- `h1_probe.py`：`--run`（第一趟：列表判定）/ `--run2`（第二趟：No Name 审计 + 面板 + 开局采样）/ `--analyze [--in]`。底层复用 `W7_load_baseline\load_baseline_probe.py`（启动/导航/选图/内存采样/收尾/还原），可重跑。
- `out\`：`maplist.json`、`maplist_run2.json`、`nn_audit_{91,97,96}.hex`、`run.ndjson`、`run2.ndjson`（2129 拍）、`meta.json`、`meta_run2.json`、`analyze_run2.json`、`run_stdout.txt`、`run2_stdout.txt`。

## 遗留交接（Lead）

- 实例锁已恢复 `owner=lead`。
- H1 载体仍装入在 `ra2youli`（哈希未变），还原由 Lead 执行。
- 下卡建议见 `UNCOVERED.md`。
