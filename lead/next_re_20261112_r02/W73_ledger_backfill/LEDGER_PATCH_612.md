# LEDGER_PATCH_612 · W73（RE-N11 知识库归位）产出：待 Lead 审定后合入主台账的 §612 段

> 生成：2026-11-14T02:30+08:00｜执行者：GLM-5.3-Flash（W73 归位卡，只读本轮签发件与原始产物）
> 本文件**不是台账本体**，是可直接粘贴合入 `lead/GOAL_THREE_TARGETS_20261018.md`（末条 §611 之后）的补丁文本。主台账与 `PENDING_DECISIONS.md` 均有他人未提交改动，按纪律 §3.7 不覆盖，留归属方合入。
> 路径均相对仓库根 `D:\Project\ra2-campaign-forge\`。

---

## §612 · 本轮归并：C 线三关链真机贯通与重复性、菜单第三徽章真相（两条口径订正）、门控字节否定、EndOfGame 多关链机制、B 线三层论证（字节判据放弃→V2 修正→SAME_DISTRIBUTION）、`battlemd:inplace` 解冻与 v15 回归、产品路线裁决（2026-11-14）

- **性质与依据**：本节是 2026-11-13 22:25 – 2026-11-14 01:50 轮次的**入账归并**，由归位卡 W73（`lead/next_re_20261112_r02/W73_ledger_backfill/`）从 `lead/next_re_20261112_r02/REVIEW\` 各签发件回对原始产物后起草，供 Lead 审定。**本节起草者零真机、零启动、零 attach**（W73 只读文件；所有真机读数均转引自 W63/W70/W69/W72/W55b 等持锁卡并逐项核到其落盘 JSON/PROOF）。
- **分级口径**（本节统一，沿用 §610 风格收敛为五级）：`[已证]`=真机/采集实测且签发件已核；`[已证（静态）]`=磁盘字节/反汇编直接读数与穷举扫描计数；`[静态推断·较强]`=多数据点互证但未符号级/运行期定谳；`[转引]`=签发件采信的他人实测（本节已回对到落盘产物）；`[待运行验证]`=需要真机/动态才能闭合。
- **★ 本节两条订正（显式登记，不静默改写历史原文）**：
  1. **订正①**：W34 曾签发的「INI 数字键范围 0..255」**推翻**，实测硬上限 = **1..100**（详见 §612-D4）。
  2. **订正②**：Lead 2026-11-13 18:15 签发的「新增第 3 个战役徽章在产品上不支持 / 结构性封死」**推翻**，改为「引擎保留 3 个具名战役槽，零售资源模板只画了 2 个」——是**资源没画**，不是**引擎结构上不可能**（详见 §612-B1）。
- **条目标号**：A–G 七组 = `§612-A01`…`§612-G04`，覆盖矩阵见 §H，引用本节请用条目号。

### A · C 线：三关战役链真机贯通 + 重复性 + 卸载后官方战役功能级可用（W63 / W70）

- **§612-A01 [已证]** 路线 (a)（就地改写官方 `BATTLEMD.INI` 的 `[SOV1]`，`Scenario=RA2F_M1.MAP`，1 行改写 2,733→2,732 B）能把三关战役包送进游戏并**走完 M1→M2→M3 三关链**；M3 的 `EndOfGame=yes` 正确终止：`outcome=FULL_CHAIN_M1_M2_M3`、`ok=true`、M3 `advance=false`/`end_of_game=1`/`no_fourth_start=true`，点「繼續戰役」后走 `CREDITSMD.TXT` 片尾字幕、无第 4 关。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W63.md`；原始产物 `lead/next_re_20261112_r02/W63_route_a_e2e/out/TRIP_RESULT.json`。
- **§612-A02 [已证]** 字段轨迹（`0x125C` 为 `Start_Scenario` 实参，主锚）：`Scen+0x125C` 走 `RA2F_M1.MAP→RA2F_M2.MAP→RA2F_M3.MAP` 后**冻结在 M3**（47 samples/71 s）；`Scen+0x35A0`(WORD) `0→8→9` 单调递增；`Scen+0x34AC`(EndOfGame) `0→0→1`（M3 入口置位）；`MSG:UnableMapSelect` 全程 **0 次**。签发件同上 §2；原始产物同上 `trajectory` 逐阶段快照（7 个）。
- **§612-A03 [已证]** **重复性成立（3 趟一致）**：同一构建、同一包（11/11 文件 SHA 一致）在 3 趟中逐项一致通过（W63 trip1 + W70 trip2/trip3；W70 自身只计 2 趟、把 trip1 标 [转引]，该口径正确）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W70.md` §1-T1；原始产物 `lead/next_re_20261112_r02/W70_c_repeatability/out/TRIP_trip2.json`、`TRIP_trip3.json`（均 `ok=true`/`FULL_CHAIN_M1_M2_M3`，stage 0/8/9 同构）+ trip1 转引自 `W63_route_a_e2e/out/TRIP_RESULT.json`。
- **§612-A04 [已证]** **卸载后官方战役功能级可用**（W63 没做的一步）：装包(inplace)→卸载→逐字节还原→**重启游戏**→走官方苏联战役：`Scen+0x125C=SOV01UMD.MAP`（官方图名）、`frame=32` 进局、`scen_next=GDI2A.map`（官方关的 NextScenario，独立旁证）、全程 0 次 `MSG:UnableMapSelect`。`BATTLEMD.INI` 还原 2,733 B / SHA `7e40691a…` == 清单 `original_sha256` == 官方样板 == 真目录 PRE/POST。签发件同上 §1-T2；原始产物 `lead/next_re_20261112_r02/W70_c_repeatability/REAL_DIR_PROOF.txt`、`W63_route_a_e2e/REAL_DIR_PROOF.txt`。
- **§612-A05 [转引]** 收尾纪律自证：真目录 `ra2youli` 全程零写入（647 文件 / 1,989,215,270 B，`IDENTICAL_TREE=True`，added/removed/changed/mtime_diff 全 0，5 锚哈希 PRE==POST，`gamemd.exe` 基线 `73201cc0…` 不变）；沙箱逐字节还原并清理；游戏自生成 `RA2F_M1/M2/M3.sav` 三份存档（逐关进局旁证）已清并在还原自证体现。原始产物即上两条 `REAL_DIR_PROOF.txt`。
- **边界（照签发件照登，防外溢）**：不得写「三方战役包通用可通关」（1 包/3 关/1 台机/1 镜像）；不得写「官方战役不受影响」（装包态 `[SOV1]` 被占用，`.bak` 仅保证可还原）；未跑 `SkipMapSelect=yes` 分支、未做两包共存、官方全战役通关未验（`LEAD_VERIFY_W70.md` §3）。

### B · C 线：菜单第三徽章的真相（W58 / Lead CHECK / W64b / W61）

- **§612-B1 [已证（静态）] ⚠订正②** Lead 18:15 签发的「产品上不支持 / 结构性封死」**不成立**。两实现两路径独立收敛：**引擎有 3 个具名战役槽**（`1770=all1`、`1772=sov1`、**`1771=tut1`**），WndProc `0x52EC00` 认得 `0x6EB`(1771)（立即数 8 次，与 1770×7/1772×7 形态对等，含 `0x52EEA8 mov dword ptr [0xA8F7A8],0x6EB`）；零售 `RT_DIALOG 148`（664 B，`cDlgItems=13`，解析至末尾 `trailing=0`）**只画 2 个徽章 Static（1770/1772），无 1771**。⇒ **不是「引擎结构上不可能」，是「资源没画」**。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W58.md`、`REVIEW/LEAD_CHECK_menu_3slot.md`；原始产物 `lead/next_re_20261112_r02/W58_menu_review/EVIDENCE/07_third_slot.stdout.txt`、`01_resources.stdout.txt`、`EVIDENCE/rt_dialog_148.bin`。
- **§612-B2 [已证（静态）]** 具名战役槽**固定 3 个**：`all1/sov1/tut1` 全镜像字符串各 **1** 次（.data `0x825CA0/98/90`），`all2/sov2/tut2` 全 **0** 次 ⇒ **第 3 个有现成槽（补资源即可）；第 4 个才需要改代码**（新增槽、比较链、查表项、资源项）。签发件 `LEAD_VERIFY_W58.md` §2（A20 收窄）；原始产物 `W58_menu_review/EVIDENCE/14_strings_census.stdout.txt`（occurrences=1/1/1，0/0/0）。
- **§612-B3 [已证（静态）]** **第三徽章的图资源不存在**：全 MIX 递归 **5,630 个嵌套容器 / 1,168,759 个 CRC id**，唯一带 campaign 名的美术是 `CAMPAIGN.PCX`（640×480，`ra2.mix/A8548FD9`，76,884 B）；无任何 `TUT*/BOOT*/BADGE*/EMBLEM*`。第三徽章像素**不存在** ⇒ 路线 (c) 代价升级为「改 exe 资源 + 重绘菜单背景美术 + 自建 tut1 战役数据」。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_RULING_C_line_route_a_first.md` §5（采信 W61）；原始产物 `lead/next_re_20261112_r02/W61_third_badge_route/EVIDENCE/mix_recursive_stdout.txt`（TOTAL 1168759/5630、CAMPAIGN.PCX 命中行）。
- **§612-B4 [已证（静态）]** 官方 vanilla `BATTLE.INI`（`ra2.mix` 嵌套 `LOCAL.MIX` id `0xA8548FD9` 内，4,054 B / SHA `a5752a8d…`）**含 `[Battles] 1=TUT1` + `[TUT1] CD=0 / Scenario=trn01t.MAP / Description=DESC:TUT1`**，但 **YR 不加载**：`gamemd.exe` 只有 `"BATTLEMD*.INI"`@`0x4261A8` 与 `"BATTLEMD.INI"`@`0x426198`，`"BATTLE.INI"` 字符串 **0 命中** ⇒ **死数据**。官方 tutorial **地图**（1,003 候选名 × 13,007 CRC id 成员测试 0 命中）与 **MAPSELMD 阶段表**（官方 5,573 B 20 段全为 ALL01..07/Sov01..07）均**不存在**。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W64B.md`；原始产物 `lead/next_re_20261112_r02/W64_bootcamp_inventory/EVIDENCE/S5_exe_strings_stdout.txt`、`EVIDENCE/extracted/MIX_ra2_LOCAL_MIX_BATTLE.INI`、`S2_q2_stdout.txt`、`S4_q4_stdout.txt`。
- **§612-B5 [转引·待运行验证]** 唯一残差（W58 自留 d 类）：`0x46CC90` 查表结果**是否被上层用常量 2 截断**导致 `tut1` 分支「代码可达、数据不可达」未定谳；现措辞 =「引擎代码保留 3 个具名战役槽；第 3 槽能否运行期真正生效，取决于上层是否截断查表结果——未定谳」。签发件 `LEAD_VERIFY_W58.md` §3；原始产物 `W58_menu_review/EVIDENCE/09_const2_region.stdout.txt`（未闭合，维持登记）。
- **§612-B6 [转引]** 方法论教训（W64b）：W61 当年 `q2_scan.py` 跳过 `size>2,000,000` 条目，恰好跳过 33 MB 的 `LOCAL.MIX` ⇒ 「过滤条件会吃掉证据」。今后凡全量扫描必须写明过滤条件并单列因过滤跳过的候选。签发件 `LEAD_VERIFY_W64B.md` §2/§4。

