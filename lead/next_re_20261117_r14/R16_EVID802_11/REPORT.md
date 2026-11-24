# R16-EVID802-11 执行报告

> 任务：把 11 行的 `evidence_path` 连到盘上已有的 `PROOF_<entry>.txt`（纯台账修复，不做逆向）。
> 写域：`lead\next_re_20261117_r14\R16_EVID802_11\`；未写 `COVERAGE\coverage.tsv`。

## 1. 11 行逐行判定摘要（旧指针 → 新指针）

共 11 行：**OK 11 / SKIP 0 / UNDECIDED 0**。每个 entry 在 lead 全树仅找到 **1 份** PROOF_<entry>.txt，无需二分。所有产物文件非空、①②③④ 四段齐全、entry 在内容中出现 2–3 次，④ 段为同一 entry 的外部派发/装表记录，与本行槽位语义一致。

- **0045A560**（S10，T_DynamicVectorClass_PAVInfantryClass__::slot2）：OK — 旧 `EVIDENCE/classification_trace.tsv#0045A560` → 新 `EVIDENCE/classification_trace.tsv#0045A560;S10_KPROVED\EVIDENCE\PROOF_0045A560.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **0045A610**（S10，T_DynamicVectorClass_PAVInfantryClass__::slot4）：OK — 旧 `EVIDENCE/classification_trace.tsv#0045A610` → 新 `EVIDENCE/classification_trace.tsv#0045A610;S10_KPROVED\EVIDENCE\PROOF_0045A610.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **0053C6A0**（S20，T_DynamicVectorClass_PBVAnimClass__::slot2）：OK — 旧 `EVIDENCE/classification_trace.tsv#0053C6A0` → 新 `EVIDENCE/classification_trace.tsv#0053C6A0;S20_KPROVED\EVIDENCE\PROOF_0053C6A0.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **005514B0**（S20，T_DynamicVectorClass_PAVLaserDrawClass__::slot2）：OK — 旧 `EVIDENCE/classification_trace.tsv#005514B0` → 新 `EVIDENCE/classification_trace.tsv#005514B0;S20_KPROVED\EVIDENCE\PROOF_005514B0.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **00551560**（S20，T_DynamicVectorClass_PAVLaserDrawClass__::slot4）：OK — 旧 `EVIDENCE/classification_trace.tsv#00551560` → 新 `EVIDENCE/classification_trace.tsv#00551560;S20_KPROVED\EVIDENCE\PROOF_00551560.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **00557090**（S20，T_DynamicVectorClass_PAVLineTrail__::slot2）：OK — 旧 `EVIDENCE/classification_trace.tsv#00557090` → 新 `EVIDENCE/classification_trace.tsv#00557090;S20_KPROVED\EVIDENCE\PROOF_00557090.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **00557140**（S20，T_DynamicVectorClass_PAVLineTrail__::slot4）：OK — 旧 `EVIDENCE/classification_trace.tsv#00557140` → 新 `EVIDENCE/classification_trace.tsv#00557140;S20_KPROVED\EVIDENCE\PROOF_00557140.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **006B1850**（S10，T_DynamicVectorClass_PAVSlaveManagerClass__::slot2）：OK — 旧 `EVIDENCE/classification_trace.tsv#006B1850` → 新 `EVIDENCE/classification_trace.tsv#006B1850;S10_KPROVED\EVIDENCE\PROOF_006B1850.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **006B1900**（S10，T_DynamicVectorClass_PAVSlaveManagerClass__::slot4）：OK — 旧 `EVIDENCE/classification_trace.tsv#006B1900` → 新 `EVIDENCE/classification_trace.tsv#006B1900;S10_KPROVED\EVIDENCE\PROOF_006B1900.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **006B8660**（S10，T_DynamicVectorClass_PAVSpawnManagerClass__::slot2）：OK — 旧 `EVIDENCE/classification_trace.tsv#006B8660` → 新 `EVIDENCE/classification_trace.tsv#006B8660;S10_KPROVED\EVIDENCE\PROOF_006B8660.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`
- **006B8710**（S10，T_DynamicVectorClass_PAVSpawnManagerClass__::slot4）：OK — 旧 `EVIDENCE/classification_trace.tsv#006B8710` → 新 `EVIDENCE/classification_trace.tsv#006B8710;S10_KPROVED\EVIDENCE\PROOF_006B8710.txt;M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`

新指针格式（逐行一致）：`原有 classification_trace 段` + `;` + `新 PROOF 路径（相对 next_re_20261117_r14，形如 S10_KPROVED\EVIDENCE\PROOF_0045A560.txt）` + `;` + `M94 指针修复：④ 已写在盘上（PROOF 文件含 ①②③④ 四段），原指针只连 classification_trace`。原有 `classification_trace` 段一律保留，未删除。

## 2. SKIP / UNDECIDED 清单与原因

- **SKIP**：无。
- **UNDECIDED**：无。
- 11 个 entry 的 PROOF 均为唯一候选、四段齐全、entry 命中，不存在多份同名需二分的情况。

