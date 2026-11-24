# W44 · DISAGREE（差异 / 更正 / 与上游口径的边界）

> 口径与 `E2E_RESULT.md §0` 一致。本卡**未推翻任何已签发事实**；本文件记录
> ① 本卡相对上游卡/任务卡的口径差异，② 本卡新增的、需要下游注意的观测，
> ③ 本卡自身的驱动缺陷与自证脚本误判（照录，不粉饰）。

---

## D1 · 沙箱选择：从 `ra2youli` 只读复制，而非复用 W35 沙箱 `[本卡决策]`

任务卡 §2 允许「从 `ra2youli` 只读复制沙箱（**或**复用 `W35_mapselmd_live\sandbox_game`，须先 `verify` exit 0）」。本卡选**前者**，理由（均 `[本次实测]`）：

- W35 沙箱当前是「W27 包已装 + 散装追加 `MAPSELMD.INI`」态（`ra2forge_install.json=c25ac593…`，非 v0.3），与任务卡 §2「处理既存旧包 **v0.3**」不符；复用它还要先额外清理。
- 新复制沙箱初始态干净：`ra2forge_install.json=fe3bdf62…`（v0.3）、无散装 `MAPSELMD.INI`、无散装 `ra2md.csf`、官方 `BATTLEMD.INI` 原样 —— 正好可作「卸载还原」的清晰起点。
- 所有改动落在 `W44_c_line_e2e/` 写域内，不触碰其它卡的沙箱。
- 代价：多 1.9 GB 磁盘 + 一次 robocopy（~2 s，实测 rc=1）。

⇒ **不是**对 W39/W40「复用 W35 沙箱」做法的否定；两条路径卡面都允许。

## D2 · 用 v12 工具卸载 v0.3 旧包（W27 §2 用的是 v9） `[本卡差异，结果一致]`

`[转引]` W27 §2 的 `uninstall --game <sandbox> --json` 在 v9 下得到 `exit 0 / status=completed / 9 actions / degraded-mode 警告`。本卡用 **v12**（本卡指定的构建工具）执行同一命令，`[本次实测]` 得到完全同型结果：`exit 0`、`status=completed`、9 条 actions、`verify` 卸后 exit 0。

⇒ 这是一处**工具版本差异**，不是行为差异。后续引用 W27 §2 流程时不必假定必须用 v9。

## D3 · 「覆盖官方可见标签会真的渲染」需要细化 `[本卡新增观测，非否定 W40]`

`[转引]` 任务卡 §3 与 `LEAD_VERDICT_CSF_live.md §4.2`（W40 E 臂）：覆盖 `GUI:SinglePlayer` → 主菜单第一按钮渲染我方文本。本卡对照臂 `[本次实测·截图]` **独立复现**（`crop_w44_ctrl_main_menu_content2x.png` 第一按钮显示 `W44_C_LINE_CSF_DE…`）。

但本卡在**同一份**诊断 CSF 里还覆盖了 `DESC:SOV1`（官方苏联战役简介标签，原值「蘇聯戰役 - 毀天滅地大行軍」），结果 `[本次实测·截图]`：

- 战役菜单截图与主链臂 **SHA-256 完全相同**（`0bdcfd8c…`），徽章下仍是「點選蘇聯圖示以開始蘇聯戰役。」，**没有**渲染我方文本。

⇒ **口径细化建议**：不能把「覆盖官方可见标签」外推成「任何官方标签都能改它名义上对应的可见文案」。`GUI:SinglePlayer` 这类按钮标签确实驱动渲染；`DESC:SOV1` 在本卡的战役菜单这一屏**不**驱动徽章下短句（该短句另有来源，见 `UNKNOWNS.md U1`）。这与 W40 §4.2 的「E 臂是覆盖官方标签，不能冒充追加标签能显示」并不矛盾，是补了一层限定。

## D4 · Q3 与 W27 的差异：不再是 D3 诊断变体 `[本卡推进，非否定]`

`[转引]` W27 §5 的 Q3 是在 **D3 诊断变体**（`[SOV1] Scenario=ECH02.MAP`，直接进 A2）下成立。本卡 `[本次实测]` 在 **v12 包 + `--mapselmd` 管线**下复验，且 K2 **刻意不重新应用 D2 劫持**（读档不经过徽章入口），得到 `scen_filename=ECH02.MAP` / frame 283→396 / 局内 Esc 菜单 6/6 / 雪地图截图 / 存档副本哈希不变。

⇒ 结论作用域比 W27 更宽（不再依赖 D3 变体），但**仍**带「K1 进图借 `[SOV1]` 官方徽章」的限定；**不得**外推成「追加战役 `RA2F1` 从菜单可达」。这与 `LEAD_VERDICT_Q2_CLOSED.md §1.1` 的防外推要求一致。

## D5 · `scen_stage_idx=8` 口径：沿用 `[转引]`，不升格 `[与签发一致]`

`[转引]` `LEAD_VERDICT_Q2_CLOSED.md §3` 已把「引擎选中了第 8 阶段」降回 `[转引]`（非符号级证明），并修正了下标差一格的问题。本卡 K1/K2 均读到 `scen_stage_idx=8`（`[Scen+0x35A0]`），`[本次实测]` 仅记录该数值，**不**据此宣称引擎选中了某阶段。口径一致，无异议。

## D6 · `frame_delta=78` vs W39 的 `79` `[采样窗口差异，非矛盾]`