### C · C 线：门控字节 `0xA8F7AD`（W57 双实例 + Lead CHECK）

- **§612-C1 [已证（静态）]** **有边界的否定**：本镜像静态代码中 `.data` 字节 `0xA8F7AD` **没有任何静态写入者**。覆盖矩阵：线性指令边界 1,394,120 条（99.9984%，66 未覆盖字节 anchored 复核）；内存写操作数 **135,330**（绝对 18,705 / `[reg+disp]` 116,625）；`rep stos/movs` 3,268；**37 条门控页绝对写**（disp∈`0xA8F700–0xA8F7FF`）逐条核 `[disp,disp+w−1]` → **0 覆盖**；全字节 anchored 超集 **4,005,210** 次解码 → `DETERMINATE gate hits: 0`。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W57.md`；原始产物 `lead/next_re_20261112_r02/W57_gate_writer_adjudication/EVIDENCE/w57b_layer2_stdout.txt`（census 行 mem_write_ops=135330 absolute=18705 regbase=116625 absolute_in_gate_page=37）、`w57b_probe_gatepage_stdout.txt`（P1: 37）、`w57_prior_regbase_stdout.txt`（anchored decodes 4005210）、`candidates_classified.tsv`（740 rows）、`GATE_WRITER_SCAN.md`/`GATE_WRITER_SCAN_W57B.md`（双实例独立同结论）。
- **§612-C2 [已证（静态）]** **唯一以 gate 为操作数的静态指令 = VA `0x52F00B` 的 `A0 AD F7 A8 00` 读**（`mov al, byte ptr [0xA8F7AD]`；精确 LE32 全场 1 次@FOFF `0x12F00C`；RVA/页内相对形式 0）。签发件 `REVIEW/LEAD_CHECK_gate_byte.md` §1/§2；原始产物 `W57_gate_writer_adjudication/EVIDENCE/w57_classify_stdout.txt:306`（`cat=read`）。
- **§612-C3 [已证（静态）]** 该门控**只控制 DEBUG LISTBOX 是否被填充，与徽章数量无关**（W58 销项；Lead 原 `[待复核]` 已闭合）。签发件 `LEAD_VERIFY_W58.md` §1 末行；原始产物 `W58_menu_review/EVIDENCE/04_gate.stdout.txt`。
- **§612-C4 [已证（静态）]** 未覆盖面必须随条携带（否则即外推）：基址相对写的运行期取值、间接跳转表、自修改代码、外部模块（`ddraw.dll`）、`.detour` 节、运行期 `WriteProcessMemory` 均不在「静态写入者」定义内；「无静态写入者」**≠**「零售态运行期恒 0」（若把运行期写者计入，结论应读作「③ 无法判定」——定义域问题）。该地址在 `.data` BSS（virtual-only），文件内无初值。签发件 `LEAD_VERIFY_W57.md` §1 三条限定、`LEAD_CHECK_gate_byte.md` §2 限定 1–2；原始产物同 §612-C1。
- **§612-C5 [转引]** W56 补正：其 `WRITE_MN` 名单漏 x87/SSE 存储（`fstp qword`/`movups`/`movntps` 被误标 READ）⇒ W56 的「740 候选 211 write」分类表**不可再直接引用**，须用 W57/W57b 补正版（补正后结论不变，仍 0 覆盖）。签发件 `LEAD_VERIFY_W57.md` §4；原始产物 `W57_gate_writer_adjudication/EVIDENCE/w57_classify_stdout.txt`（补正版分类：write=211/read=379/immediate=4/address-taken=74/false-positive=72）。
- **§612-C6 [裁决登记]** 「打开隐藏调试战役列表」路线**关闭**：静态无可触及入口（无写入者）+ 门控与徽章数无关。签发件 `LEAD_VERIFY_W57.md` §5。

### D · C 线：EndOfGame 与多关链机制（W59 静态 + W63 真机闭环）

- **§612-D1 [已证（静态）]** `EndOfGame` 是**终止闸**而非推进开关：`[Basic] EndOfGame` 加载时写入 `[Scen+0x34AC]`(BYTE)（`0x68A11F`）；`0x6859BF` 读、`0x6859C7` `je 0x685A10` 仅在 `==0` 时进推进分支；`!=0` → `0x6859C9` 取 BattleIdx → `0x5BF260` → `0x6859EE call 0x4C3E30`（CREDITSMD.TXT 结尾）→ `ret`，**到不了 `Start_Scenario`**。多关链写法必须 M1/M2=`no`、末关=`yes`。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W59.md` §2-①；原始产物 `lead/next_re_20261112_r02/W59_endofgame_chain/ENDOFGAME_CHAIN.md`、`EVIDENCE/w59_static.stdout.txt`（20/20 断言）。**真机闭环 [已证]**：W63 三张截图 + `TRIP_RESULT.json` 的 M3 `end_of_game=1`/片尾截图与该静态路径精确对上（`LEAD_VERIFY_W63.md` §3）。
- **§612-D2 [已证（静态）]** 真正驱动 **>2 关链**的是 **`MAPSELMD.INI` 阶段表**：`0x5CEEF0` 载入阶段向量（`DynamicVectorClass`，`+0x4` 数组/`+0x10` 计数，16 位索引 `and eax,0xffff`，越界→NULL→`Invalid stage!`→`MSG:UnableMapSelect`）→ `stage_get_by_index([Scen+0x35A0])` → 选中子阶段 `Scenario=` 经 `0x686700` 写 `[Scen+0x125C]` → `0x685C54 call 0x683AB0`（Start_Scenario）；`NextScenario` 只是 `skip_path_match` 匹配过滤器，`[Battles]` 只提供常量 `BattleIdx`。签发件 `LEAD_VERIFY_W59.md` §2-②③；原始产物 `W59_endofgame_chain/EVIDENCE/w59_static.stdout.txt:60`（xref=2）、`w59_detail3.stdout.txt`（0x686700 写入器、0x5AE0A7/0x5AE1ED 两 call 点）。
- **§612-D3 [已证（静态）]** `Scen*`=`*(DWORD*)0xA8B230`；`+0x35A0` 为 **WORD** 阶段索引，推进写点 `0x5AE0B8`（skip 路径）/`0x5AE1FA`（交互路径），值来自 `call 0x5CF830`。签发件 `LEAD_VERIFY_W59.md` §2/§5；原始产物 `w59_static.stdout.txt`（`66 89 83 a0 35 00 00` 双点，Lead 逐字节复算吻合）。
- **§612-D4 [已证（静态）] ⚠订正①** **INI 数字键硬上限 = 100**：`0x5CF04F` `83 ff 64`（`cmp edi,0x64`，循环 A）与 `0x5CF367` `83 fd 64`（`cmp ebp,0x64`，循环 B）双点。**推翻 W34 曾签发的「0..255」**；W34 原文不追溯改写，但今后引用必须写「实测 1..100（`cmp reg,0x64` 两处）」。签发件 `LEAD_VERIFY_W59.md` §2-④；原始产物 `W59_endofgame_chain/EVIDENCE/w59_static.stdout.txt:5287/:5843-5844`（[BOUND] 全量枚举仅此两条 `cmp reg,0x64`）。
- **§612-D5 [静态推断·较强]** `Scen+0x35A0` 的经验语义 = **「推进到当前关时所消费的那个阶段记录的键」，不是当前关序号**：M1 里 0（`Scenario=` 直进，不经阶段表）、M2 里 8（键 8=M1 的阶段记录推它进来）、M3 里 9（键 9=M2 的记录）；键 10（M3 自己的记录）全程未被消费。3 数据点 + 表结构互证，**未排除偶合**（如「最后一个被解析的键」）。**判据影响：判断「进了第几关」必须用 `+0x125C`（图名），不得把 `+0x35A0` 当当前关序号**；N 关链需 N 个阶段记录（第 1 关不需要），末关记录不被消费但必须存在且格式合法。签发件 `LEAD_VERIFY_W63.md` §8；原始产物 `W63_route_a_e2e/out/TRIP_RESULT.json`（trajectory 7 快照）+ `W63_route_a_e2e/out/MAPSELMD.INI.variant_from1`（键 8/9/10）。
- **§612-D6 [转引]** 阶段键「从 1 连续」口径获正向实测：W63 主变体键 1..10 连续一次成功；W34 当年 `2=` 起始属「可工作的巧合（或引擎容忍）」，因果未定谳、**不写成必修项**（W59 原 U-2 维持开放）。签发件 `LEAD_VERIFY_W63.md` §4/`LEAD_VERIFY_W59.md` §3-2。

