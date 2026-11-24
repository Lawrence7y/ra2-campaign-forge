# RUNLOG · W17 RE-N04f（B 臂换载体负载对照）

run_id `NEXT_RE_20261112_R02` ｜ 卡 RE-N04f ｜ 2026-11-13 04:54–05:27+08（Asia/Shanghai）

## T0 开工核对（04:54–05:04）
1. 锁 `owner=lead` 可认领；`Get-Process gamemd` 残留 = 0。
2. **卡面文件名勘误**：实际文件为 `[8]音速公路_SonicHighways.yrm`（半角括号），252,270 B ✓；`【8】` 为普查表写法。
3. **卡面显示名勘误**：离线实读 `[Basic].Name = "[8] Sonic Highways"`（第 1129 行）；普查表 name 列 `Invisible Light Post` 是文件中第一个 `Name=`（第 57 行，建筑定义段）——**普查 bug**。MaxPlayer=8 / MinPlayer=2 / GameMode=battle / MultiplayerOnly=1 / Official=yes / 含 [Events]。
4. sha256 开工实算 `0805e637…712f3` 钉定入探针；复制 W15 探针为 `load_b_probe.py` + 观察者为 `load_b_ui_watch.py`（改路径/载体/判据/新字段 win_cyc_delta/cyc_est_ms/ctx/A8ED50 事件；语法编译通过）。

## attempt1（05:04:32 启动，WMI pid=38984）
- S0 锁认领 `owner=W17-load-B-subagent`、残留 0、5 文件哈希全对、B 载体哈希对、清单 647 项。
- S1 启动成功：pid=43632、is32、代码签名 @0x55DE4F ok、主菜单就绪。
- S2 导航：SinglePlayer→Skirmish→ChooseMap，地图 ListBox 条目=268；模式 `['[8] Sonic Highways','Sonic Highways','Invisible Light Post']` **0 命中**（空名条目 0）→ RuntimeError。
- finally 自愈：停观察者（未启动过）→ WM_CLOSE + taskkill(无/F) + taskkill /F → pid 43632 退出 → 残留 0 → 配置逐字节还原（实算一致）→ 清单 diff 647→647 全空 → meta_end → 锁恢复 `owner=lead`。exit_code=1。
- 判定：失败发生在首个 frame>0 之前 ⇒ 按预设允许 1 次重试。

## attempt2（05:08:46 启动，WMI pid=17808）
- 探针增补：选图前全列表 268 条名称落盘 `out\maplist_names.json` + 关键词探针日志；模式追加 `['音速公路','音速']`。
- S0/S1 同 attempt1（pid=39956）。S2：268 条中 5 模式仍 **0 命中**；dump 前 80 条显示列表主体为本地化中文官方名 + 部分伪 Unicode 乱码名 → RuntimeError。
- finally 自愈同 attempt1 全链成功（残留 0 / 还原一致 / 锁回 lead / meta_end）。exit_code=1。

## T1 离线对账（05:10–05:25，未再启动游戏）
- `match_maplist.py` / `match_maplist2.py`：277 散装文件 ↔ 268 列表条目。
- 结论（详见 LOAD_B.md §4）：列表 = 内置本地化官方图 92 条（索引 0–91）+ 散装 .yrm 176 条（92–267）；.mpr/.map 0 上列表；未上图 .yrm 48 张反向字节级 48/48 ABSENT，其中 47 张 official=yes 全为西木系官方图英文名 ⇒ **B 无 skirmish 列表条目**（官方去重机制，推断标注）。
- 假阴性排除：把 48 张未上图文件的 [Basic].Name 原始字节做零扩展串与 268 条原始条目精确比对，无一条命中 ⇒ 非乱码恢复缺陷。
- LoadBench 五张全在列表；U0050/U0200/U0400（+1 张）`[Basic].Name` 同名撞车 `[Pro] [2] Urban Rush`。
- `analyze_load_b.py`：无 ingame 样本 ⇒ `out\analysis.json` 最小档 `[B 不可用]`；`out\tickcost.csv` 未生成（按无数据分支）。

## 结论分档
**`[B 不可用]`**（未进图；结构性原因，未重启凑时长）。

## 产物
`load_b_probe.py`（可重跑；--map-patterns 为选图旋钮）、`load_b_ui_watch.py`、`analyze_load_b.py`、`match_maplist.py`、`match_maplist2.py`、
`out\run.ndjson`（attempt2，49 行）、`out\meta.json`、`out\analysis.json`、`out\maplist_names.json`、
`maplist_reconcile.json`、`maplist_reconcile2.json`、`LOAD_B.md`、`SAFETY.md`、`CONFIG_RESTORE.md`、`RUNLOG.md`、`UNCOVERED.md`。
