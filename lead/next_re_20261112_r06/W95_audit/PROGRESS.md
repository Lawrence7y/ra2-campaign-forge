# W95 · PROGRESS

> 卡：W95（异族独立审计）｜执行 `w95-audit`｜写域 `lead\next_re_20261112_r06\W95_audit\`
> **离线只读**：未启动游戏、未注入、未改任何二进制、未改 `ra2youli`。

## 时间线（`Get-Date`，Asia/Shanghai）

| 时间 | 动作 |
|---|---|
| 2026-11-14T16:36:26+08:00 | 开卡；建 `W95_audit\` / `EVIDENCE\` / `work\`；写 `HEARTBEAT.txt` |
| 16:37 | 定位主张来源：`§626/§627` 在 `r06\REVIEW\LEAD_VERIFY_W91.md`；`§625` 在 `r04\W88_envelope\ENVELOPE.md` + `r04\REVIEW\LEAD_VERIFY_W88.md`；N=3 配对在 `r05\REVIEW\LEAD_VERIFY_W90.md` + `r05\W90_replicates\out\analysis.json` |
| 16:38 | 读 `ENVELOPE.md`(182行) / `LEAD_VERIFY_W88.md`(86行) / `LEAD_VERIFY_W90.md`(50行) / `LEAD_VERIFY_W91.md`(43行)；读 W88 `analysis.json`(417行) / W90 `analysis.json`(200行) |
| 16:39 | **E1 落盘+运行**：`e1_crewed_override_and_design.py` — 覆写字节、C6 vs CTRL_C6 逐字段 diff、建筑普查 |
| 16:40 | 读 C6 设计简报，发现 "**Crewed override OFF**" ⇒ 转去核 `w88_build.py` 的 step 表（C6 无覆写、C4/C7 有） |
| 16:41 | **E2 落盘+运行**：`e2_*` — 17 趟 ndjson 字段并集（24 个，无计数字段）、三代理量级、三对描述统计 |
| 16:42 | **E3 落盘+运行**：`e3_*` — **独立复算**六趟 CPU 率（差 ≤0.0013 pp）+ **统一 150 s 窗口重算** |
| 16:43 | 读原始截图：`C6/combat_t150.png` vs `CTRL_C6/combat_t120.png` ⇒ 交战臂**基地全毁+满地弹坑**，对照臂**基地完整零弹坑** |
| 16:44 | **E4 落盘+运行**：`e4_*` — k/N 概率表、混杂量级算术（≤24 个 ≈ 0.315 pp ≈ 2.0 %） |
| 16:44 | 查 `re_atlas`：`kb/30_ini_subsystem.md` §13.5（`Init` 读 3 份 INI 含 map INI、后读覆盖先读）、§19.3（逐类节走 rulesmd+artmd 两份）；核 `ra2forge/` 无 rules 覆写能力 |
| 16:45 | **E5 落盘+运行**：`e5_*` — 度量完整性（`win_tid` 唯一 / 100 % 前台 / 0 次回退 / 6.04 ms / 0 读失败） |
| 16:46 | **E6 落盘+运行**：`e6_*` — 重叠前提核查（2×2 vs 3×2 模型结论相反：0 格 vs 10 格） |
| 16:46 | **E7 落盘+运行**：`e7_*` — 全 22 座建筑重叠普查 ⇒ **零重叠臂仍有 14 格 TESLA 重叠** |
| 16:47 | 写 `AUDIT.md` / `UNKNOWNS.md` / `DISAGREE.md` / 本文件 |

## 纪律自查

- 只读：✅ 未启动游戏、未注入、未 attach 进程、未改任何二进制或 MIX。
- 写域：✅ 只写 `W95_audit\`（`EVIDENCE\` 7 脚本 + 7 stdout，`work\` 3 个中间 dump）。
- 需要的文件：✅ 全部**原地只读**（没有复制任何大文件到本卡；只读 `run.ndjson` / 设计 JSON / 源码 / 截图 / atlas 文本）。
- 分级：✅ 每条结论标 `[本次实测]` / `[静态读码]` / `[静态推断]` / `[未证]`。
- 统计纪律：✅ **无 p 值、无 CI、无"显著"**。只有描述性统计（极差/比值/分离量）与初等概率（(2/3)^N）。
- 小步落盘：✅ 每个脚本先写文件再跑，stdout 用 `Tee-Object` 同时落盘。
- 不复述：✅ 我的正面贡献是 **7 个独立产出**（独立复算 / 统一窗口 / 覆写字节实测 / 全建筑重叠普查 / 重叠前提核查 / 度量完整性 / k-N 概率表），
  其中 **§625(a) 的"零重叠臂仍有 14 格重叠"** 与 **"工具的重叠检查用 2×2 因而从未验过前提"** 是本卡新发现。

## 交付物

| 文件 | 内容 |
|---|---|
| `AUDIT.md` | 三条主张判决 + Lead 混杂判断 + 5 项必查证据 + 混杂严重性排序表（10 项，含判别实验）+ 最该先做的 1 个实验 + "还缺什么" |
| `UNKNOWNS.md` | U1–U8；U8 为"确认不是问题"的正面项 |
| `DISAGREE.md` | D1–D7；D7 为自我边界 |
| `PROGRESS.md` | 本文件 |
| `EVIDENCE\e1_crewed_override_and_design.{py,stdout.txt}` | 覆写字节 / C6-vs-CTRL_C6 逐字段 diff / 建筑普查 / 乘员上界 |
| `EVIDENCE\e2_proxy_inventory_and_pairstats.{py,stdout.txt}` | 17 趟字段并集 / 代理量级 / 三对描述统计 / 窗口可比性 |
| `EVIDENCE\e3_independent_recompute_common_window.{py,stdout.txt}` | **独立复算**六趟速率 / 统一 150 s 窗口重算 / 窗口长度效应 / 轮次偏移 |
| `EVIDENCE\e4_kn_probability_and_confound_math.{py,stdout.txt}` | k/N 概率表 / 混杂量级算术 |
| `EVIDENCE\e5_metric_integrity_checks.{py,stdout.txt}` | `win_tid` / `win_foreground` / 单调性 / 采样节拍 |
| `EVIDENCE\e6_overlap_premise_check.{py,stdout.txt}` | 2×2 vs 3×2 模型、格数、footprint span |
| `EVIDENCE\e7_full_structure_overlap_census.{py,stdout.txt}` | 全 22 座重叠普查（NAPOWR 10 / TESLA 14） |
| `work\` | `_ini_sections_dump.txt` / `_ini_globals_dump.txt` / `_foundation_dump.txt`（中间取证） |
| `HEARTBEAT.txt` | 开卡时间戳 |

## 未做的事（如实）

- 未解 ra2youli 的 MIX 自提 `rulesmd.ini`（§3-1 用 `[转引]` + 本地复扫）；未提 `artmd.ini` ⇒ `Foundation` 仍 `[未证]`。
- 未做任何运行时验证（本卡纪律禁止），所以没有"极性对照已跑"这回事——那是 AUDIT §5 交给下一轮的动作。
- 未做像素统计（截图只作定性用）。
