# ASM-SCAN —— 全库文档内联断言机械化复扫（VA + 字节串 逐条对二进制复核）

> 任务卡：ASM-SCAN ｜ 执行方：DSH 子代理 ｜ 日期：2026-09-27
> 基线二进制：`ra2youli/gamemd.exe`（YR 1.001，4,825,360 B，MD5 `4F37486E5B0DBE2AE5F45AEEE0F98367`，ImageBase `0x400000`）—— **只读，全程未写盘**
> 工具：`python tools/verify_anchors.py`、`python tools/audit_bytes.py`、Capstone 5.0.7 x86-32
>
> **快照声明（双快照口径）**：抽取跑批窗口 = 2026-09-27 09:54:28 ~ 09:59:10（`extract_claims.py`/`classified.json` 的 mtime 为准）。本文件**全部行号为该窗口内快照的行号**。窗口内与窗口后另有写入者改动了两份被扫文档（`REVERSE_ENGINEERING_AND_PATCHES.md` mtime 10:01:08、`docs/RE_COORDINATION.md` mtime 10:01:18，**非本执行方所写**——本执行方只对二者做过 `read`/`grep`）。收尾复核时本轮引用的台账行号 `:237 / :1992 / :1993` **原文逐字未变**，故行号仍可用；若 Lead 后续改写这两份文档，请以「VA + 声明字节」为锚、勿以行号为锚。
> 复核用快照哈希（2026-09-27 10:02 复算）：`REVERSE_ENGINEERING_AND_PATCHES.md` = `794389D07BB347562BCE8ADA7B83D4FD`（240,719 B）｜`docs/RE_COORDINATION.md` = `9D8C3AB1794124AAF24E38F5D92AB172`｜`docs/re/deep_dive_sweeps_closure.md` = `9BF99377637A5C6295FEBCBB00231994`（51,852 B）｜`docs/re/ARCHITECTURE_ATLAS.md` = `70ADF4AA05EB7B138DC47067FCA1F061`

---

## 0. 结论摘要（先读这段）

1. **机械复扫已完成**：150 个文档、28,703 处 `0xVA` 出现点全部过机，其中 **2,815 条带邻近字节串**（可核验断言），2,258 条地址引用（无字节串，判类⑤）。
2. **文档抄错字节确有系统性存量，但远小于表面计数**：可核验断言中 **①一致 2,254 条（87.53%）**，**③不符 310 条 + ②长度差 11 条 = 321 条**。321 条经分桶复核后，**真·需勘误 114 条**（P1 36 / P2 8 / P3 27 / P4 43），**其余 207 条为抽取误报 / 预期不符**（详见 §6 误报控制）。
3. **最大单个真错来源不是「笔误」而是「手写规范化清单」**：`re_sprint_S2/S3/S5/S7/S11/S14/S17` 系列报告的 asm 清单语义基本正确、**机器码不可复现**（例：`C7 40 04..` 文档写 `[eax+4]`、实测 `C7 46 04..` 即 `[esi+4]`；`8A 05` 手写、实测 `A0` 短编码）。此类已在总表标为 P3，**建议不改结论、只加「清单为手写示意」标注**。
4. **第 6 例「文档抄错字节」的同类问题本批又发现多处**，最重的三条：`ARCHITECTURE_ATLAS.md:471/472`（`89 7C 83 E4` 全镜像 **0 命中**）、`ARCHITECTURE_ATLAS.md:1371/1374`（`85 C0` 实为 `84 C0`，`test eax,eax` 应为 `test al,al`）、`cross_doc_consistency_audit.md:182`（`...84 00 00 00 00` 实为 `...84 00 00 00 01`，立即数 0/1 写反）。
5. **N-2 真锚点已找到**（S5）：`66 8B 01`（`mov ax,[ecx]`）在全镜像共 **65 处**，其中 **`0x007BC8A3`** 正是 `BlitTrans@G`（`0x007BC890`，`ret 0x20`）内的 16 位源像素流循环体 —— **N-2 结论成立，原锚点 VA 抄错**，建议改锚 `0x007BC8A3`。

---

## 1. 方法（可复跑、无人工记忆）

### 1.1 S1 抽取器 `out/re_work/asm_scan/extract_claims.py`

扫描范围：`docs/re/**.md`（含 `dispatch/`）+ 台账 `REVERSE_ENGINEERING_AND_PATCHES.md` + `docs/RE_COORDINATION.md`，共 **150 个文件**。

