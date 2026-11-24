你是 RA2 Campaign Forge 的**交叉一致性审计卡 W43**。任务：**以第三方视角审计本会话（run_id `NEXT_RE_20261112_R02`）全部签发文件与卡片产物之间的一致性，专门找互相矛盾、过度声明、以及"结论超出证据"的地方。**

工作目录：`D:\Project\ra2-campaign-forge`

## 为什么要你做
本项目贯穿一条纪律：**代理的自我总结不可信，必须回对原始证据**。本次已有多个实例：W25 自述全绿实为 36/39；W27 脚本 `chain_results.q2` 自述"未出现胜利/结算屏"实为假阴性（截图里「任務完成」清晰可见）；某卡把 `0x922B8CE7` 的来历解释错了但产物是对的。**现在要让一个不同的模型来挑 Lead 自己的判断。**

## 审计对象

### A. Lead 的签发文件（在 `lead\next_re_20261112_r02\REVIEW\`）
- `LEAD_VERDICT_map_start_root_cause.md`（关卡推进根因，W31+W33 双卡互证）
- `LEAD_VERDICT_campaign_menu_q1.md`（战役菜单结构性封死）
- `LEAD_W27_RAW_VERDICT.md`（W27 真机卡复核）
- `LEAD_W28_VERIFY.md`、`LEAD_W29_VERIFY.md`、`LEAD_W33_VERIFY.md`
- `LEAD_VERIFY_W34.md`、`LEAD_VERIFY_W36.md`、`LEAD_VERIFY_W37.md`
- `LEAD_FACT_map_error_label.md`

### B. 卡片产物（各自目录）
`W27_campaign_live\`、`W28_nextscenario_form\`、`W29_override_order\`、`W30_csf_capability\`、`W31_map_start_failure\`、`W32_campaign_menu_entries\`、`W33_nextscenario_dataflow\`、`W34_mapselmd\`、`W35_mapselmd_live\`、`W36_b_line_kickoff\`、`W37_official_id_borrow\`、`W38_version_guard_s1\`、`W39_mapselmd_live2\`（含 `LIVE_RESULT.md` / `out\*.ndjson`）

## 要专门查的 8 类问题

1. **结论冲突**：两个文件对同一事实给出不同说法。例：`MAPSELMD.INI` 的物理位置（文件偏移、长度、SHA-256、行数）在各处是否一致？`0xFBE0D09D` 的来历是否被某处当"事实"写了？
2. **过度声明**：把 `[静态推断]`/`[转引]` 写成 `[本次实测]`；把"离线回归全绿"写成"功能可用"；把"已收窄到某分支"写成"已定位根因"。
3. **数值不一致**：镜像/文件 SHA-256、字节数、模块数（11/13/14）、用例数（39/45/51）、地址（VA/RVA/FOFF）、`frame` 数值、标签数（5,211）等在多处是否一致。
4. **地址口径**：是否有把 RVA 当 VA（或反之）的地方？`.text` 内 `FOFF = VA − 0x400000` 这条是否被一致使用？
5. **未经证实的因果**：`LEAD_VERDICT_map_start_root_cause.md` 说"两卡互证"，请核对 W31 与 W33 的**判定链是否真的等价**，还是只是结论相同、路径不同、其中一卡的中间步骤有错但被另一卡掩盖。
6. **W39 的真机结论**：`run_outcome=A2_loaded` 与负对照 `error_dialog_GUI_OK` 是否足以支撑"MAPSELMD 登记是成功原因"？检查 `out\w39_skip_no.ndjson` 与 `out\w39_control_official.ndjson`，注意 `scen_stage_idx`、`scen_filename`、`frame` 的实际数值与报告描述是否一致（**报告里有个说法是 "frame 44→123（2.5s，Δ79，≈31.6/s）"，而 ndjson 里 `elapsed_s` 是 4.56 —— 请核对这是口径问题还是错误**）。
7. **已撤回/已降级的陈述是否还在某处活着**：例：「描述文本只影响显示不影响功能」（应已撤回）、「永久冻结/229 s」旧定性、「3.104e9 cyc/ms」单位错误、「LB_GETCOUNT=0 是破绽」（已被 W32 否证为零售设计）。
8. **纪律自证是否可信**：各卡声称"未写 ra2youli / 未改仓库"，`LEAD_W27_RAW_VERDICT.md` 与 `W35`/`W39` 都有 `IDENTICAL_TREE=True` 的自证；核对是否存在**自证方式本身不可靠**（例如 `all()` 遍历空集为真、只比对了文件数没比哈希）。

## 输出要求

- 每条问题给：**位置（file:line 或 file 段落）**、**问题类型**（1–8 之一）、**原文摘引**、**为什么是问题**、**建议处置**（改口径 / 补证据 / 撤回）
- 按**严重度**排序：`BLOCKER`（会误导工程决策）/ `MAJOR`（口径不实但方向对）/ `MINOR`（笔误）
- **不要重做反汇编**，不要启动游戏。你只做文本与产物的一致性核对；对代码级结论只核"引用是否自洽"，不核"代码是否真的如此"
- 若你发现 Lead 的判断有错，**直接说，不要客气**。这份审计的价值就在于挑错

## 交付（只写这个目录）
`lead\next_re_20261112_r02\W43_consistency_audit\`
- `AUDIT_REPORT.md`（按严重度排序的问题清单 + 每条的建议处置）
- `CONFLICT_TABLE.md`（同一事实在不同文件的取值对照表，标出不一致项）
- `UNKNOWNS.md`（你无法判断的部分，以及为什么）
