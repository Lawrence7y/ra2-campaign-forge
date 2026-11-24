# FINDINGS (in progress)

Card: W71 | Auditor: GLM-5.3-Flash | Target: LEAD_VERIFY_W63 主结论
被审计结论：就地改写官方 BATTLEMD.INI 的 [SOV1]，能把我方三关战役送进游戏并走完 M1→M2→M3；M3 的 EndOfGame=yes 正确终止，不再进第 4 关。

纪律声明：纯只读审计。I launched 0 / attached 0。未读活进程内存，未取 .game_instance.lock，未启动 gamemd.exe。

## Section 0 — 设置
- STARTED.txt / FINDINGS.md / EVIDENCE\ 已建立。

## Section 1 — 必查1「三关是否真三关」 `[本次实测]`
- `work\pkg\W63RouteA\` 内确有且仅有 3 张我方 `.MAP`：
  - `RA2F_M1.MAP` 4,520 B SHA256 前16 `EF7AFE54AB01078A`
  - `RA2F_M2.MAP` 4,406 B SHA256 前16 `2EC4912F2C571188`
  - `RA2F_M3.MAP` 4,411 B SHA256 前16 `6CBC21FF6D444695`
  三文件大小、哈希互不相同 ⇒ **不是同一张图改名**（文件层面成立；内容语义差异另见 enter 截图目视）。
- `out\TRIP_RESULT.json` trajectory 7 个阶段（非 6）：enter_M1/victory_M1/enter_M2/victory_M2/enter_M3/victory_M3/final_after_M3_continue；前 6 个快照 `scen_filename` = `RA2F_M1.MAP`→`RA2F_M2.MAP`→`RA2F_M3.MAP`，`scen_ptr` 恒 64273272（同一 ScenarioClass 实例），`stage_idx` 0→8→9，`eog` 0→0→1。与三文件对应关系成立。
- 旁证：E2E_RESULT §6/REAL_DIR_PROOF B 记录游戏自生成 `RA2F_M1/M2/M3.sav` 三份存档（已清理，无法直接复核，标 `[未核·已清理]`）。
- **判：成立**（待截图目视交叉确认 M2≠M3 画面）。

## Section 2 — 截图/哈希实测 `[本次实测]`
- `screen_victory_M2.png` 与 `screen_victory_M3.png`：均 246,905 B，SHA256 前16 同为 `99D3135C756D28CC` ⇒ **逐字节相同**。E2E_RESULT §3 与 DISAGREE D6 **已如实披露**（"静态结算模板，不作两次独立胜利的视觉证据"），故不算隐瞒，但该对截图对"M3 也通关"**零独立视觉证明力**，仅靠 run.ndjson 读数支撑（见 Section 5 核对）。
- enter 三图哈希互不相同：M1 `AB720E95`/1,422,147 B、M2 `E76F01CC`/1,158,398 B、M3 `75CBFE85`/1,158,260 B。M2 与 M3 字节数仅差 138 ⇒ 画面高度相似，需目视区分（待做）。
- `screen_final_after_M3_continue.png` 151,169 B `4309CCC7`，与 E2E_RESULT §3 登记一致。

## Section 3 — 收尾还原（部分核对） `[本次实测]`
- `out\pristine\BATTLEMD.INI` = 2,733 B SHA256 前16 `7E40691A3480B1E5` == REAL_DIR_PROOF/清单声称的 `original_sha256=7e40691a…` ✔（注意：该哈希是从 `out\pristine\` 副本算的；真目录现物是否等于它，由 real_pre/real_post 全树清单断言，见下）
- `out\real_pre.json` 与 `out\real_post.json` **逐字节相同**（1,21,332 B，SHA 同 `D36337E0`）⇒ 真目录含 mtime 零改动成立（该 JSON 本身含全树 SHA，相同即树相同）。
- **新疑点 W71-1**：`out\sandbox_pre.json` 与 `out\sandbox_post.json` 均为 121,381 B 但 SHA 不同（`55DB1D20` vs `F66F9E83`）。若两文件均为纯树清单，则与 REAL_DIR_PROOF B 的 `IDENTICAL_TREE=True` 矛盾；若 JSON 内嵌采集时间戳等元数据则无碍。→ 待 diff 落实。
- `work\pkg\W63RouteA\MAPSELMD.INI` == `out\MAPSELMD.INI.variant_from1`（均 6,410 B，SHA 同 `8064B783`）⇒ 实跑包确为主用变体 A ✔；variant_from2（`2=` 起始）`4B15F3AC` 未跑，与报告一致。
- `work\pkg\W63RouteA\BATTLEMD.INI` = 2,732 B `8FB51769` == 清单 `post_install_sha256` ✔。

## Section 4 — 收尾还原复核结论（必查5） `[本次实测]`
- `FINALIZE.json` `real_dir_anchors` 5 项：`equal:true` 且 pre/post 64 位哈希**程序化比对逐字符相同**（含 ra2forge_install.json）。并与 `real_pre.json`/`real_post.json` 条目交叉核对：RA2MD.INI / gamemd.exe / ddraw.dll / ra2forge_install.json / BATTLEMD.INI / BATTLEMD.INI.ra2forge.bak 六项 sha 与 mtime_ns 全同 ⇒ 真目录零改动成立。
- `FINALIZE.json` `battlemd_restore`：restored 2733 B sha `7e40691a…` == manifest_original == official_baseline == pristine == real_dir_pre/post，`sov1_scenario_gone=true`、`official_sov1_scenario_back=true`。
- `config_restore` 21 项构成：**20 项 `byte_identical:true` + `ra2forge_install.json.seal` 1 项 `{restored:true, absent_baseline:true}`（删除现存，非 byte_identical）**。E2E_RESULT §6 表述准确；**LEAD_VERIFY_W63 §7 表"21 个，逐个 byte_identical=True"与 FINALIZE.json 不符（夸大 1 项）→ 记 B 级 W71-B1**。
- `sandbox_pre.json` vs `sandbox_post.json`（各 647 条）：added=0 removed=0 sha256 差异=0，**除 mtime_ns 外零字段差异**。FINALIZE `sandbox_diff_after_extra_cleanup.mtime_diff` 列 20 个文件 == config_restore 20 项（还原写盘动 mtime，内容 sha 未变），`identical_tree:true` 是 sha 口径且 mtime_diff 已如实列出 ⇒ W71-1 疑点解除。注意 `sandbox_diff`（清理前）added 恰为 3 个 `.sav`，与"游戏自生成三份存档"叙述一致。
- **判：成立**（还原链完整、自洽，无造假痕迹）。

## Section 5 — MAPSELMD.INI.variant_from1 实读（必查7） `[本次实测]`
- `[Nod]` 段：`1=Sov01 … 7=Sov07`、`8=RA2F_RA2F_M1_3B52DC3A`、`9=RA2F_RA2F_M2_06228782`、`10=RA2F_RA2F_M3_1AE84EB9` ⇒ **键 1..10 连续**，无空洞、无 100 上限风险。
- 追加 3 个阶段段（行 266-296）：M1 段 `Scenario=RA2F_M1.MAP` 子项 `1=RA2F_RA2F_M2_…`；M2 段 `Scenario=RA2F_M2.MAP` 子项 `1=RA2F_RA2F_M3_…`；M3 段 `Scenario=RA2F_M3.MAP` **无子项数字键**（终关）。⇒ 追加阶段确实指向我方 3 张图，M1/M2/M3 一一对应。
- 变体 A 子项键 `1=`：与官方 Sov01..Sov07 段的官方惯例（子项键=下一阶段号，如 `[Sov01] 2=Sov02`）**不同**——官方数字键是 ClickMap 颜色索引语义（2 起）。这正是 U1/D1 登记的"1= vs 2="未定谳点；本卡只证变体 A 可用，未跑变体 B，报告口径诚实。
- **判：成立**（与 LEAD_VERIFY_W63 §4/E2E_RESULT §4 的描述一致）。

## Section 6 — run.ndjson 终核 `[本次实测]`
- 行数 **198** ✔（195 event + meta/meta_start/meta_end）。`UnableMapSelect` **0 次** ✔；`blocked/fatal/error` 0 ✔。
- 事件分布：`w59_point`×82（其中 `final_after_M3_continue_w59`×**47**）、`screen_state`×77、`screenshot`×10、`click`×5、`level_victory`×3、`level_advance`×2、`level_entered`×1、`trip_result`×1、`final_endofgame_observation`×1、`close_game`/`trip_cleanup`/`lock_released`/`meta_end` 各 1。
- 关键数值：pid **34668**、`WM_CLOSE(hwnd=331606)`→taskkill rc=0×2→residual 0；锁 `owner=w63` 23:37:11.796 → `owner=lead` 23:39:42.497；桌面预检 `enum_windows_total=392 / visible=20 / ImageGrab 2560×1440 / pass=true`。

## Section 7 — 必查2「advance 判据」 `[本次读码]`（work\tools\w63_run.py）
- **enter**：`want_fn in scen_filename`（大小写不敏感）且 `frame>30`（w63_run.py:127）→ `level_entered`。
- **advance**：点 Continue 后轮询，判据 = `0x125C` 变为**下一关图名**且 `frame>10`（w63_run.py:198），2.5 s 后复采确认并截图 → `level_advance`（:201-208）。**不是"点了 Continue 就算"**；超时/报错弹窗/进程退出都会 raise TripError 不返回。细节：`frame_advancing=(f2>f1)` 仅记录、不作为返回条件（:207）——判据比 enter 略松（>10 vs >30），但有 0x125C 名字 + stage idx 递增 + enter 截图三重佐证，实质成立。
- **victory**：`GUI:Continue` 控件可见（EnumChildWindows 枚举，:150-151）+ 2 s 后复读 frame 停滞确认（`frame_stalled` 仅记录），错误弹窗先行排除（:146）。
- **no_fourth_start**：`observe_final(timeout_s=70)`（:216）每 ~1.5 s 采样；`fourth` = 图名含 M4/MAP/RA2F 且不含 RA2F_M3 且不属于 EXPECTED 三名的采样（:239-244）；`no_fourth_start = (len(fourth)==0)`（:253）。
- **判：成立**（判据为状态机读数型，非"点击计数型"；附 W71-B2/B3 两个口径提示）。

## Section 8 — 必查4「截图与读数同一趟」 `[本次实测]`
- **10/10 截图 SHA-256 与 E2E_RESULT §3 登记表全部对上**（前16）：S0 `982CDE29`、S2 `C8901BD5`、after_badge `E2F37275`、enter_M1 `AB720E95`、victory_M1 `C4EA0B25`、enter_M2 `E76F01CC`、enter_M3 `75CBFE85`、victory_M2/M3 `99D3135C`（同）、final `4309CCC7`。
- 截图 mtime 与 run.ndjson `screenshot` 事件**秒级对齐**：enter_M1 23:37:48、victory_M1 23:37:56、enter_M2 23:38:02、victory_M2 23:38:10、enter_M3 23:38:16、victory_M3 23:38:23、final 23:39:36；全部落在锁窗口 23:37:11–23:39:42 内。trip_result 事件（23:39:36.695）与 TRIP_RESULT.json 内容一致。
- 中间态复算 ✔：`post_continue_M1_w59` 23:37:58 `fn=RA2F_M2.MAP stage=0 frame=0` → 23:38:00 `stage=8 frame=14`（先写名后写 stage，与 W59 静态链次序一致）；`post_continue_M2_w59` 23:38:12 `fn=RA2F_M3.MAP eog=1` ⇒ **M3 载入即置位 EndOfGame**（对应 `0x68A11F` 写点）。
- **判：成立**（无"别的趟截图充数"的迹象）。

## Section 9 — 必查3「M3 EndOfGame 真生效」+ 必查6「反证」 `[本次实测]`
- 47 采样（run.ndjson `final_after_M3_continue_w59`）23:38:25→23:39:35、跨度 70 s（观测器 `elapsed_s=71.38`）：`scen_filename` 唯一值 `RA2F_M3.MAP`、`frame` 唯一值 210、`eog` 唯一值 1、`stage` 唯一值 9；`fourth_scenario_candidates=[]`、`saw_settlement_or_menu=false`、无 `final_process_exited` 事件（进程全程存活）。
- **最终截图亲眼核验**：`screen_final_after_M3_continue.png`（1,51,169 B，SHA `4309ccc7…`）是**片尾职员表滚动字幕**（Assistant Coordinator / Production Assistants / Teleprompter Operator / Ultimatte Operator / Concept Artist…），**不是报错框、不是主菜单**。
- 与 W59 静态预测闭环：`0x6859BF mov al,[Scen+0x34AC]` → `0x6859C7 je`（==0 才推进）→ `!=0` 走 `0x6859C9 BattleIdx` → `0x6859EE call 0x4C3E30`（CREDITSMD.TXT）→ ret（LEAD_VERIFY_W59.md §2/ENDOFGAME_CHAIN.md §Q5）。真机行为（eog=1 进关即置位 + Continue 后进字幕、无第 4 图名）与该分支**精确对应**。
- UNKNOWNS U1-U12 / DISAGREE D1-D8 逐条评估：**无一条削弱签发句主体**——U1（1= vs 2= 因果）只影响"哪个子项键写法必需"，不影响"变体 A 走通了"；U2/+0x35A0 语义 Lead §8 自己标了 `[静态推断·较强]` 且未进签发句；U3（`scen_next`/`+0x04` 语义）未被用作判据；D6（结算屏同哈希）已自我设限不充当独立证据；D7（单趟无重复臂）与签发句 §6 的边界一致。
- **判：成立**（附 W71-B2 口径提示："不再进第 4 关"= 70 s 观测窗内实测，片尾播完后行为未观测）。

## Section 10 — 必查1 补充：目视三张 enter 图 `[本次实测]`
- `screen_enter_RA2F_M3.png`：我方小图——TEMPERATE 草地一小块 + 苏军建造场（吊爪+金顶）+ 特斯拉线圈 + 坦克 + 1 步兵，四周未探索黑雾，右下角「未探索之地形」。与 LEAD_VERIFY_W63 §3 描述相符。
- `screen_enter_RA2F_M2.png`：与 M3 **布局近同**（同建筑集，步兵站位微差，字节差 138）。⇒ "三关"的区分证据在 `0x125C` 文件名 + 三文件哈希/尺寸互异 + 3 份 `.sav`（已清理，`[未核·已清理]`），**画面本身几乎不能区分 M2/M3**——引用时勿写"画面明显不同"（E2E_RESULT §3 未这样写，无违例）。

---

## 分级发现（最终）

**A 级（推翻/削弱主结论）：0 条。**

**B 级（口径/证据链瑕疵，不推翻）：**
- `W71-B1 | REVIEW\LEAD_VERIFY_W63.md:72（§7 表）`｜原文「21 个，逐个 `byte_identical=True`（含那个 241 B 孤儿 `.bak`…）」｜与 `out\FINALIZE.json` `config_restore` 实况不符：21 项 = **20 项 `byte_identical:true` + 1 项 `ra2forge_install.json.seal` `{restored:true, absent_baseline:true}`（删除现存，非逐字节还原）**；`E2E_RESULT.md:144` 表述准确｜问题：Lead 验收小节转述夸大 1 项｜建议：改写为"20+1"口径（seal 基线本不存在，删除现存是正确处置，还原事实本身成立）。
- `W71-B2 | E2E_RESULT.md:26 / LEAD_VERIFY_W63.md:22`｜「71 秒 / 47 采样恒为 M3 → 不再进第 4 关」｜`observe_final` 观测窗 `timeout_s=70`（w63_run.py:216），"不再进第 4 关"实测语义是**70 s 窗口内未出现第 4 图名**；片尾播完后是否回主菜单/异常未观测（UNKNOWNS U4 已登记）｜建议：签发句引用时加"点 Continue 后 70 s 观测窗内"限定，或后续卡补一次片尾播完观测。
- `W71-B3 | work\tools\w63_run.py:223-225,253` `[本次读码]`｜`observe_final` 中进程中途退出（`final_process_exited`）会提前 break 且 `fourth` 为空 ⇒ `no_fourth_start` 仍为 True｜本趟未触发（无该事件、47 采样连续、frame 恒 210），不影响本趟结论｜建议：复用该判据时显式要求"进程存活覆盖全窗"作为 `no_fourth_start=True` 的前置条件。

**C 级（表述/引用小问题）：**
- `W71-C1 | REVIEW\LEAD_VERIFY_W63.md:51`｜「390 windows」｜run.ndjson `step0_desktop_precheck` 实测 `enum_windows_total=392`（E2E_RESULT §5 写 392 正确）｜转写漂移。
- `W71-C2 | 任务书路径`｜`REAL_DIR_PROOF.txt` 实际在 `W63_route_a_e2e\` 根目录，非 `out\` 下｜引用路径小偏差。
- `W71-C3 | TRIP_RESULT.json trajectory`｜7 个阶段快照（任务书称 6 个；末个 `final_after_M3_continue` 无完整 w59 字段）｜Lead §8 自身称 7 个，无违例，仅口径提示。
- `W71-C4 | out\screen_victory_M2.png / screen_victory_M3.png`｜两文件逐字节相同（246,905 B，SHA 前16 `99D3135C`）｜D6 已自曝并声明不作独立证据；提醒后续引用勿单独以该图证 M3 通关。
- `W71-C5 | work\tools\w63_run.py:51-53`｜`ERR_MARKERS` 含我方三图名（`RA2F_M1.MAP` 等）｜仅用于错误弹窗时内存标记搜索语境，不参与 enter/advance 判定；阅读者注意勿误读。

## 审计结论

**主结论成立**（在卡面声明范围内：本环境 / 本包 / MAPSELMD 变体 A / 单趟 / `SkipMapSelect=no` / 70 s 观测窗）。具体拆解：
1. 「三关」成立：三张 `.MAP` 哈希/尺寸互异、`0x125C` 依次为 RA2F_M1→M2→M3.MAP、三个 `level_advance/level_victory` 事件独立存在（`.sav` 旁证已清理未核）。
2. 「advance」判据是状态机读数型（下一关图名 + frame 推进），非"点了就算"，成立。
3. 「M3 EndOfGame 正确终止」成立：eog=1 进关即置位、47 采样/70 s 恒 M3、最终截图亲验为片尾职员表、与 W59 静态分支（`0x6859C7 je` / `0x4C3E30`）精确闭环。
4. 「收尾还原」成立：真目录 real_pre==real_post 逐字节（含 mtime）、BATTLEMD.INI 还原 SHA==清单 `original_sha256==7e40691a…`、沙箱 647 条 sha 零差异（mtime 动是还原写盘，已如实列 mtime_diff）。唯一瑕疵是 Lead §7 把 20+1 写成"21 个逐个 byte_identical"（W71-B1）。

**若我错了（主结论其实不成立），会看到但实际没有看到的反证**：
- 三关是假的：`trajectory` 中 `scen_filename` 重复同名 / pkg 只有 1 张 `.MAP` / 三图哈希相同 / MAPSELMD 阶段段缺失指向——实测全反。
- advance 造数：`level_advance` 前后 `0x125C` 未变名 / 无 `advance_frame_confirm_*` 事件——实测有且名字正确。
- EOG 终止是假的：47 采样出现 EXPECTED 外第 4 图名、frame 重置爬升、`final_process_exited` 后重启、final 截图是报错框/主菜单——实测全无，截图亲验为职员表。
- 截图充数：截图 SHA 与 §3 表不符、mtime 与 run.ndjson 时间线错位——实测 10/10 全中且秒级对齐。
- 还原造假：real_pre/real_post 不同、BATTLEMD.INI 现值 ≠ `7e40691a…`、FINALIZE 出现 `byte_identical:false`——实测全反。

纪律声明：I launched 0 / attached 0。全程未启动 gamemd.exe、未 attach、未读活进程内存、未取 `.game_instance.lock`；除本卡目录（STARTED/FINDINGS/HEARTBEAT/EVIDENCE）外零写入；git 未调用。