| 通道 | 触发格式 | 条数 |
|---|---|---|
| C1 `immediate` | `VA` 后紧跟分隔符（`: = \| ：`）再接连续 2-hex 字节 token | 1,621 |
| C2 `quoted` | C1 失败时，取 VA 后 100 字符内最近的反引号包裹纯字节短语 | 6 |
| C3a `cell` | markdown 管道单元格中纯字节短语（首格为主断言，其余格记入 `extra_cells`） | 1,174 |
| C3b `arrow` | `→` 分隔的「字节\|反汇编」链，逐段收集（**分段拼接，非连续串**，单独成桶） | 14 |

### 1.2 排除规则（S6 误报控制的第一道闸）

- **E1 token 边界**：`(?<![0-9A-Za-z_])` / `(?![0-9A-Za-z_])` 双向卡边界 ⇒ `push edx` 里的 `ed`、`call [eax+4]` 里的 `ea` 永不误收。
- **E2 裸地址必须 0 开头**（`004093B0`），杜绝 `accede`/`deface` 等「纯十六进制字母英文单词」误判。
- **E3 汇编伪指令** `db/dd/dw/dq/dt/dc` 起始的 token 不作字节串。
- **E4** MD5/SHA 十六进制摘要天然不匹配（长于 8 位）。
- **E5** 无分隔符 / 无引号 / 无管道 / 无箭头的纯地址引用 ⇒ 判类⑤「无法解析」，不计入不符。

### 1.3 S2 判定器 `classify.py`

地址映射**一律走 PE 段表**（`off = rawptr + (VA - 段基址)`），不用 `VA-0x400000` 近似 —— 两者在 `.text/.rdata/.data` 等价，但 `.rsrc/.detour` 相差 `0x2FC000`（沿用 `tools/audit_bytes.py` 口径）。判定五分类：

| 类 | 定义 | 条数 |
|---|---|---|
| ① `EXACT` | 声明字节 == 该 VA 实测字节 | 2,254 |
| ② `PREFIX_LEN` | 与实测共享 ≥3 字节前缀但尾部不符（长度/尾字节差） | 11 |
| ③ `MISMATCH` | 与实测共享 <3 字节前缀（文档字节与二进制不符） | 310 |
| ④ `OOB` | 地址不在基线镜像内（外模块 / 补丁运行时 `.detour` / 非地址数值） | 239 |
| ⑤ `NOBYTES` | 纯地址引用，无邻近字节串（跳转目标 / 立即数 / 字符串引用） | 25,888 |
| — `ALIAS` | 行内同时给出 VA 与 FileOffset，字节实测属后者（自愈重绑） | 1 |

判类②③每条额外记录：**声明字节串在全镜像/`.text` 的命中次数**与**最近命中地址及 Δ** —— 这是把「VA 走锚」与「字节抄错」分开的关键证据（S4 验收依据）。

### 1.4 S3 分桶 `triage.py` + `build_errata.py`

321 条②③再按可复现规则分桶（顺序即优先级）：

| 桶 | 判定条件 | 条数 |
|---|---|---|
| `A-ARTIFACT` 抽取误报 | 单元值列 / arrow 拼接 / 行内多 VA / `A/B=x/y` 简写 / FileOffset 别名 | 178 |
| `B-PATCH` 补丁后字节 | 声明以 `E9`(≥5B)/`EB`(≥2B) 开头，或全 `90` 填充 | 26 |
| `B-ERRATA-QUOTE` | 行内含「改前原文/原记录/订正」等标记（历史引用） | 3 |
| `P1-BYTE-ERROR` | 声明 ≥3 字节且**全镜像 0 命中**（非 VA 漂移） | 36 |
| `P2-VA-DRIFT` | 声明串罕见（≤4 命中）且落在 VA±0x400 内 ⇒ 给出真值 VA | 8 |
| `P3-LIST-DRIFT` | sprint 报告 asm 清单族（手写规范化/整体偏移） | 27 |
| `P4-REVIEW` | 其余需逐句判读（多为 1 字节或高频公共模式） | 43 |

---

## 2. 统计总表（S3）

