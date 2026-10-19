# R-VA-BATCH run1 — 剩余悬空 VA 批量补证试跑

日期：2026-09-30 · 基线：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000`
产物：`out/re_work/re_sprint/R_va_batch/` · 只读依赖：T17 `R_claims_fac/**`、T4 `R_va_claims/**`、`tools/audit_bytes.py`（未改动）

---

## 1. 范围与选样

| 项 | 值 |
|---|---|
| ATLAS dangling 全量 | 482 |
| 扣除 T4 `sample80` | 402 |
| 本批实跑 | **80**（目标 60–100） |
| 优先子系统外（非 Render/Fog/Cell/SuperWeapon/Trigger） | 57 / 80 |
| 有 xref 证据 | 76 / 80 |

选样波次（`batch_run1.py:select_batch`）：
A. 优先子系统外且 xref≥1 → 全收（57）；
B. 补 BSS 无 raw（bss_ref schema 覆盖）→ 23（含子系统内）；
C. 高 xref raw → 0（A/B 已占满 80）。

## 2. 产出格式

| 文件 | 说明 |
|---|---|
| `claims_batch.jsonl` | 80 行，`claim_schema.json` 可校验 |
| `claims_batch.txt` | 116 行，`audit_bytes.py` v3 兼容（含 `bss 0xVA = virtual` 区域行 + 锚点字节行） |
| `out_batch_summary.json` | 覆盖率/冲突/分级/BSS 比例 |
| `batch_run1.py` | 批次流水线（复用 T17 模块，只读 import） |

文本形态（§2.2）：
- raw：`0xVA = HEX  # … | type=raw | [grade]`
- BSS：`bss 0xVA = virtual  # … | type=bss_region | [grade]` **并列** 锚点行 `0xSITE = HEX  # bss-xref -> 0xVA | type=bss_ref | [grade]`

## 3. 自检结果（全绿）

| 检查 | 结果 |
|---|---|
| `claim_schema.py validate claims_batch.jsonl` | 80 / 80，0 bad |
| `tools/audit_bytes.py claims_batch.txt` | **116 / 116 OK**，0 MISMATCH |
| 窗宽归一重算（45 条有历史窗） | 45/45 为 `WINDOW_VARIANT`，**0 真冲突** |
| 锚点离线复算（34 条 bss_ref） | 34/34 文件字节一致；`covers_abs_at` 4 字节 == `pack(va)`；全部被 imm32 覆盖（F3） |
| MD5 门禁 | 与工厂基线一致 |

历史窗宽集合（合并后一律拉到 `W_std=16`）：

| width-set | 条数 | 判定 |
|---|---|---|
| (8, 16) | 30 | 假冲突，已合并 |
| (4, 16) | 14 | 假冲突，已合并 |
| (3, 8, 16) | 1 | 假冲突，已合并 |

## 4. 统计

### 4.1 分级

| grade | 条数 | 占比 |
|---|---|---|
| [实证] | 44 | 55.0% |
| [推演] | 1 | 1.3% |
| [待实测] | 35 | 43.8% |

### 4.2 类型 / BSS 比例

| type | 条数 |
|---|---|
| raw | 45 |
| bss_ref | 34 |
| bss_region | 1 |

- **BSS 比例 = 35 / 80 = 43.75%**（对应 T4「65 条无 raw」缺口的补证路径）
- BSS 中 34/35 有可复算锚点（97.1%）；1 条无 imm 覆盖锚点 → 降级 `bss_region`
- 仅 1 条高 xref BSS 发出第 2 锚点（读/写各一）

### 4.3 合并与冲突

| merge_status | 条数 |
|---|---|
| WINDOW_VARIANT（假冲突合并） | 45 |
| none（无历史 claim） | 35 |
| BYTE_CONFLICT（真冲突） | **0** |

### 4.4 kind

| kind | 条数 |
|---|---|
| bss-global | 35 |
| code | 31 |
| ptr-or-data | 14 |

## 5. 工厂规则修补建议（只记本文档，未改 T17 产物）

### P0 — intake 把「已有 claim」直接跳过，窗宽归一永不触发

`factory_batch.py:load_existing_claim_vas` 把凡出现在 claim/anchor 文本里的 VA 从队列剔除。
实测：dangling 482 中 417 条已在 `claims_va_p1.txt`（多为 4/8B 短窗），扣除后只剩 64 条，**且全是 BSS**。
后果：runbook §4.1「400 条队列」与现实不符；步骤 6 的 `classify_pair` / 假冲突合并永远空跑。
本批改为：**保留有历史 claim 的 VA**，强制重采 16B 并做 `merge_windows`（45 条假冲突全部合并，0 真冲突）。
建议：§4 step 1 拆成两桶 —— `upgrade/merge`（已有短窗）与 `new`（无 claim）；`--limit` 对两桶分别配额。

### P0 — `pick_anchor` 盲目 5 字节窗回退违反 §2.4「指令立即数覆盖」

`factory_batch.py:pick_anchor` 在 imm32 命中失败时回退 `site=hit-1` 的 5B 窗，标 `form=window / [推演]`，**未跑 F3**。
实测反例：`0x008A0000` 的 `pack` 字节 `00 00 8A 00` 在镜像出现 5 次，**0 次被任何 imm32 覆盖**（落在 `jbe` 指令流/数据巧合字节）。
若接受回退锚点，`bss_ref` 不可称为「引用点指令断言」。
建议：回退必须过 `sf._covered_by_imm`；全拒则出 `bss_region` + `F3 rejected n/n hits` 注记（本批已如此）。

### P1 — `emit_text(bss_ref)` 只出锚点行，不出对象区域行

`claim_schema.emit_text` 对 `bss_ref` 仅打印 `0xSITE = HEX`。`audit_bytes.py` 只有两态：字节断言 / `bss 0xVA = virtual`。
缺少区域行时对象 VA 的「虚拟存在」从不被审计。
建议：`bss_ref` 落盘时**成对输出** `bss 0xVA = virtual` + 锚点行（本批 txt 116 行 = 36 区域 + 80 锚点/原始）。

### P1 — 高 xref 第二锚点未实现

spec §2.4「高 xref（≥100）建议 2 条（读点+写点）」。`factory_batch.process` 只存单个 `anchor`。
本批 `pick_anchors(..., prefer_two)` 在 `n_abs_text+n_call≥50` 时取读/写各一，仅 1 条命中阈值（其余 BSS 落在优先子系统外、xref 中低）。
建议：schema 增加 `anchors: [anchor]` 数组，或保留 `anchor_extra` 并在测试中覆盖。

### P2 — `kind_of` 首字节启发式误判入口

`0x006F93C1`（ATLAS 引用的指令内部点，非函数入口）被标 `kind=code` 且 xref 全 0 → `[推演]`。
同一模式还有若干 `b8 imm32; c3` 尺寸桩（`0x0041C170` 等，返回 `0x6d8/0x1c8/0x148…`），当前标 `code`，更贴 `ret-stub` / `thunk`。
建议：`kind_of` 结合 capstone 线性反汇编入口对齐（或 `window_norm.prologue_window`）再定 kind；thunk 增加 `size-thunk` 类。

### P2 — 优先级用的 `xref_census.json` 是 T4 未过滤计数

T4 `xref_census.json` 的 `n_abs_text` 未全开 F1–F6（如 `0x008A0000` 被记 1 次 abs_text，过滤后应为 0）。
按该分数排序选样会抬高假引用 VA。
建议：runbook step 3 产出过滤后 census 再排序；或选样阶段先跑 `sf.census_va`。

## 6. 出口判据对照（§4.2）

| 判据 | 本批 |
|---|---|
| 100% 有 type 且 schema 通过 | 是（80/80） |
| BYTE_CONFLICT 有清单且不静默合并 | 是（0 条，全部走 WINDOW_VARIANT 显式合并） |
| BSS 100% ≥1 条可复算锚点 | **34/35**；1 条无 imm 锚点 → `bss_region`（符合降级语义） |
| 窗宽全部 16（或 ≥4 截断） | 是（raw 45×16；BSS window=0） |
| audit_bytes 全 PASS | 是（116/116） |

## 7. 产物索引

- `out/re_work/re_sprint/R_va_batch/batch_run1.py`
- `out/re_work/re_sprint/R_va_batch/claims_batch.jsonl`
- `out/re_work/re_sprint/R_va_batch/claims_batch.txt`
- `out/re_work/re_sprint/R_va_batch/out_batch_summary.json`
- `out/re_work/re_sprint/R_va_batch/selfcheck.json`
