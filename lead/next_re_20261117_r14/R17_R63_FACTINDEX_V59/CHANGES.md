# CHANGES.md — FACT_INDEX v5.8 → v5.9（充分性修法落地）

基底 v5.8（54 条）。条数不变，改 **4 行**：`F01`（evidence_paths）、`F19`（加锚）、`F27`（加锚）、`F29`（limitations）。

## 0. 先纠正上一轮的一项数据：9 条 PARTIAL 里 5 条被驳回

v5.8 的充分性审计判 9 条 PARTIAL。我逐条复算 gap 描述（§2.12 规则 D），结果：

| 条目 | 审计判定 | 我的复算 | 依据 |
|---|---|---|---|
| `F31` | PARTIAL | **REFUTED** | `R17_R50_ADJ_PSELF\VERDICT.md` §6：「`F31 -> keep the prohibition, replace the reason: "COL has no pSelf field (5-dword layout); never test a vtable start by pSelf self-reference"`」——与 statement 几乎逐字相同 |
| `F04` | PARTIAL | **REFUTED** | `R17_LEDGER_1062\SECTION.md(事项1)`（含「308」）**本身就在 F04 的 evidence_paths 里**；审计把「在自己的锚里找到」误报成锚位偏移 |
| `F10` | PARTIAL | **REFUTED** | `1065\SECTION.md` 第 1 项原文即有「函数体长度 56 字节（`0x5657A0`–`0x5657D8`，`0x38`）；区间内唯一 `ret` 在 `0x5657D5`，字节 `C2 04 00` 即 `ret 4`」 |
| `F21` | PARTIAL | **REFUTED（过严）** | `R35\REPORT.md` Q3 有完整逐 site「返回值去向」表，该主张已由第一锚覆盖；`evidence_paths` 不要求每个锚覆盖每条主张 |
| `F24` | PARTIAL | **REFUTED** | 锚就是 `R16_MEASURE_EVID675\REPORT.md`，实测含 `## 7`=1、`file_kind`=2、`首版`=2、`假阳`=4 ⇒ 前提**在锚内**，只是 statement 未写 |
| `F01` | PARTIAL | **部分成立** | (1)「COL 恰 5 dword 无直说」→ REFUTED（R50 §6 明写）；(2)「954 的限定语在锚外」→ **CONFIRMED**（该语在 archive「第 20–21 轮」段，而 F01 的锚是「第 13 轮」段） |
| `F19` | PARTIAL | **CONFIRMED** | `AUDIT_FI_V5` 内「10 处」= 0；原文在 `R17_AUDIT_FACTINDEX\missing_entries.md` |
| `F27` | PARTIAL | **CONFIRMED-BUT** | 68 同源成立；但 Lead 已按字节复现 68 ⇒ 第二源存在、只是未入锚 |
| `F29` | PARTIAL | **CONFIRMED** | `§13.3` 原文「即对 `[this+4]` 调 `InterlockedIncrement` 的真实 AddRef」——字节只给 `call [0x7E11C8]`；且 `0x6C2AC0` 在 `R14_COMMON` **0 命中** |

⇒ **净账：9 条 PARTIAL = 5 驳回 + 1 部分成立 + 3 成立（其中 1 条可解）。** 审计的「判定」倾向过严、且 gap 引文有定位错误；但**它确实挖出了 2 条真缺陷**（F19 的正控不在锚内、F29 的推断措辞当事实）。

**⚠ 我本轮也犯了一次错并已更正**：上一轮我判 F24「引文不实」，是**查错了文件**（查 `R16_AUDIT_EVID675` 而非锚本身 `R16_MEASURE_EVID675`）。复算后确认审计引文属实。

## 1. 本轮落地的 4 处修法

| fact_id | 改动 | 依据 |
|---|---|---|
| `F01` | `evidence_paths`：`BOARD_ARCHIVE.md(R17 第 13 轮 段)` → `(R17 第 20–21 轮 段)` | 「954 为『主 COL』数（每类一个 lowest-VA 主 COL）」与「COL 恰 5 dword」的上下文都在第 20–21 轮段（C-1 裁决段），第 13 轮段三者皆无 |
| `F19` | 加锚 `R17_AUDIT_FACTINDEX\missing_entries.md` | statement 写「正控：`E8`→`0x47C620` 得 10 处」，该正控原文实际在此文件（「`0x47C620 得 10`」命中）；原锚内「10 处」= 0 |
| `F27` | 加锚 `R17_R56_FACTINDEX_V53\lead_byte_checks.tsv` | 68 原为 4 处同源复制；我已在第 18–19 轮按「紧邻 `68 imm32` + `E8`→`0x7C978A`」判据字节复现 68，该产物即第二源 ⇒ **加锚而非降级** |
| `F29` | `limitations` 追加：`0x6C2AC0` 的「InterlockedIncrement」是 §13.3 的**推断措辞**（字节只给 `call [0x7E11C8]`），引用时须写明该词未经字节证实 | 见上表 F29 行 |

## 2. 未落地的 3 条（说明理由，不假装已修）

- **`F24`**：前提在锚内，缺的是 statement 措辞精度（未写「正控首版曾被推翻」）。改 statement 会动到 `[已证]` 条目的正文语义，牵涉再审计，**本轮不动**，登记待议。
- **`F29` 的 statement**：同样只是加 `limitations` 说明，未改正文措辞（正文仍写「是 InterlockedIncrement 真 AddRef」）。若要精确化需改正文，同样待议。
- **`F04`/`F10`/`F21`/`F31`**：复算后判为**审计误报**，无缺陷可修。

## 3. v5.9 核验基线（`anchor_check.txt`，退出码 0）

| 项 | v5.8 | v5.9 |
|---|---:|---:|
| 路径项 | 138 | **140**（+2 个新锚） |
| 文件存在 | 138/138 | **140/140** |
| 带锚点 | 116 | **116** |
| 　机械核验通过 | 101 | **101** |
| 　节号体例通过 | 15 | **15** |
| 　人工 / 未核验 / 裸目录 / 目录+锚 | 0/0/0/0 | **0/0/0/0** |
| **MISS** | 0 | **0** |

## 4. 未改动项

- `grade` 零改动：仍 `[已证]` 27 / `[静态推断]` 1 / `[流程]` 24 / `未取得` 2；
- 条数 54；`fact_id` 连续 F01–F54；其余 50 行逐字节未动。