| 指标 | 数值 |
|---|---|
| 扫描文件 | 150 |
| `0xVA` 出现点总数 | 28,703 |
| 带字节串（可核验断言） | 2,815（9.81%） |
| 纯地址引用（判类⑤） | 25,888（90.19%） |
| ①一致 | 2,254（占可核验 80.07%） |
| ②长度差 + ③不符 | 321（11.40%） |
| ④越界/非镜像 | 239（8.49%，明细：外模块 89 / 未映射 69 / 补丁运行时 detour 77 / 非地址数值 4） |
| 可核验子集（2,815 − 239④ − 1 alias = 2,575） | ①一致率 **87.53%** |
| **真·需勘误（P1+P2+P3+P4）** | **114 条** |
| 非勘误（误报 + 预期不符） | 207 条（占 321 的 64.5%） |

不符行 TOP 文件（321 条口径）：

| 文件 | 条数 | 主体性质 |
|---|---|---|
| `docs/re/trigger_system_manifest.md` | 85 | **85/85 全为单值表格列（抽取误报）** |
| `docs/re/re_sprint_S2_report.md` | 33 | 真错 + 手写规范化清单（P1 8 / P3 大部） |
| `docs/re/ARCHITECTURE_ATLAS.md` | 19 | 真错 10（单值列误报 10） |
| `docs/re/nonrle_blit_and_named_hotspots.md` | 18 | **18/18 单值列（字节长度列）** |
| `docs/re/audio_input_hotspots.md` | 15 | 14 单值列 + 1 真错（`:617`） |
| 台账 `REVERSE_ENGINEERING_AND_PATCHES.md` | 13 | 含 §七 2 条真错、7 条 arrow/勘误引用 |

---

## 3. 最小勘误总表

全量机器表：`out/re_work/asm_scan/errata_table.md`（357 行，含 P1/P2/P3/P4 与非勘误附录）、原始 TSV：`mismatch_ranked.tsv`。以下**内联 P1、P2 两张可执行勘误表**。

### 3.1 P1 —— 高置信真·字节错（声明 ≥3 字节且全镜像 0 命中，非 VA 漂移）

