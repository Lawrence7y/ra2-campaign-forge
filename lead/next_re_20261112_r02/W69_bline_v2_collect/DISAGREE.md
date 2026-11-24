# W69 · `DISAGREE.md`（异议 / 与上游口径的偏差，全部显式登记）

> 执行者 Hy4（非 Lead）｜本文件记录**本卡与任务卡 / FROZEN SPEC / 上游做法之间的判断分歧与处置**，不隐藏、不自行改写判据。裁决权在 Lead。

## D0 ★★ W68 的 V2 存在两套并发版本，本卡以「权威 W68b 版」为准 —— 与「按文件名取最新」的直觉可能不一致

- `[本次实测]` 本卡启动（`00:45:27`）后，W68 根目录于 `00:45:12` / `00:46:19` 被并发方覆盖：
  - 我**首次读到**的 `CRITERIA_SPEC_V2.md`（10845 B，FROZEN `2026-11-14T00:32:14.7707651+08:00`，自署 `GLM-5.3-Flash`）与 `tool_b_stats_v2.py`（22280 B，`B-W68-2`，联合 `max_f TVD_f` 置换、`random.Random(seed).shuffle`、工具输出带 `gate` 字段）；
  - 随后被覆盖为 **W68b/Hy4 版**：spec 15229 B / FROZEN `2026-11-14T00:33:05.3748807+08:00`、tool 20787 B / `B-W68B-V2-1`（逐字段 TVD、`numpy` 多元超几何精确重分、`N_disc` 取两臂 max）。