### E · B 线：三层论证（W55b → W65 → W68b → W69 / W72）

- **§612-E1 [已证]** **存档字节等价判据已放弃**：`.SAV` 是 **OLE2/MS-CFB**（15 个具名 stream）；同臂（A）、同冻结帧 2408、同构建两次运行，`CONTENTS` 流差异 **1,339,784 B**（N_A）vs **1,316,737 B**（N_B）、`N_stable=false`；Lead 用独立 stdlib CFB 解析器核算：1,381,318 vs 1,377,434 B、2697 vs 2690 块（512 B）、**跨文件相同块数 = 0**，与 N_A 完全一致。⇒ W45 规格判据 `D>N` **数学失效**（D 与 N 同量级且不可稳定），verdict=**仍不可判**——不是采集没做够（三条硬前置全达成）。另发现第二族非确定源：变长 `Scenario Description`（32–38 B）与 `\x05SummaryInformation`（380–388 B），W55b **未事后加白名单**（处置正确）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W55B.md`；原始产物 `lead/next_re_20261112_r02/W55b_equivalence_rerun/out/analysis.json`（N_A_arm=1339784、N_B_arm=1316737、N_stable=false、verdict=仍不可判）、`out/CFB_COMPARE_TABLE.md`。
- **§612-E2 [已证]** **判据语义缺陷（已修）**：旧 V1 离散字段按「值→**计数**」多重集比较 ⇒ **只要两臂行数不等（=采样时长不同）必判 mismatch**，与分布无关——测的是采样时长不是行为。代数证明（定理 1）+ 两反例实跑复现（反例 A：同分布仅行数不同→误判 `SHIFT_DETECTED`；反例 B：真差异同行数→能判）+ 对照组全同。修正 = **V2**（离散改**占比向量+TVD+置换检验**；`n_min/N_max/alpha/k_ratio/D_floor/perm_iters/seed/theta_ui/qs` 及连续量算法 **10 常量逐字未动**；规格 FROZEN `00:33:05` 先于实现）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W68B.md`；原始产物 `lead/next_re_20261112_r02/W68_criterion_discrete_fix/CRITERIA_SPEC_V2.md`、`EVIDENCE/W68b_snapshot/`（权威副本：`DEFECT_PROOF.md`、`ce_A/ce_B/ce_C` result.json、`tool_b_stats_v2.py` sha `B419959A…`）、`EVIDENCE/recompute_v2_real_compare.json`（诊断性重算，非正式判定）。
- **§612-E3 [已证]** **V2 判据正式判定（重新采集，非事后重算）——append 形态 `SAME_DISTRIBUTION`/`within_noise_band`**：`D_ks=0.0000488782 ≤ max(N_ks=0.0004928496, D_floor=0.05)`、`p=1.000000`、`J_ui=1.0`、`n_a=20459/n_b=20451`（每趟约 10,200 采样点 × 4 趟，四趟 ok=true/errors=[]、两臂同图 `SOV01UMD.MAP`）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W69.md`；原始产物 `lead/next_re_20261112_r02/W69_bline_v2_collect/out/b_compare_v2.json`（schema B-W68B-V2-1，工具 sha `B419959A…`）。
- **§612-E4 [已证]** **inplace 形态 `SAME_DISTRIBUTION`/`within_noise_band`**（补 W69 只测 append 的缺口）：`D_ks=0.00039292 ≤ max(N_ks=0.00016744, D_floor=0.05)`、`p=0.9235382`、`n_a=20627/n_b=20587`、`delta_Q=0.0`、`discrete_shifted=[]`；INI diff 仅 1 行（`SOV01umd.MAP→SOV01UMD.MAP` 大小写改写，前后均 2,733 B/146 行/145 CRLF，sha `7e40691a…→919a50b2…`）——大小写改写是**为保住自变量的必要设计**（字节相同会走 `ADOPT`/`IDEMPOTENT_REPLAY` 零写路径，自变量消失）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_VERIFY_W72.md`；原始产物 `lead/next_re_20261112_r02/W72_inplace_noninterference/out/b_compare_v2.json`。
- **§612-E5 [已证]** **C 判据（安装期零越界写入）PASS**：合成用例（W62）+ 三张真实快照（W65/W69/W72）；W72 口径 `W⊆D`、`out_of_scope=[]`、`protected_all_equal=true`、`restore.equal=true`、C-1..C-6 全 true、`BATTLEMD.INI` 分类=`DECLARED-REWRITE`（非越界）、`.bak` sha == official。签发件 `LEAD_VERIFY_W69.md` §3、`LEAD_VERIFY_W72.md` §2；原始产物 `W69_bline_v2_collect/out/`、`W72_inplace_noninterference/out/`（c-audit JSON）。
- **§612-E6 [口径裁定]** **正确主张（照写，不得外溢）**：「我方安装机制（append 与 inplace 两种形态）**安装期零越界写入，且未检出行为分布差异**——在上述已声明的判据、观测量与场景范围内」。**`SAME_DISTRIBUTION` 是「未检出」不是「已证明相同」；不得写「B 线等价性成立」「装包对游戏无影响」「行为等价」**。判别力全部来自连续量（帧时序）：五离散字段全单值 ⇒ `TVD≡0`/`p≡1`，不得拿「离散 0 差异」当强度；`N_disc` 只取 A 侧属未暴露风险。签发件 `LEAD_VERIFY_W69.md` §1/§4、`LEAD_VERIFY_W72.md` §1/§3。
- **§612-E7 [已证]** **关键收窄（两命题不得混用）**：W72 测的是「写了但**内容等价**」（大小写改写，引擎不加载差异）；「写了**不同内容**」的功能可用性由 **W63/W70** 证明（inplace 把 `[SOV1]` 指向 `RA2F_M1.MAP` 后三关链贯通 + 三趟一致）。合起来 =「inplace 写不同内容时功能可用（W63/W70）；inplace 改写官方文件本身不扰动行为分布（W72）」。**没有任何一卡**测过「inplace 写不同内容**之后**的行为分布」——该方法上无法同图对照。签发件 `LEAD_VERIFY_W72.md` §3；原始产物同 §612-E4 + §612-A01/A03。
- **§612-E8 [裁决登记]** W65 旧判定处置：**维持 `SHIFT_DETECTED`（reason=discrete_or_ui_mismatch），附注「触发项为采样时长伪差异」**，不改写历史（判据变更发生在采集之后，属事后分析，故正式判定必须用 V2 重采——已由 W69 兑现）。签发件 `LEAD_VERIFY_W68B.md` §3；原始产物 `W65_bline_live_collect/out/b_compare.json`（D_ks=0.0012858、SHIFT_DETECTED）。