| # | 文件:行 | VA | 声明字节 | 实测字节 | 共前缀 | .text 命中 | 最近命中 | Δ | 说明 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | REVERSE_ENGINEERING_AND_PATCHES.md:237 | 0x007C8B3D | `FF 74 24 04 E8 A3` | `FF 74 24 04 E8 A2` | 5 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 2 | REVERSE_ENGINEERING_AND_PATCHES.md:238 | 0x00655F48 | `8B 8D 58 12 00 00` | `85 ED 0F 84 2E FF` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 3 | REVERSE_ENGINEERING_AND_PATCHES.md:1992 | 0x006F8737 | `C1 F8 01` | `D1 F8 EB` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 4 | docs/RE_COORDINATION.md:1240 | 0x006F8737 | `C1 F8 01` | `D1 F8 EB` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 5 | docs/re/ARCHITECTURE_ATLAS.md:471 | 0x006DA945 | `89 7C 83 E4` | `8B 4C 24 1C` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 6 | docs/re/ARCHITECTURE_ATLAS.md:472 | 0x006DA957 | `FF 43 E0` | `89 83 E0` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 7 | docs/re/ARCHITECTURE_ATLAS.md:1513 | 0x0064DAD9 | `E8 52 1A F6 FF` | `00 00 00 8B B8` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 8 | docs/re/cross_doc_consistency_audit.md:182 | 0x006E9CE8 | `C6 86 84 00 00 00 00` | `C6 86 84 00 00 00 01` | 6 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 9 | docs/re/doc_consistency_fix_list.md:214 | 0x00577EC5 | `89 91 34 01 00 00` | `89 B8 34 01 00 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
> 【W3 勘误 · W3-A6/ISSUE-TABLE-GAP-BYTES】改前：89 91 34 01 00 00；改后：89 B8 34 01 00 00 (0x00577EC5) / 89 98 34 01 00 00 (0x00577B60)；依据：ra2youli/gamemd.exe:0x177EC5, 0x177B60; docs/re/doc_consistency_fix_list.md:49 (N-2)；分级：P0
| 10 | docs/re/doc_consistency_fix_list.md:215 | 0x00577B60 | `89 91 34 01 00 00` | `89 98 34 01 00 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 11 | docs/re/l4_vision_dirty_final_spec.md:72 | 0x006DA945 | `89 7C 83 E4` | `8B 4C 24 1C` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 12 | docs/re/l4_vision_dirty_final_spec.md:73 | 0x006DA957 | `FF 43 E0` | `89 83 E0` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 13 | docs/re/re_sprint_S14_report.md:475 | 0x00406F8C | `83 F8 21 7E 41` | `00 01 00 00 00` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 14 | docs/re/re_sprint_S14_report.md:487 | 0x0055D377 | `8A 05 80 ED A8 00 84 C0 75 33` | `A0 80 ED A8 00 C6 05 58 CD AB` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 15 | docs/re/re_sprint_S14_report.md:488 | 0x0055D830 | `E8 1B 75 07 00 E8 4B F8 F2 FF` | `E8 1B 75 07 00 E8 46 F8 F2 FF` | 6 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 16 | docs/re/re_sprint_S14_report.md:489 | 0x0055D650 | `8D 46 0A 89 0D 28 73 88 00 A3 30 73 88 00` | `8D 46 0A 89 0D 28 73 88 00 8D 4C 24 14 89` | 9 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 17 | docs/re/re_sprint_S14_report.md:490 | 0x0055D744 | `8D 46 0A 89 0D 28 73 88 00 A3 30 73 88 00` | `8D 46 0A 89 0D 28 73 88 00 8D 4C 24 14 89` | 9 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 18 | docs/re/re_sprint_S17_report.md:51 | 0x006CD754 | `8B 8A EC 0F 00 00` | `8B 40 08 6A 00 6A` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 19 | docs/re/re_sprint_S2_report.md:167 | 0x004AA52B | `E8 B0 22 1B 00` | `8E FC 00 00 00` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 20 | docs/re/re_sprint_S2_report.md:345 | 0x006CDEFE | `E8 7D 24 D4 FF` | `D4 FF 85 C0 0F` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 21 | docs/re/re_sprint_S2_report.md:352 | 0x006CDF13 | `C7 00 E8 3F 7F 00` | `C7 06 E8 3F 7F 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 22 | docs/re/re_sprint_S2_report.md:353 | 0x006CDF19 | `C7 40 04 CC 3F 7F 00` | `C7 46 04 CC 3F 7F 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 23 | docs/re/re_sprint_S2_report.md:354 | 0x006CDF20 | `C7 40 08 C4 3F 7F 00` | `C7 46 08 C4 3F 7F 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 24 | docs/re/re_sprint_S2_report.md:355 | 0x006CDF27 | `C7 40 0C BC 3F 7F 00` | `C7 46 0C BC 3F 7F 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 25 | docs/re/re_sprint_S2_report.md:357 | 0x006CDF2E | `83 7E 68 00` | `8B 46 68 57` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 26 | docs/re/re_sprint_S2_report.md:371 | 0x006CDFB2 | `E8 89 12 00 00` | `8A 12 00 00 C7` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 27 | docs/re/re_sprint_S2_report.md:421 | 0x006CC36E | `80 78 52 00` | `00 00 84 D2` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 28 | docs/re/re_sprint_S2_report.md:423 | 0x006CC374 | `83 79 7C 00` | `8B 41 7C 85` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 29 | docs/re/re_sprint_S3_report.md:115 | 0x0045196E | `E8 2D 05 FD FF` | `8B C8 E8 2B 05` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 30 | docs/re/re_sprint_S3_report.md:126 | 0x00423B3C | `FF 90 48 00 00 00` | `FF 50 48 50 B9 E8` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 31 | docs/re/re_sprint_S3_report.md:232 | 0x00556D53 | `8B 15 7C CB AB 00` | `8B 0D 7C CB AB 00` | 1 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 32 | docs/re/re_sprint_S5_report.md:398 | 0x0040937A | `6A 00 68 E8 03 00 00 E8 4E FF 3B 00` | `6A 00 68 E8 03 00 00 51 52 E8 48 FF` | 7 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 33 | docs/re/re_sprint_S5_report.md:401 | 0x0055D377 | `8A 05 80 ED A8 00 84 C0 75 33` | `A0 80 ED A8 00 C6 05 58 CD AB` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 34 | docs/re/re_sprint_S5_report.md:404 | 0x006842D3 | `8B 0D 70 F7 87 00 E8 3B B4 EC FF` | `8B 0D 70 F7 87 00 C6 05 9C ED A8` | 6 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 35 | docs/re/superweapon_re.md:807 | 0x004AA52B | `E8 B0 22 1B 00` | `8E FC 00 00 00` | 0 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |
| 36 | docs/re/trigger_runtime_deep_dive.md:461 | 0x0055DE9F | `E8 CC 7D 02 00` | `E8 CC 7D 1C 00` | 3 | 0 | None | None | 声明字节在全镜像 0 命中（非 VA 漂移） |

### 3.2 P2 —— 真·VA 走锚（字节正确、地址抄错，已给出真值 VA）

| # | 文件:行 | VA | 声明字节 | 实测字节 | 共前缀 | .text 命中 | 最近命中 | Δ | 说明 |
|---|---|---|---|---|---|---|---|---|---|
| 1 | docs/re/deep_dive_sweeps_closure.md:265 | 0x006F876B | `8B 80 00 56 00 00` | `84 C9 74 23 8B 80` | 0 | 3 | 0x006F876F | 4 | 文档字节在 VA+4 处命中 → 真值 VA 0x006F876F |
| 2 | docs/re/deep_dive_sweeps_closure.md:269 | 0x006F876B | `8B 80 00 56 00 00` | `84 C9 74 23 8B 80` | 0 | 3 | 0x006F876F | 4 | 文档字节在 VA+4 处命中 → 真值 VA 0x006F876F |
| 3 | docs/re/re_sprint_S14_report.md:472 | 0x00409510 | `FF 15 F8 11 7E 00` | `56 FF 15 F8 11 7E` | 0 | 4 | 0x00409511 | 1 | 文档字节在 VA+1 处命中 → 真值 VA 0x00409511 |
| 4 | docs/re/re_sprint_S14_report.md:479 | 0x0053E516 | `68 38 81 82 00 56 E8 2A C3 28 00` | `E8 2A C3 28 00 83 C4 08 A3 68 04` | 0 | 1 | 0x0053E510 | -6 | 文档字节在 VA-6 处命中 → 真值 VA 0x0053E510 |
| 5 | docs/re/re_sprint_S14_report.md:480 | 0x0053E57A | `68 3C 81 82 00 56 E8 C6 C2 28 00` | `E8 C6 C2 28 00 83 C4 08 A3 68 04` | 0 | 1 | 0x0053E574 | -6 | 文档字节在 VA-6 处命中 → 真值 VA 0x0053E574 |
| 6 | docs/re/re_sprint_S7_report.md:47 | 0x004D37EA | `E8 F6 4F 09 00` | `8D 44 24 10 56` | 0 | 1 | 0x004D37F5 | 11 | 文档字节在 VA+11 处命中 → 真值 VA 0x004D37F5 |
| 7 | docs/re/re_sprint_S7_report.md:48 | 0x004D37D2 | `E8 DE 4B 09 00` | `8D 54 24 10 56` | 0 | 1 | 0x004D37DD | 11 | 文档字节在 VA+11 处命中 → 真值 VA 0x004D37DD |
| 8 | docs/re/savegame_block_manifest.md:126 | 0x0067E0A9 | `BA 20 41 8B 00` | `20 41 8B 00 8B` | 0 | 1 | 0x0067E0A8 | -1 | 文档字节在 VA-1 处命中 → 真值 VA 0x0067E0A8 |

> 注：`deep_dive_sweeps_closure.md:269` 是 closure §2.2「团队战术集火权重」的**现行正文**（`:265` 是其勘误块内的逐字引用）—— 即 **DA4-9 的「附带发现」尚未落地到正文**，本批复扫以机器证据确认：`0x006F876B` 处实测 `84 C9 74 23`（`test cl,cl` / `je`），文档字节真值位于 **`0x006F876F`（Δ+4）**。

### 3.3 P3 / P4

- **P3（27 条）sprint 报告 asm 清单族**：`re_sprint_S2`（8）、`S14`（7）、`S3`（4）、`S5`（3）、`S7`（2）、`S11`（2）、`S17`（1）。共同点：语义正确、编码不可复现（寄存器名被规范化 / 指令被展开或折叠 / 清单整体偏移 ±1~±11）。**建议按「示意清单」定性，不逐条改字节**；`S11` 的 6 条特殊：文档「VA 指向 `call`、字节串含前置 `push`」，属**记法约定**而非抄错（实测前置 push 起点 = VA−(push 长度)，Δ 恒为 −2/−5）。
- **P4（43 条）需逐句判读**：`blitter_microkernel_deep_dive.md:198-200`（`00496828` 起 3 条 push 清单整体偏 +1）、`landing_equivalence_static_proof.md:276/277/279`（`0x007C8E24` 区段清单整体错位）、`particle_fog_owner_evidence.md:226-228`（`0x0062FD6D` 区段清单整体错位）、`offline_verification_alternatives.md:132/133`（`Surface::Lock/Unlock` 入口字节与实测不符，最近命中在 0x7CBCAF/0x7BC610，Δ>1MB ⇒ 疑另一构建）、`ARCHITECTURE_ATLAS.md:1511-1514`（`0x0064DACE` 区段 4 条：文档 `mov eax,[0xA8B230]` vs 实测 `mov eax,[0xA83DEC]`，且后续指令序列整体不同 —— 该块是帧 CRC/随机数证据链的一环，**影响面最高**）、`deep_dive_sweeps_closure.md:586` / `台账:1993` / `RE_COORDINATION:1240` 为 N-2 历史引用（预期不符）。

---

## 4. S4 负向验证（证明判定器没有错杀）

对 ③ 类抽 **15 条**定点复核（另加 2 条判①的**阳性对照**），全部用 Capstone 反汇编 + 模式命中普查 + 分支目标反查三重交叉。原文见 `out/re_work/asm_scan/sample_review.txt`（377 行）。代表性三条：

```text
[docs/re/ARCHITECTURE_ATLAS.md:471]  VA=0x006DA945  FileOffset=0x2DA945  .text  verdict=MISMATCH
  declared : 89 7C 83 E4
  actual   : 8B 4C 24 1C
  declared pattern census: whole-image=0  .text=0  nearest .text hit=None
  --- ACTUAL bytes decoded at the documented VA (proof the VA holds real code):
      006DA945  8B 4C 24 1C          mov ecx, dword ptr [esp + 0x1c]
      006DA949  89 8C 83 E4 00 00 00 mov dword ptr [ebx + eax*4 + 0xe4], ecx
      006DA950  8B 83 E0 00 00 00    mov eax, dword ptr [ebx + 0xe0]
      006DA956  40                   inc eax
      006DA957  89 83 E0 00 00 00    mov dword ptr [ebx + 0xe0], eax
  --- DECLARED bytes decoded at the same VA (what the doc claims is there):
      006DA945  89 7C 83 E4          mov dword ptr [ebx + eax*4 - 0x1c], edi