`[本次实测]` 本卡 `A2_confirmed frame_t1=53 → frame_t2=131`，`frame_delta=78` / 2.5 s ≈ 31.2 计数/s；`[转引]` W39 为 `44→123, Δ79/2.5s ≈31.6/s`。两者都是 32 ms 定拍（31.25/s）下的采样，差值 1 个计数来自采样时刻，不是行为差异。本卡**不**把 78 写成「帧速」也不与 W39 对齐数字。

## D7 · `K2_load_selected=null` 与 W27 §5 同型 `[如实照录]`

`[本次实测]` 按名字匹配存档列表项未命中（读到 `玩qsave` / `[]` / `[蘇聯 01 - 時空轉移]`…），依赖高亮首槽完成读档；`[转引]` W27 §5「`Q3_load_selected=null` … 实际是该存档已是高亮首槽」。两卡同型，本卡**未**修复该能力，见 `UNKNOWNS.md U3`。

## D8 · 本卡自身的三个驱动缺陷（**照录，不掩盖**） `[本次实测]`

| # | 缺陷 | 影响 | 处置 |
|---|---|---|---|
| D8-1 | K1 的 `w44_common.heal()` 初版把 `ra2forge_install.json` 列入还原集合，用 PREP 时的 **v0.3 旧清单**覆盖了 v12 安装记录 | 约 50 s 窗口内 `verify` 会失败；**不影响** K1 真机判定本身 | 从 `install.ndjson` 逐字节恢复 v12 清单 `ea34bada…`，`verify` exit 0、seal 完好（`out/repair.ndjson`）；修 `heal()` 永不再碰安装记录 |
| D8-2 | `w44_phase_uninstall.py` 初版把 `sandbox_pre.json`（**v0.3 已安装态**）当还原基线，把自己的结果判为 `ok=false` | 自证脚本误判；**卸载本身 exit 0、verify 0、三条硬判据全过** | 构造正确基线 `baseline_clean/`（只卸 v0.3），`w44_phase_restore_proof.py` 得 `IDENTICAL_TREE=True`；修脚本判据，把该 diff 标为信息项 |
| D8-3 | `w44_finalize.py` 的 `finally` 防御式还锁误写 `C.LOCK`（应为 `L.LOCK`），抛 `AttributeError` | 无实质影响：主流程 `lock_restore_lead()` 已成功，锁最终 `owner=lead` | 已修脚本；`out/final.ndjson` 保留 `lock_restore_error` 原始记录 |

⇒ 三者都是**驱动/自证脚本缺陷，不是游戏行为**；均已在 `out/*.ndjson` 留痕并在 `E2E_RESULT.md §5` 逐条写明。下游引用本卡数据时须知道存在 `repair.ndjson` 与 `restore_proof.ndjson` 这两个「修正/重做」记录。

## D9 · 真目录零改动数字与上游一致 `[无异议]`

`[本次实测]` PRE/POST 均 647 文件 / 1,989,215,270 B / 277 地图类，`IDENTICAL_TREE=True`；`RA2MD.INI=c91c6a47…`、`gamemd.exe=73201cc0…`、`ddraw.dll=85e0f7d5…`、`ra2forge_install.json=fe3bdf62…` 四项 PRE=POST 全对，与任务卡 §4 基线、`W27 §1`、`W39 §7` 完全一致。

## D10 · v12 `--mapselmd` 产物与 W39（v11）逐字节相同 `[交叉验证，无异议]`

`[本次实测]` 本卡 v12 构建出的 `MAPSELMD.INI` = 6,108 B / `11cc1cac…`，与 `W39/LIVE_RESULT.md §3` 记录的 W35/v11 追加版完全一致（stage 名 `RA2F_ECH01_2004FB14` / `RA2F_ECH02_1E0DEBE8`、`[Nod] 8=/9=`）。`[本次读码]` W41 `APPLY.md §2` 已说明 `mapselmd.py` 自 v11 起 IDENTICAL；本卡在真机上端到端印证（S4 `A2_loaded`）。

## D11 · 官方 CSF / MAPSELMD 容器归属：引用未独立重做 `[转引，非异议]`

`[本次实测]` 本卡复核 `W40/out/official_ra2md.csf` = 332,973 B / `1b90bb07…`（与 v12 内置 `RA2MD.OFFICIAL.CSF` 字节相同）、`MAPSELMD.OFFICIAL.INI` = 5,573 B / `074ccccd…`。但**未**亲自从 `langmd.mix` / `ra2md.mix` 重新提取（依 W41 EVIDENCE step1 `[转引]`）。任务卡 §1 的「两个容器别混」按签发事实引用，本卡未独立复验，见 `UNKNOWNS.md U11`。

---

## 汇总：本卡对上游结论的净影响

- **未推翻**：W39（MAPSELMD 推进）、W40（CSF 覆盖/值驱动渲染）、W27（Q1/Q3 及其作用域）、W32/菜单结构封死、W41（v12 回归 57/57）、真目录零改动基线 —— 全部复核一致。
- **推进 1 步**：Q3 存读档从「D3 诊断变体」推进到「v12 包 + MAPSELMD 管线 + 无 D2 的正式状态」（D4）。
- **补 1 层限定**：`DESC:SOV1` 被覆盖后战役菜单简介区不变，说明「覆盖官方标签能渲染」不能外推到所有官方标签/所有屏（D3）。
- **照录 3 个自身缺陷**（D8），供下游引用时避坑。