## 3. coverage.tsv 改前/改后一致性证明（本任务未改该文件）

本任务自始至终未对 `COVERAGE\coverage.tsv` 执行任何写操作。以"本任务产出写入前"与"本任务产出写入后"两次采样对比：

| 采样点 | mtime (UTC) | 字节 | sha256 |
|---|---|---|---|
| 改前（产出写入前） | 2026-11-20T16:55:34.3400563Z | 4077137 | 822B2112C64451849EF9E7D26D5E0BB02EA9E8B46CD9CCFAC465410CAC1646D8 |
| 改后（产出写入后） | 2026-11-20T16:55:34.3400563Z | 4077137 | 822B2112C64451849EF9E7D26D5E0BB02EA9E8B46CD9CCFAC465410CAC1646D8 |

**结论：改前/改后 mtime、字节、sha256 三项完全一致** → 证明本任务的写入未触及 `coverage.tsv`。（sha256 与字节数逐字节相同；mtime 为同一时刻 `2026-11-20T16:55:34.3400563Z`。）

透明性附注（并发观察）：本任务会话开始时首次采样到的 coverage.tsv 为 `mtime_utc=2026-11-20T16:38:08.3629893Z, bytes=4068561, sha256=400D211A53AB55C7E24E85B389727934C235FBE66A7B52FB5736313DBBC69F7F`；在产出写入前，该文件已被**其他进程**更新为上表"改前"状态（`mtime_utc=2026-11-20T16:55:34.3400563Z`），发生在本次会话期间（本任务开始时刻 2026-11-20T16:53:23Z 之后）。该并发变更非本任务所为。两个版本中 11 个目标行的 `evidence_path` 均为 `EVIDENCE/classification_trace.tsv#<entry>`（trace-only）、grade 均为 `[已证]`，故本 delta 基于当前盘上行生成，逐字节取自"改前"版本，不受该并发变更影响。

## 4. 并表后 R_OK 预估（预估，非实际并表）

- 当前：`R_OK = 852 / 1,654`（卡面给定）。
- 逐个确认：11 个 entry 当前均为 `R_TRACE_ONLY` —— grade `[已证]` 但 `evidence_path` 仅连 `EVIDENCE/classification_trace.tsv#<entry>`，无任何 PROOF 证据段。
- 本 delta 为这 11 行追加真实 PROOF 证据段，并表后这 11 行应转为 `R_OK`。
- **预估并表后：R_OK ≈ 852 + 11 = 863 / 1,654**（预估；实际并表由合并员执行，本任务不写 coverage.tsv）。

## 5. 自检

只读：仅只读打开 `coverage.tsv` 与 11 个 PROOF 文件、只读遍历 `lead\` 目录；未做任何逆向、未读 `gamemd.exe`、未改卡目录。只写自己目录：全部产物（`fields.tsv` / `coverage_delta.tsv` / `REPORT.md`）均写在 `lead\next_re_20261117_r14\R16_EVID802_11\`，未写 `COVERAGE\coverage.tsv`，未写 `PANEL.md` / `R14_COMMON.md` / 台账 / 看板 / `_drafts\` / `_cards\` / 任何卡目录。未改任何共享文件（见第 3 节一致性证明）。

## 6. 注记修正记录（R16-FIX-EVID802-11-NOTES）

> 背景：`R16_AUDIT_EVID802_11` 对上一版 delta 判 **FAIL 11 / PASS 0**，唯一必改项 §D-2：11 行第 6 列末尾注记**逐字节完全相同（unique=1）**，不含本行信息，属复制。§A/§B/§C/§D-1 已全部 PASS，本轮一律不动。

### 6.1 改法（只动注记）
仅替换 `coverage_delta.tsv` 第 6 列 `;M94 指针修复：` **之后**的注记。路径前缀 `EVIDENCE/classification_trace.tsv#<entry>;<卡目录>\EVIDENCE\PROOF_<entry>.txt` 逐字节保持不变（本轮未增删、未改写其中任何字符）。每行新注记含本行实际值三项：① 本行 entry；② PROOF 文件名与所在卡目录；③ 从盘上 PROOF 文件 ④ 段实读的实测形态与关键地址。

### 6.2 注记 unique 计数
| 口径 | 上一版 | 本版 |
|---|---|---|
| 整条注记（含 `;M94 指针修复：` 前缀）原文 unique | **1 / 11** | **11 / 11** |
| 把本行 entry 替换为 `<ENTRY>` 占位符后 unique | 1 / 11 | **11 / 11** |

### 6.3 「entry 归一后仍两两不同」自证
对 11 行新注记做三种独立归一后再数 unique，结果全为 11：

1. **逐行按本行 entry 字面替换为 `<ENTRY>`**（审计口径：仅把 entry 当占位符）——unique = **11**。差异不只来自 entry：每行还带本行 name（如 `T_DynamicVectorClass_PAVInfantryClass__::slot2`）、④ 形态描述、以及 ④ 段关键地址（派发点 / 装表点 / vt）。
2. **所有 8 位十六进制 token 统一替换为 `<HEX8>`**——unique = **11**。
3. **所有 6–8 位十六进制 token 统一替换为 `<HEX>`**——unique = **11**。