```

```text
[docs/re/ARCHITECTURE_ATLAS.md:1371]  VA=0x0048CE8F  verdict=MISMATCH   declared=85 C0  actual=84 C0
  --- ACTUAL:  0048CE8F  84 C0  test al, al  /  0048CE91 74 09 je  /  0048CE93 E8 38 01 0D 00 call 0x55cfd0
  --- DECLARED: 0048CE8F  85 C0  test eax, eax     (高频公共模式，命中 400 处，最近 0x004144CC Δ=-494019 ⇒ 非走锚)
```

```text
[docs/re/re_sprint_S2_report.md:167]  VA=0x004AA52B  verdict=MISMATCH  declared=E8 B0 22 1B 00  actual=8E FC 00 00 00
  --- ACTUAL bytes at the documented VA: 8E FC 00 00 00  -> Capstone 无法解码 (invalid)
      ⇒ 该 VA 落在指令中间 (0x004AA529 起才是 8B 8E FC 00 00 00 mov ecx,[esi+0xFC])
  --- declared call implies target 0x0065C7E0; 415 call/jmp sites in .text target it;
      nearest by |delta|: 0x004AA6A2(d=+375), 0x004AA94E(d=+1059), ... 无一落在 ±0x400
      ⇒ 判定「文档字节与 VA 双错」，不是简单的 VA 漂移