- `[转引]` `W68_criterion_discrete_fix\EVIDENCE\CONCURRENT_WRITER_NOTE.md`：目录被两个执行者并发写入；W68b 已把根目录「恢复自洽」为自己的版本，并在 §4 给出**权威 sha256** 与「再次被覆盖则以 `EVIDENCE\W68b_snapshot\` 为准」的验收指引。`REVIEW\LEAD_VERIFY_W68B.md` 记载的 FROZEN `00:33:05` 与 `W68b PROGRESS.md` 的冻结时刻均对应此版。任务卡写的冻结时刻 **`2026-11-14T00:33:05`** 亦对应 W68b 版。
- **本卡处置**：严格按任务卡指定的**路径**（`W68_criterion_discrete_fix\CRITERIA_SPEC_V2.md` / `tool_b_stats_v2.py`）取**当前**文件，逐字节复制到本卡并 hash 自证；两副本 sha256 与 `CONCURRENT_WRITER_NOTE.md §4` 的权威值**完全一致**（`TOOL_HASHES.json`）。**不使用**首次读到的 GLM 版工具/规格，也不事后混合两版。
- **留给 Lead 裁决**：并发方产物归属、是否终止并发进程、后续卡是否合并两版实现。若 Lead 认为本卡应改用归档 GLM 版重跑，须**另开卡事先声明**；本卡不事后切换判据（§3.4）。
- **附带处置**：`LIVE_RESULT_V2.md §4` 把两版 gate 原句**都逐字抄录**（权威版 §2.3/§2.4 判定规则表 + 归档版 §3.3 `B-2v2` 行 + 工具内嵌 `gate` 字符串），避免「gate 原句」指哪一套产生验收歧义。两版对 W65 数据结论一致（`CONCURRENT_WRITER_NOTE.md §2`），`N_ks`/`D_ks`/`p`/`J` 连续量读数逐值一致。

## D1 沿用 W65 取舍：B 臂用 v15 **append** 路线，未用 `battlemd:inplace`

- 任务卡明确「**沿用 W65 的取舍**……不用 inplace —— 因为要让两臂玩同一张官方图才有可比性（W65 `DISAGREE.md` D1）……若你认为必须验 inplace，另开卡，别在本卡混」。本卡**照办**，不构成新的异议，仅登记以保持与 W65 的可追溯一致。
- `[本次实测]` `out\pkg\W65Bline\` 只有 `BATTLEMD98.INI`（无 `BATTLEMD.INI` 就地改写）；`sandbox_base\BATTLEMD.INI` 的 `[SOV1] Scenario=SOV01umd.MAP` 逐字未变；四趟 `0x125C` 全为 `SOV01UMD.MAP`。
- `[静态推断]` 若用 inplace，A/B 会加载不同 `map_name`，`dframe` 分布比较失去意义且必然由 `map_name` 触发 B-2。留给 Lead 的裁决点与 W65 D1 相同：若原意是「必须验 inplace 就地改写」，需另开卡补跑（见 `UNKNOWNS.md` U8）。

## D2 设计文件与包名沿用 W65 的 `W65Bline`（逐字节复制，未改名）

- `[本次实测]` `designs\w69_design.json` 是 `W65_bline_live_collect\designs\w65_design.json` 的**逐字节副本**（campaign.name=`W65Bline`，missions=`W65M1/W65M2`），因此 `PKG_INNER = PKG / "W65Bline"`，包内容资源名也带 `W65` 前缀。
- 理由：**保证与 W65 已验证的 append 包逐字节同构**，使「两臂同一干净沙箱起点 + 同一张官方图」的对照条件与 W65 完全一致，避免引入新的变量。文件名带 `W65` 只是内部 campaign 名，**不影响**两臂进入的官方第一关（已实测四趟 `SOV01UMD.MAP`）。
- `[静态推断]` 若 Lead 要求 W69 产物全部使用 W69 命名，可另开卡改名重建；本卡不擅自改设计（改设计 = 改包内容 = 改实验条件）。

## D3 使用「逐字节副本」而非「直接调用 W68/W62 路径下的脚本」

- 任务卡：工具 `tool_b_stats_v2.py`「**原样使用，一个字节不改**」；红线 5「**不得直接调用别卡脚本**（W55b 曾因此覆盖 W45 原始证据）：要复用 `w65_collect.py` 就复制过来改输出路径」。
- 本卡把 4 个工件（`tool_b_stats_v2.py`、`tool_c_writeaudit.py`、`w65_collect.py`、`w65_report.py`）+ 1 个设计 + 1 份 spec **全部先逐字节复制进本卡**，再运行**自己的副本**；`TOOL_HASHES.json` 逐文件列 sha256 并证明 `ALL_BYTE_IDENTICAL=True`，另附 `CONCURRENT_WRITER_NOTE.md §4` 权威 sha 复核。
- `[静态推断]` 副本与原件字节相同 ⇒ 满足「一个字节不改」；只运行本卡副本 ⇒ 满足红线 5。`v15 ra2forge` 工具链是任务卡指定的构建/安装工具，按原路径调用（只读其 CLI，不写其目录）。
- 采集器 `w69_collect.py` 在副本基础上**仅改**：`CARD/OUT/BASE/PKG` 路径、`DESIGN` 文件名、`TOOL_C/TOOL_B` 指向本卡副本、`owner=w65→w69`、Sink 文件名、`SPEC_FROZEN_AT` 元数据、finalize 卡名与文案；**FROZEN 阈值与判定逻辑零改动**（判定完全在 V2 工具内）。

## D4 合并臂 `A=A1∪A2`、`B=B1∪B2`（继承 W65 / FROZEN 工具自检语义）

- `[本次读码]` V2 工具 `--compare` 的 `--arm-a/--arm-b` 需合并臂，`--noise-a1/a2/b1/b2` 需四条独立同臂轨迹；W65 与 FROZEN 工具自检 `_merge()` 都用「同臂两趟逐行拼接」。
- `[本次实测]` 合并臂各含 1 个拼接边界伪差（`cv≈143/141`），两臂对称存在；本卡**未剔除、未补齐、未截断**（§3.4 禁止）。该伪差对 `D_ks` 贡献 ≈1/20460。见 `UNKNOWNS.md` U5。
- `[静态推断]` 若 Lead 认为应改用「单趟为臂、另一趟为噪声」或「按行对齐」的其它合并策略，涉及改实验协议，须另开卡事先声明；本卡不事后切换。

## D5 `SAME_DISTRIBUTION` 的措辞保留（严格按任务卡口径）

- 任务卡：`SAME_DISTRIBUTION` **不等于**「等价性成立」；正确表述为 **「在 V2 判据、n≈8000/趟、该场景、该观测量集合下，未检出装包导致的行为分布差异」**；不得写「B 线等价性成立」「装包无影响」。
- 本卡**照写**该口径句，并同时如实给出**实测**每趟 ≈10,200 行（≥8000 目标）——名义 `n≈8000/趟` 与实测值并列，不把名义量当实测值，也不把实测值替换掉任务卡要求的措辞。
- 本卡**不签发**任何等价/不等价结论；判定词严格取自 `b_compare_v2.json` 的 `verdict` 字段，未替换、未美化。

## D6 判据 C 在惰性沙箱上取快照，而非直接对 B1/B2 趟内沙箱实体

- 同 W65 做法（`--phase audit`）。B1/B2 趟内沙箱在还原 + `IDENTICAL_TREE=true` 后已删除，`pristine_<tag>\` 保留字节副本。见 `UNKNOWNS.md` U6。
- `[静态推断]` 安装期写入集由 v15 CLI 决定，与是否跑图无关；但本卡**未对趟内沙箱本体直接跑 `--audit`**，如实登记，不冒充。

## D7 每趟结束后删除该趟沙箱目录（同 W63/W65 惯例）

- `[本次实测]` 在完成逐字节还原 + 实算 `IDENTICAL_TREE=true` 之后删除 `sandbox_<tag>`（`w69_run.ndjson` 的 `trip_sandbox_removed` 事件）。理由：4 × ~1.99 GB 副本占盘；证据（NDJSON / 截图 / 日志 / `restore_proof_*.json` / `pristine_*` 字节副本）全部已落 `out\`。
- 真目录 `ra2youli` 从未被写，`REAL_DIR_PROOF.txt` 的 PRE/POST 全树零改动即最终自证。若 Lead 要求保留完整 2 GB 沙箱实体，本卡 `pristine_<tag>\` 可复核根级文件字节副本，但沙箱已按 W63 惯例清理。

## D8 未重跑以「修正」判定

- 看到 `SAME_DISTRIBUTION` 之后，本卡**没有**再跑第二轮（例如改固定 N 行、改 cadence、换设计）来争取另一个词。理由：看到结果后改 protocol 属 §3.4 禁止的事后调整，且会产生两套证据、两个判定，容易被误读为 verdict shopping。
- 取舍：宁可交付一个带完整披露的 `SAME_DISTRIBUTION` + 明确局限（U1 单值退化、U2 边缘分布、U8 未验 inplace），也不交付靠事后改动换来的「好看」结果。若 Lead 需要更强检出力，请**另开卡事先声明**新协议再跑。