三种归一都得 11 ⇒ 即使抹掉 entry 与全部地址，各行 name + 形态描述仍互不相同，不存在「仅差 entry」或「两两相同」的注记。

### 6.4 逐行 ④ 取值（均从盘上 PROOF 文件 ④ 段实读，未编造）
| entry | 卡目录 / PROOF | ④ 段实测形态 | 写入注记的关键地址 |
|---|---|---|---|
| 0045A560 | S10_KPROVED / PROOF_0045A560.txt | exact external dispatch sites（外部派发点） | 派发点 00517B1E；槽位 vt=007E43C8 slot2 |
| 0045A610 | S10_KPROVED / PROOF_0045A610.txt | exact external dispatch sites（外部派发点） | 派发点 00517E8D；槽位 vt=007E43C8 slot4 |
| 0053C6A0 | S20_KPROVED / PROOF_0053C6A0.txt | exact dispatch sites / global vptr write evidence（全局 vptr 写装表点） | vt=007EBFCC；装表点 site=00539CC5 |
| 005514B0 | S20_KPROVED / PROOF_005514B0.txt | exact dispatch sites / global vptr write evidence（全局 vptr 写装表点） | vt=007ECEDC；装表点 site=0054FF85 |
| 00551560 | S20_KPROVED / PROOF_00551560.txt | exact dispatch sites / global vptr write evidence（全局 vptr 写装表点） | vt=007ECEDC；装表点 site=0055002A |
| 00557090 | S20_KPROVED / PROOF_00557090.txt | exact dispatch sites / global vptr write evidence（全局 vptr 写装表点） | vt=007ED0CC；装表点 site=00556A9F |
| 00557140 | S20_KPROVED / PROOF_00557140.txt | exact dispatch sites / global vptr write evidence（全局 vptr 写装表点） | vt=007ED0CC；装表点 site=00556D90 |
| 006B1850 | S10_KPROVED / PROOF_006B1850.txt | exact external dispatch sites（外部派发点） | 派发点 006AF32E、006AF40C；槽位 vt=007F315C slot2 |
| 006B1900 | S10_KPROVED / PROOF_006B1900.txt | exact external dispatch sites（外部派发点） | 派发点 006AF509；槽位 vt=007F315C slot4 |
| 006B8660 | S10_KPROVED / PROOF_006B8660.txt | exact external dispatch sites（外部派发点） | 派发点 006B6E69、006B6F69；槽位 vt=007F35E4 slot2 |
| 006B8710 | S10_KPROVED / PROOF_006B8710.txt | exact external dispatch sites（外部派发点） | 派发点 006B7087；槽位 vt=007F35E4 slot4 |

### 6.5 样例注记（两条，证明不同）
- **0045A560**：`;M94 指针修复：原指针只连 classification_trace；本行 T_DynamicVectorClass_PAVInfantryClass__::slot2（entry=0045A560）④ 已写在 S10_KPROVED\EVIDENCE\PROOF_0045A560.txt 的 ④ 段（形态：外部派发点 exact external dispatch sites，RING_TYPE=EXACT，派发点=00517B1E；本行槽位 vt=007E43C8 slot2）`
- **0053C6A0**：`;M94 指针修复：原指针只连 classification_trace；本行 T_DynamicVectorClass_PBVAnimClass__::slot2（entry=0053C6A0）④ 已写在 S20_KPROVED\EVIDENCE\PROOF_0053C6A0.txt 的 ④ 段（形态：全局 vptr 写装表点 exact dispatch sites / global vptr write evidence，RING_TYPE=EXACT，vt=007EBFCC，装表点 site=00539CC5）`

### 6.6 本轮校验结论
- 11 行新注记 unique = **11**；entry 归一后 unique = **11**（另两种 hex 归一亦为 11，见 6.3）。
- 11 行路径部分（`;M94` 之前）与上一版**逐字节相同**（本轮只替换 `;M94 指针修复：` 之后的文本）。
- `coverage_delta.tsv` 第 1–5、7、8 列与盘上 `COVERAGE/coverage.tsv` 对应行**逐字节相同**（程序逐列比对通过）。
- `coverage.tsv` 本轮读到 **4,079,053 B / sha256 3A1DC1DD3F67B7684BF167640CEECF3EC85330CF5B54C31B65A02CA98C993D4A**；写入前后字节与 sha 完全一致，**未写该文件**。（注：第 3 节表格记录的是上一轮期间另一进程更新前的旧快照 4,077,137 B；本轮盘上实值以本节为准，本轮未对 coverage.tsv 做任何写操作。）

### 6.7 写域声明
本轮仅写 `lead\next_re_20261117_r14\R16_EVID802_11\` 内三份产物（`coverage_delta.tsv` / `fields.tsv` / `REPORT.md`，覆盖自身产物）。未写 `COVERAGE\coverage.tsv`，未改任何其它目录、任何共享控制文件；未做逆向、未读 `gamemd.exe`、未编造。
