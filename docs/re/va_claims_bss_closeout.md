# R-VA-BSS — 64 条无主悬空 BSS 关账报告

日期：2026-09-30 · 基线：`ra2youli/gamemd.exe` MD5 `4f37486e5b0dbe2ae5f45aeee0f98367` · ImageBase `0x00400000`
产物：`out/re_work/re_sprint/R_va_bss/` · 工厂：T33/T36 v2（`R_fac_fix/factory_fix.py` + `claim_emit.py`，只读引用）
只读依赖：`R_claims_fac/**`、`tools/audit_bytes.py`、`atlas_va_crosscheck.json`（未改动）

---

## 1. 范围界定

| 项 | 值 |
|---|---|
| ATLAS dangling 全量 | 482 |
| 其中有历史 claim（upgrade 桶） | 418 |
| **无主（无历史 claim）悬空** | **64** |
| 其中 raw 可读 | 0 |
| 其中 BSS / virtual（无 raw） | **64（100%）** |
| 段分布 | 全部 `.data(virtual)` |

无主判定 = `load_prior_claims()` 全库扫描 `out/re_work/**` + `docs/re/anchor_claims.txt` 的 `0xVA = HEX` 断言后，该 VA 零命中。64 条与「真实剩余无主悬空约 64 条全 BSS」口径一致，本批一次关账，无剩余。

## 2. 工厂路径（v2 五补丁全覆盖）

| 补丁 | 本批落点 |
|---|---|
| P0 intake 分桶 | 64/64 落入 `new` 桶（upgrade=0），无历史窗需 merge |
| P0 pick_anchors F3 强制 | 全部锚点过 `sf._covered_by_imm`；**0** 条盲窗回退 |
| P0 全拒 → bss_region | 1 条降级（见 §4） |
| P1 paired emit | 63 条 `bss_ref` 均发出 region 行 + 锚点行 |
| P1 高 xref 双锚点 | 12 条（`n_abs_text+n_call≥50`）发出读/写双锚点 |
| P2 kind 扩展 | 全部 `bss-global`（`.data(virtual)` 无 raw） |

文本形态（`claims_factory_spec_v2.md` / audit_bytes v3）：

```
bss 0x0087E180 = virtual  # seg=.data(virtual) | kind=bss-global | type=bss_region | [待实测]
0x00403ED6 = B9 80 E1 87 00  # bss-xref -> 0x0087E180 | type=bss_ref | [待实测]
```

## 3. 自检（全绿）

| 检查 | 结果 |
|---|---|
| `claim_emit.validate_record` | 64 / 64，0 bad |
| txt 重解析 | 75 byte + 64 bss = **139** 行，0 bad |
| `tools/audit_bytes.py out_bss_claims.txt` | **139 / 139 OK**（bytes 75 OK + BSS 64 BSS-OK），MISMATCH/NOREAD = **0** |
| 锚点离线复算 | 75/75 文件字节一致 |
| F3 imm 覆盖 | 75/75 |
| `covers_abs_at` 4 字节 == `pack(va)` | 75/75 |
| MD5 门禁 | 一致 |
| P0/P1/P2 断言 | 全部 ok |

明细见 `selfcheck.json`、`selfcheck_audit_bytes.json`。

## 4. 统计

### 4.1 类型 / 分级

| type | 条数 | 说明 |
|---|---|---|
| bss_ref | 63 | 有 F3 实证锚点，region+anchor 成对 |
| bss_region | 1 | 无 imm 覆盖锚点，降级 |
| **合计** | **64** | |

| grade | 条数 | 占比 |
|---|---|---|
| [待实测] | 64 | 100% |

BSS 记录 body 一律 `[待实测]`（锚点侧可实证，BSS 本体需运行时观测）；`anchor_grade=[实证]` 记在 notes。

### 4.2 锚点形态

| 项 | 值 |
|---|---|
| 带锚点 | 63 / 64（98.4%） |
| 双锚点（高 xref） | 12 |
| 锚点指令形态 | write 40 · mov 17 · read 18 · alu-imm32（op_05/0D/15/35/3D）53 · push 8 · lea 2 |
| 读/写多样性 | write 42 · read 28 · mov 15 · other 53 |

高 xref 双锚点 VA：`0x0087E8A4, 0x0087F658, 0x0087F770, 0x0087F7E8, 0x00886B88, 0x00886FA8, 0x008871E0, 0x00887314, 0x00887324, 0x00887640, 0x00887644, 0x0089F688`。

### 4.3 降级个案

| VA | 笔记 |
|---|---|
| `0x008A0000` | `no imm-covered anchor (F3 rejected 5/5 hits)` — pack(va) 在 .text 有 5 处命中，但全部不在任何 imm32/abs32 覆盖内，按 P0 一律不作锚点，降级 `bss_region` |

### 4.4 VA 分布（区间条数）

| 区间 | 条数 |
|---|---|
| `0x0087xxxx` | 16 |
| `0x0088xxxx` | 10 |
| `0x0089xxxx` | 16 |
| `0x008Axxxx` | 9 |
| `0x008Bxxxx` | 13 |

全距 `0x0087E180` – `0x008B4204`，均落在 `.data` 虚拟段（BSS），无一进入 `.text`/`.rdata` raw 区。

### 4.5 合并 / 冲突

| merge_status | 条数 |
|---|---|
| none（无历史窗，new 桶） | 64 |

BYTE_CONFLICT = 0，WINDOW_VARIANT = 0（本批无主，无历史 claim 可冲突）。

## 5. 产物清单

| 文件 | 说明 |
|---|---|
| `out_bss_claims.jsonl` | 64 行结构化记录（schema 可校验） |
| `out_bss_claims.txt` | 139 行 audit_bytes v3 兼容文本（paired emit） |
| `out_bss_summary.json` | 汇总统计 |
| `selfcheck.json` | 自检判定（ok=true） |
| `selfcheck_audit_bytes.json` | audit_bytes 逐行明细（139 行全 OK） |
| `run_bss_closeout.py` | 关账流水线（只读 import v2 工厂） |

## 6. 关账结论

64 条真实剩余无主悬空 **全部为 BSS**，经 v2 工厂一次关账：63 条 `bss_ref`（F3 锚点 + paired emit，12 条双锚点）+ 1 条 `bss_region`（F3 全拒合规降级）。audit_bytes 139/139 通过，schema 0 bad，锚点复算 75/75（含 F3 与 pack(va) 双检），MD5 门禁一致。无主悬空 BSS 缺口 **清零**。