### F · B 线：`battlemd:inplace` 能力（D5.2 解冻 + W60 v15）

- **§612-F1 [裁决登记]** **D5.2 解冻**：`battlemd.mode="inplace"` 从 `DEFERRED`（`BATTLEMD_INPLACE_REFUSED`/exit 25）转**实现**。主论据**不依赖**「菜单封死」前提（该前提当晚已被订正②推翻）：① 路线 (b) `BATTLEMD98.INI` 追加重 id 有跨文件重复 ID + MIX 回退翻盘 ⇒ 静默失效；② 路线 (a) 就地改写无重复 id 且 W27 D2/D3 已有真机进图证据。其余守卫（K1/K2/K4、seal、content-conflict、版本守卫、升级孤儿规则）**全部原语义不动**；解冻的是**能力不是结论**；D6 的「G3 不可达」自述前提随之收窄（非推翻 D6）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_RULING_D5_2_INPLACE_UNFREEZE.md`（含 §5 审计注记：前提被推翻但结论不受影响）。
- **§612-F2 [已证（离线）]** **v15 实现与回归**：**96/96 用例全过、835 断言 0 失败、exit 0**（继承 v13 88 例 + S4 8 例 + W60 S5 新 6 例）。签发件 `REVIEW/LEAD_RULING_C_line_route_a_first.md` §1；原始产物 `lead/next_re_20261112_r02/W60_battlemd_inplace/out/SUMMARY.txt`（cases:96 passed:96、assertions:835）、`out/regress_full.stdout.txt`。
- **§612-F3 [已证]** **改写件锚**：`BATTLEMD.INI` 2,733→**2,730 B**、1 行 diff（145 CRLF 保持）；`after_sha256=369592f06371a2e7…97c470`，W60 `hashes.json` 记 `after_matches_w27_D2_prefix=true`（与 W27 D2 `369592f06371a2e7` 前缀一致；签发件表述为「与 W27 D2 逐字节一致」）。原始产物 `W60_battlemd_inplace/out/BATTLEMD.INI.hashes.json`、`out/BATTLEMD.INI.before`/`.after`/`.diff.txt`。
- **§612-F4 [已证]** **新增 6 例（INPLACE1–6）全过**：`.bak` 生成与还原 SHA 相等（INPLACE1/2，签发件记「INPLACE2 已实测相等」）；手改 drift 检出 **exit 9**（INPLACE3d：`recorded 369592f0…, disk fa7ecbea…`）；重复孤儿备份 **`INPLACE_BACKUP_ORPHAN exit 34`**（INPLACE4b，写前拒绝）；**K2 仍硬拒绝 `RESOLVE_COUPLING_REFUSED exit 26`**（INPLACE5c：csf×battlemd 强耦合，`install_write_set=[]`、零字节写入，K2 未被 W60 削弱）；路线 (b) append 包**不被误当 inplace**（INPLACE6e：manifest 无 `inplace_rewrite` 块）。原始产物 `W60_battlemd_inplace/out/INPLACE1.log`…`INPLACE6.log`、`SUMMARY.txt:99-104`。
- **§612-F5 [转引]** 能力边界（SUMMARY 自注，必须随条携带）：回归绿只证**文件层** plan/guard/integration 行为；真机验收当时未做（后由 W63/W70 兑现），版本守卫为 opt-in。原始产物 `W60_battlemd_inplace/out/SUMMARY.txt:108`。

### G · 产品路线裁决（C 线）

- **§612-G1 [裁决登记]** **真机先走路线 (a)**：① 不动 `gamemd.exe`（全项目基线不变式 `73201cc0…` 是 A/B 线所有对照的锚）；② 可逆且已有先例（W27 D2/D3 进图证据 + `.bak`/`original_sha256` 逐字节还原保证）；③ 真机风险最低（失败只影响沙箱 INI）。事后兑现：W63/W70 三关链贯通（§612-A01–A04）。签发件 `lead/next_re_20261112_r02/REVIEW/LEAD_RULING_C_line_route_a_first.md` §2。
- **§612-G2 [裁决登记]** **路线 (c) 不否决、压后**，前置门：**门 1** 徽章图来源解出（已由 W61 确认「不存在」→ 收敛为**门 3：第三徽章美术可造**，属资产创作非逆向）；**门 2** 明确接受「分发打过补丁的 `gamemd.exe`」并给版本守卫可用口径（如登记已知构建）。(c) 本轮只做离线补丁与静态验证（W61 副本补丁已打通：`cDlgItems` 13→14、回读 14 项 `trailing=0`）。签发件同上 §2/§5；原始产物 `W61_third_badge_route/EVIDENCE/patch_stdout.txt`、`verify_patch_stdout.txt`。
- **§612-G3 [裁决登记]** **「打开隐藏调试列表」路线关闭**（依据 §612-C1/C6）。签发件 `LEAD_RULING_C_line_route_a_first.md` §2-4、`LEAD_VERIFY_W57.md` §5。
- **§612-G4 [转引]** 产品叙事收获：`1771` 槽 = 零售版被砍的官方 **Boot Camp（训练营）战役入口**——控件 id/battle 名 `tut1`/音效 `BootCampSelect`/`STT:CampaignAnimTutorial`/`DESC:TUT1` 数据齐全（CSF 三件套实存），只是资源没画、YR 数据不全（§612-B3/B4）。签发件 `LEAD_RULING_C_line_route_a_first.md` §5；原始产物 `W61_third_badge_route/EVIDENCE/csf_check_stdout.txt`、`csf_values.txt`。

### H · 覆盖矩阵（结论 → 签发件 → 原始产物）

| 条目 | 签发件（REVIEW\） | 原始产物（原始落盘，W73 已回对） |
|---|---|---|
| §612-A01/A02 | `LEAD_VERIFY_W63.md` | `W63_route_a_e2e/out/TRIP_RESULT.json` |
| §612-A03 | `LEAD_VERIFY_W70.md` §1-T1 | `W70_c_repeatability/out/TRIP_trip2.json`、`TRIP_trip3.json`（trip1 转引 W63） |
| §612-A04 | `LEAD_VERIFY_W70.md` §1-T2 | `W70_c_repeatability/REAL_DIR_PROOF.txt`、`W63_route_a_e2e/REAL_DIR_PROOF.txt` |
| §612-A05 | 同上两条 PROOF 自证 | 同上（647 files / 1,989,215,270 B，IDENTICAL_TREE=True） |
| §612-B1 | `LEAD_VERIFY_W58.md`、`LEAD_CHECK_menu_3slot.md` | `W58_menu_review/EVIDENCE/07_third_slot.stdout.txt`、`01_resources.stdout.txt`、`rt_dialog_148.bin` |
| §612-B2 | `LEAD_VERIFY_W58.md` §2 | `W58_menu_review/EVIDENCE/14_strings_census.stdout.txt` |
| §612-B3 | `LEAD_RULING_C_line_route_a_first.md` §5 | `W61_third_badge_route/EVIDENCE/mix_recursive_stdout.txt` |
| §612-B4 | `LEAD_VERIFY_W64B.md` | `W64_bootcamp_inventory/EVIDENCE/S5_exe_strings_stdout.txt`、`extracted/MIX_ra2_LOCAL_MIX_BATTLE.INI`、`S2_q2_stdout.txt`、`S4_q4_stdout.txt` |
| §612-B5 | `LEAD_VERIFY_W58.md` §3 | `W58_menu_review/EVIDENCE/09_const2_region.stdout.txt` |
| §612-C1/C4/C5 | `LEAD_VERIFY_W57.md`、`LEAD_CHECK_gate_byte.md` | `W57_gate_writer_adjudication/EVIDENCE/w57b_layer2_stdout.txt`、`w57b_probe_gatepage_stdout.txt`、`w57_prior_regbase_stdout.txt`、`candidates_classified.tsv`、`GATE_WRITER_SCAN.md`(+_W57B) |
| §612-C2 | `LEAD_CHECK_gate_byte.md` | `W57_gate_writer_adjudication/EVIDENCE/w57_classify_stdout.txt`（:306 读指令） |
| §612-C3 | `LEAD_VERIFY_W58.md` §1 | `W58_menu_review/EVIDENCE/04_gate.stdout.txt` |
| §612-D1/D2/D3/D4 | `LEAD_VERIFY_W59.md` | `W59_endofgame_chain/ENDOFGAME_CHAIN.md`、`EVIDENCE/w59_static.stdout.txt`、`w59_detail*.stdout.txt` |
| §612-D1（真机闭环）/D5/D6 | `LEAD_VERIFY_W63.md` §3/§8/§4 | `W63_route_a_e2e/out/TRIP_RESULT.json`、`out/MAPSELMD.INI.variant_from1` |
| §612-E1 | `LEAD_VERIFY_W55B.md` | `W55b_equivalence_rerun/out/analysis.json`、`out/CFB_COMPARE_TABLE.md` |
| §612-E2 | `LEAD_VERIFY_W68B.md` | `W68_criterion_discrete_fix/CRITERIA_SPEC_V2.md`、`EVIDENCE/W68b_snapshot/`、`EVIDENCE/recompute_v2_real_compare.json` |
| §612-E3 | `LEAD_VERIFY_W69.md` | `W69_bline_v2_collect/out/b_compare_v2.json` |
| §612-E4/E7 | `LEAD_VERIFY_W72.md` | `W72_inplace_noninterference/out/b_compare_v2.json` |
| §612-E5 | `LEAD_VERIFY_W69.md` §3、`LEAD_VERIFY_W72.md` §2 | 两卡 `out/`（C-audit JSON） |
| §612-E8 | `LEAD_VERIFY_W68B.md` §3 | `W65_bline_live_collect/out/b_compare.json` |
| §612-F1 | `LEAD_RULING_D5_2_INPLACE_UNFREEZE.md` | （裁决件本体；依据 W37/W27 件为转引） |
| §612-F2/F3/F4/F5 | `LEAD_RULING_C_line_route_a_first.md` §1 | `W60_battlemd_inplace/out/SUMMARY.txt`、`out/BATTLEMD.INI.hashes.json`、`out/INPLACE1..6.log`、`out/regress_full.stdout.txt` |
| §612-G1–G4 | `LEAD_RULING_C_line_route_a_first.md` | `W61_third_badge_route/THIRD_BADGE_ROUTE.md`、`EVIDENCE/patch_stdout.txt`、`verify_patch_stdout.txt`、`csf_check_stdout.txt` |

### I · 应补进 `PENDING_DECISIONS.md` 的条目（本卡不改该文件，留归属方合入）

1. **ra2youli 旧 v0.3 包的处置**：现状 = 官方 `[SOV1]` 已被 v0.3 占用（装包态）；`PAUSE_STATE_20261113.md` §5 载明「卸载会改变 A 线基线且不可逆」；D5.2 裁决 §3 明示不涉及、W60 禁写 `ra2youli`。待裁：保留原状 / 卸载还原（A 线基线变化需重新锚定）/ 迁移到 v15+inplace 重装。依据：`LEAD_RULING_D5_2_INPLACE_UNFREEZE.md` §3。
2. **路线 (c) 是否接受分发打过补丁的 `gamemd.exe`**（门 2）+ **版本守卫口径**：改 exe 将打破全项目基线哈希 `73201cc0…`，与「未知构建拒绝」直接冲突；需裁决「登记已知构建」还是「一律拒绝」，并连带「第三徽章美术资产创作」是否立项（门 3）。依据：`LEAD_RULING_C_line_route_a_first.md` §2/§5、`LEAD_CHECK_menu_3slot.md` §4。
3. **D5.2 解冻的台账登记**（编号顺延）：D5.2 裁决 §4 自点名「`PENDING_DECISIONS.md` 需登记本条」；同处须注明与 D6 的关系（D6 判定逻辑不变，仅「不可达」适用范围收窄）。依据：`LEAD_RULING_D5_2_INPLACE_UNFREEZE.md` §4。

### J · 未验项与边界（承接，不补造）

- `0x46CC90` 查表截断问题（§612-B5）[待运行验证]；`+0x35A0` 语义仅 3 数据点（§612-D5）；`2=` 起始 vs `1=` 连续的因果未定谳（§612-D6）。
- W70 未覆盖：`SkipMapSelect=yes` 分支、两包共存、官方全战役通关（§612-A 边界）。
- W57 静态否定的覆盖边界（间接跳转/自修改/`ddraw.dll`/`.detour`/`WriteProcessMemory`，§612-C4）；W56 分类表不可直接引用（§612-C5）。
- B 线：离散侧退化、`N_disc` 单侧、「未检出≠已证明相同」（§612-E6）；「inplace 写不同内容后的行为分布」方法上不可问（§612-E7）。
- W63/W70 的 `+0x35A0` 语义与真机还原自证均已闭合；W59 原 U1（`0xA8E9A0` 语义）/U2（自动选支细节）**维持开放**。
- 本节起草者（W73）**未独立重算**仅转引的读数：W58 strings_census 之外的 W58 全套、W61 的 7/8/21 处 TUT1 命中明细（Q3）、W64b Q2 的 1,003×13,007 测试细节、W60 INPLACE1/2 的逐项断言明细——均按签发件+落盘产物对账，无数字改动。

- 本节**零真机、零采样代码执行、未改主台账、未改 PENDING_DECISIONS、未改 REVIEW\ 与任何 W 卡产物、未 commit、未 push**；W73 只写 `lead/next_re_20261112_r02/W73_ledger_backfill/`。

---
（§612 补丁文本结束。合入位置：`GOAL_THREE_TARGETS_20261018.md` 末条 §611 之后。）