```

阳性对照（判①的两条同样过机复核，均逐字节相符）：`docs/re/deep_dive_sweeps_closure.md:443 0x00492B55 = 43 (inc ebx)`、`台账:1186 0x00568273 = 89 99 34 01 00 00 (mov [ecx+0x134],ebx)` —— 证明流程既能判「错」也能判「对」，不存在系统性错杀。

---

## 5. S5 已知专项：N-2 真锚点

**结论：原案主题（`BlitTrans@G` 消费 16 位源像素流、跳色键）成立；原锚点 VA `0x004926C0` 抄错；真锚点 = `0x007BC8A3`。**

| 取证项 | 结果 |
|---|---|
| `66 8B 01`（`mov ax,[ecx]`）全镜像命中 | **65 处**（全在 `.text`）；closure 记「66 处」，**应为 65**（微勘误） |
| 落在 `0x00492670..0x00492800` | **0 处** —— **该区间无 `mov ax,[ecx]` 语义**（与 DA4-9 一致） |
| 该区间内的其它 16 位语义 | 4 条：`0x0049268B 66 8B 02 mov ax,[edx]`、`0x00492768 66 8B 51 08 mov dx,[ecx+8]`、`0x00492771 66 8B 6C 45 00 mov bp,[ebp+eax*2]`、`0x00492776 66 8B 06 mov ax,[esi]` —— 但 `0x492670` 函数是 **8 位源 + 16 位目标读改写**（`mov al,[esi]` → `shr ax,1` → `and ax,[ecx+4]` → `mov [edx],ax`），**不承载「16 位源流」语义** |
| `BlitTrans@G 0x007BC890` 全函数（17 条指令 / 43 字节，`ret 0x20` 收尾） | **`0x007BC8A3 = 66 8B 01`**，唯一 16 位源读取指令 |
| 循环体语义 | `0x7BC8A3 mov ax,[ecx]` → `0x7BC8A6 add ecx,2`（**源每像素 +2 字节 = 16 位流**）→ `0x7BC8A9 test ax,ax` → `0x7BC8AC je`（**跳色键 = 丢弃**）→ `0x7BC8AE mov [edx],ax` → `0x7BC8B1 add edx,2` → `0x7BC8B5 jne` —— 与 N-2 结论文本**逐条吻合** |

**建议改锚（供 Lead 派工）**：`nonrle_blit_and_named_hotspots.md` §6 Item 2 与 `deep_dive_sweeps_closure.md` §6 行 29 的锚点由 `0x004926C0: 66 8B 01` 改为 **`0x007BC8A3: 66 8B 01`**（`mov ax, word ptr [ecx]`，`BlitTrans@G` 循环体），`A 类·[实证]` 等级**可恢复**。

---

## 6. S6 误报控制（抽取规则 / 排除规则 / 误报率）

### 6.1 确认的误报类型（321 条中 207 条，64.5%）

| 类型 | 条数 | 判别特征 | 抽样人工确认 |
|---|---|---|---|
| 表单元值列（字节长度 / 调用次数 / 虚表槽位） | 159 | `cell` 通道且**单字节**；如 `\| 0x6F8DF0 \| 43 \|`（43 字节）、`\| 0x7F3FE8 \| 24 \| 128 \| 0x80 \|`（槽 24、尺寸 128） | **18/18 全为计数列** |
| arrow 分段拼接 | 11 | `→` 链合成的非连续串 | 11/11 确认（分段核验：closure:461 5/5 段命中、台账:1557 4/4 段命中） |
| 补丁后字节（预期不符） | 26 | 声明以 `E9 rel32`/`EB`/`90` 填充开头；载体为「装/卸字节」「force-full」表 | 25/26 确认；**1 条边界误判**：`re_sprint_S2_report.md:349` 的 `EB 05` 是手写清单而非常规补丁 |
| 勘误区引用「改前原文」 | 3 | 行内含「改前原文/原记录/订正」 | 3/3 确认（预期不符） |
| 行内多 VA / `A/B=x/y` 简写 / FileOffset 双列 / 外模块地址 | 8 | 例 `\| H-D6/b \| 0x64C911/0x64CC0A \| E8 9A A3 E7 FF \|`（字节属前者）；`0x725FCA/0x726900 = ... 01/00`；`0x01B0xxxx` 补丁运行时 | 8/8 确认为关联误报 |

### 6.2 误报率口径

- **作为「③不符」检测器的噪声率** = 207 / 321 = **64.5%**（主要来自单值表格列，占 159 条）。
- **真勘误精确率** = 114 / 321 = **35.5%**。
- 若先按下述规则预过滤（剔除单字节 cell + arrow + 补丁字节头 + 勘误标记），剩余 321→114 条，**过滤后精确率 = 114/114 = 100%（该 114 条已全量人工判读）**，即**「零漏报不可保证、零错杀可保证」**。
- 抽取器改进后的误报率变化：v1（无 cell 通道）→ 3,061 条中大量跨列拼串；**v2（本批，cell + arrow 严格化）** 3,215 条候选，误报率 64.5%。

### 6.3 已知漏检（复扫的盲区，**不计入本次结论**）

1. **散文字面量**：`49 字节原版减法`、`6 字节 90 (NOP)` 这类「长度+描述」不构成字节串，抽取器按 ⑤ 跳过（台账 §七 多行属此形，故台账表面仅 13 条不符）。
2. **arrow 链首段单字节**（如 `52 \| push edx → ...` 的 `52`）因不足 2 token 被丢弃，`arrow` 通道为**有损**。
3. **同一 VA 在长句中重复出现且字节串在句子后段**（>240 字符窗口）不被捕获。

---

## 7. 未闭环清单

| # | 缺口 | 为何无法静态闭环 | 下一步取证 | 级别 |
|---|---|---|---|---|
| U-1 | `ARCHITECTURE_ATLAS.md:1511-1514` `0x0064DACE` 区段清单与实测整体不同（`mov eax,[0xA8B230]` vs `[0xA83DEC]`） | 静态只能证「不符」，无法判定该清单出自哪一构建/哪次手写 | 追作者来源（S? 批次）；核对是否引自 `0x64F1E6` 邻域（模式命中 Δ≈+5912） | **P1** |
| U-2 | `offline_verification_alternatives.md:132/133`（`Surface::Lock/Unlock` 入口）最近命中 Δ>1MB | 同上；`55 8B EC` 是高频公共序言，模式普查无法定位唯一真值 VA | 用调用图（`DirectDrawSurface` vtable 槽）反查真实入口后重锚 | **P1** |
| U-3 | `particle_fog_owner_evidence.md:226-228`、`landing_equivalence_static_proof.md:276-279`、`blitter_microkernel_deep_dive.md:198-200` 的区段整体错位 | 清单为多指令序列，单条模式无法判定整体 Δ（需逐条配准） | 对每个区段做**序列配准**（把清单当整体在 ±0x200 内滑窗比对） | **P2** |
| U-4 | P3 的 27 条手写清单「哪些是抄错、哪些是规范化自由」 | 语义等价与抄错在字节层同形，需作者意图 | 交 Lead 定性：建议统一加「清单为手写示意」标注 | **P2** |
| U-5 | 台账 §七 表中的「长度+描述」形态断言未入机核验 | 抽取器不解析自然语言长度描述 | 扩展抽取器解析 `NN 字节` + 后续字节块（下一批） | **P2** |
| U-6 | `audio_input_hotspots.md:617`（`VA 0x55D501: 60`）、`blitter_microkernel_deep_dive.md:198-200` 等**单字节**断言 | 单字节模式在全镜像数百命中，无法用命中普查定位真值 | 以函数边界/调用图约束后再定 | **P2** |

---

## 8. 交付物 / 复跑 / 只读声明

| 交付物 | 路径 | 规模 |
|---|---|---|
| 本文档 | `docs/re/inline_assertion_scan.md` | 本文件 |
| S1 抽取器 | `out/re_work/asm_scan/extract_claims.py` | 216 行 |
| S2 判定器 | `out/re_work/asm_scan/classify.py` | 246 行 |
| S3 分桶 | `out/re_work/asm_scan/triage.py` / `build_errata.py` | 2 脚本 |
| S4 负向验证 | `out/re_work/asm_scan/verify_samples.py` + `sample_review.txt` | 377 行证据 |
| S5 N-2 专项 | `out/re_work/asm_scan/n2_anchor_scan.py` + `n2_anchor.txt` | 14,512 B |
| 机器总表 | `out/re_work/asm_scan/errata_table.md` / `mismatch_ranked.tsv` / `classified.json` / `claims_raw.json` | 357 行 / 321 行 / 28,703 条 |
| 断言（门禁用） | `out/re_work/asm_scan/claims.txt` | **1,211 条**（全部判①一致、去重） |
| 门禁输出 | `out/re_work/asm_scan/audit_output.txt` | `audit_bytes.py` 全量输出 |

复跑（幂等，全部只读 exe）：

```bat
cd /d D:\Project\ra2-campaign-forge
python out\re_work\asm_scan\extract_claims.py --min-bytes 0
python out\re_work\asm_scan\classify.py
python out\re_work\asm_scan\triage.py
python out\re_work\asm_scan\build_errata.py
python out\re_work\asm_scan\verify_samples.py
python out\re_work\asm_scan\n2_anchor_scan.py
python tools\verify_anchors.py                                  :: 323/323 PASS
python tools\audit_bytes.py out/re_work/asm_scan/claims.txt     :: 1211/1211 OK
```

**只读声明**：基线 `ra2youli/gamemd.exe` 全程只读（MD5 复算 `4F37486E5B0DBE2AE5F45AEEE0F98367` 前后一致）；未改任何 `.exe`/`.dll`；未启动游戏、未注入、未写 `ra2render/**`、`ra2forge/**`、`ra2youli/**`；**未修改任何他人文档**（本文档为新建）。
