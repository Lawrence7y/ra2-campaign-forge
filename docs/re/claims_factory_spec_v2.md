# Claims Factory Spec v2 — R-FAC-FIX

日期：2026-09-30 · 依据：T33 `docs/re/va_claims_batch_run1.md` §5 五条修补 + T17 `docs/re/claims_factory_spec.md`
基线：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367`，ImageBase `0x00400000`
产出目录：`out/re_work/re_sprint/R_fac_fix/**`（**不改** `R_claims_fac/**` 原件，只读 import）

| 文件 | 职责 |
|---|---|
| `factory_fix.py` | 修补版流水线（P0 intake 分桶 / P0 F3 锚点 / P1 双锚点 / P2 kind+census） |
| `claim_emit.py` | P1 paired `emit_text` + P2 扩展 kind 校验 |
| `selfcheck_t33.py` | T33 80 条回归门禁 |
| `out_t33_claims.{jsonl,txt}` | 回归产物 |
| `out_t33_summary.json` / `selfcheck.json` | 统计与自检 |

---

## 1. 修补对照（T33 §5 → v2 规则）

### P0-A — intake 分 `upgrade` / `new` 桶（窗宽归一必须可触发）

**原状**：`factory_batch.py:load_existing_claim_vas` 把凡有 claim 的 VA 从队列剔除。
482 dangling → 扣 417 已有 claim → 仅剩 64 条且全是 BSS；`classify_pair` / 假冲突合并永远空跑。

**v2**（`factory_fix.split_intake`）：

```
upgrade/merge 桶 = dangling ∩ 已有 claim   (强制重采 W_std=16 + merge_windows)
new 桶           = dangling − 已有 claim   (直接 W_std=16 采样)
--limit-up / --limit-new 对两桶分别配额
```

- 历史 claim 读取跳过自身输出目录（`R_fac_fix`、`R_va_batch`），避免自引用。
- 实测（全量 482）：`upgrade=418  new=64`（对比原工厂 effective queue=64）。

### P0-B — `pick_anchors` 强制 F3 imm 覆盖，禁止盲窗回退

**原状**：imm32 命中失败时回退 `site=hit-1` 的 5B 窗，标 `form=window / [推演]`，未跑 F3。
反例 `0x008A0000`：`pack` 字节出现 5 次，0 次被任何 imm32 覆盖。

**v2**（`factory_fix.pick_anchors`）：

1. `.text` 内 `find(pack(va))` 命中必须 `sf._covered_by_imm`（F3）通过，否则丢弃；
2. **不存在** `form=window` 回退路径；
3. 全拒 ⇒ `type=bss_region` + 注记 `no imm-covered anchor (F3 rejected n/n hits)`。

### P1-A — `emit_text(bss_ref)` 成对输出区域行

**原状**：`claim_schema.emit_text` 对 `bss_ref` 只打印锚点行 `0xSITE = HEX`，对象 VA 的
「虚拟存在」从不被 `audit_bytes` 审计。

**v2**（`claim_emit.emit_lines`）：

```
raw        -> 0xVA = HEX                          （1 行）
bss_region -> bss 0xVA = virtual                  （1 行）
bss_ref    -> bss 0xVA = virtual                  （区域行）
              0xSITE = HEX  # bss-xref -> 0xVA    （锚点行）
              [0xSITE2 = HEX  # bss-xref -> 0xVA] （P1-B 第二锚点，可选）
```

文本仍兼容 `tools/audit_bytes.py` v3 两态解析（`bss … = virtual` / `0xVA = HEX`）。

### P1-B — 高 xref 双锚点（可选，已实现）

- 触发：`n_abs_text + n_call >= 50`（spec §2.4 写 ≥100；批次实践 ≥50，本实现取 50）。
- 选取：`pick_anchors(..., prefer_two=True)` 优先 read/write 各一（`A1`/`8B`/`8D` vs `A3`/`C7`/`89`）。
- 落盘：JSON 同时写 `anchor`（主）、`anchor_extra`（次）、`anchors: [..]`（数组）。
  文本在 paired emit 中追加第二锚点行。

### P2-A — `kind_of` 扩展 + 入口对齐

**原状**：首字节启发式把指令内部点（`0x006F93C1`）标 `kind=code`；
`b8 imm32; c3` 尺寸桩（`0x0041C170` 等）也标 `code`。

**v2 kind 词表**（`claim_emit.KINDS`，在原 7 类上扩展）：

| kind | 判定 |
|---|---|
| `size-thunk` | `B8–BF imm32 ; C3`（5+1 字节尺寸桩） |
| `thunk` | `68 imm32 ; C3` |
| `ret-stub` | 首字节 `C3` |
| `mid-insn` | 无严格前言、无 xref、且（落在前指令 imm 域内 或 短回退线性反汇编覆盖本点） |
| `code` | 严格前言签名 **或** 正 xref 证据 |
| 其余 | 沿用 v1（`pe-base` / `bss-global` / `ptr-or-data` / `ptr-or-vtable` / `unknown`） |

严格前言（与 `grade_of` 一致）：`55 8B EC | 53 55 | 56 8B | 57 8B | 8B FF 55 | 33 C0 C | B8 | 83 EC | 81 EC | C3 | C2 | 4D 5A`。

**要点**：`code` 不再由首字节单独决定——必须有前言或 xref 外证；否则降 `mid-insn`。

### P2-B — 优先级用过滤后 census

**原状**：选样排序用 T4 `xref_census.json`（未全开 F1–F6，如 `0x008A0000` 被记 1 次 abs_text）。

**v2**：`process_one` / 选样排序一律使用 `sf.census_va`（F1–F6 全开）产出
`n_call / n_jmp / n_abs_text / n_abs_data`，并在 record `xref` 中落盘该过滤值。

---

## 2. 与 v1 的字段/文本差异

| 项 | v1 (`claim_schema`) | v2 (`claim_emit`) |
|---|---|---|
| `emit_text(bss_ref)` | 仅锚点行 | 区域行 + 锚点行（+第二锚点） |
| `kind` 词表 | 7 类 | + `size-thunk` / `thunk` / `mid-insn` |
| `anchor_extra` | 无 | 高 xref 时写入 |
| `anchors` | 无 | 锚点数组（含主锚点） |
| intake | 丢弃已有 claim | `upgrade`/`new` 双桶 |
| 锚点回退 | `form=window` 5B 窗 | **禁止**；全拒降 `bss_region` |

其余约束（`va` 格式、`covers_abs_at == pack(va)`、`window_width` 一致、grade 三级）与
T17 spec §2 一致，`validate_record` 为 v1 超集。

---

## 3. 自检口径（T33 80 条回归）

`python selfcheck_t33.py` → `selfcheck.json`，对照 `R_va_batch/out_batch_summary.json` + `selfcheck.json`：

| 检查 | T33 基线 | R-FAC-FIX | 判定 |
|---|---|---|---|
| schema validate | 80/80，0 bad | 80/80，0 bad | 对齐 |
| audit 文本可解析行 | 116（含 1 行 bss_region 重复） | **115**（paired 无重复） | 更好 |
| `tools/audit_bytes.py` | 116/116 OK | **115/115 OK** | 对齐（0 MISMATCH） |
| 窗宽归一 | 45 WINDOW_VARIANT / 0 冲突 | 45 / 0 | 对齐 |
| 锚点复算 | 34/34 文件字节一致，F3 覆盖 | **35/35**（含 1 条第二锚点） | 更好 |
| BSS 有锚点 | 34/35 | 34/35 | 对齐 |
| `0x008A0000` | F3 5/5 拒 → `bss_region` | 同左，注记 `F3 rejected 5/5` | 对齐 |
| kind 扩展 | `code` 误标尺寸桩/内部点 | `size-thunk`×7 + `mid-insn`×1 | **改善**（P2） |
| P0 intake | （升级桶空跑） | upgrade=45 / new=35（回归集内） | **改善** |
| 双锚点 | 1 条 | 1 条（`0x00886FA8` 读+写） | 对齐 |

kind 分布对比（80 条）：

| kind | T33 | v2 |
|---|---|---|
| bss-global | 35 | 35 |
| code | 31 | 23 |
| ptr-or-data | 14 | 14 |
| size-thunk | 0 | 7 |
| mid-insn | 0 | 1 |

---

## 4. 出口判据（继承 T17 §4.2，补充 P0/P1 断言）

- 400 条 100% 有 `type` 且 v2 schema 校验通过；
- `BYTE_CONFLICT` 有清单且不静默合并；
- BSS 条目 100% ≥1 条**可复算且 F3 覆盖**锚点；无则 `bss_region` + F3 注记；
- 窗宽全部 16（或 prologue 截断 ≥4）；upgrade 桶 `window_widths` 历史值只作审计；
- `emit_lines(bss_ref)` 必含 `bss 0xVA = virtual` 行（paired 率 100%）；
- `form=window` 锚点数 = 0；
- 选样/统计 xref 一律来自 `sf.census_va` 过滤值。

---

## 5. 禁区与口径

- **禁写**：`out/re_work/re_sprint/R_claims_fac/**`、`tools/**`、台账、看板、`gamemd.exe`、`ra2youli/**`。
- 可写：`out/re_work/re_sprint/R_fac_fix/**`、`docs/re/claims_factory_spec_v2.md`。
- 映射口径与 `tools/audit_bytes.py` v3 一致（段映射，PE 头 `off = VA − ImageBase`）。
- 原 T17 产物 `R_claims_fac/**` 仅只读 import（`window_norm` / `scan_filters` / `claim_schema.grade_of`）。
