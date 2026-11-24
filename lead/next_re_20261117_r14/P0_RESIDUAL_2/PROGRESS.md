# P0-RESIDUAL-2 · PROGRESS

## 结论（T4）：档 (c) — 通道仍不完备，剩余不可判 M=5,598 个（已枚举，不再给区间）

一句话：**新通道独立发现 20 个新入口（并入后分母 14,495→14,515），但正对照被独立 oracle `0x7775C0` 反证有偏，通道仍不完备，余 5,598 个 UNDECIDABLE 已逐地址枚举于 ENUM.tsv。**

| 分级 | 结论 | 证据路径 |
|---|---|---|
| `[已证]` | SHA256 匹配；`.text=[00401000,007E038D)`；全网格 253,753；N_pool=7,228；ENUM 全集 5,656；三项对照数字 | `EVIDENCE/stats.json`、`EVIDENCE/baseline.tsv`、`EVIDENCE/recall.tsv`、`EVIDENCE/negative.tsv` |
| `[已证]` | coverage 当场截面 14,495（mtime 17:47:09 / 2,813,399B）；2 条并发新增未误报；收尾复核 STABLE | `EVIDENCE/stats.json`(cov_meta/crosscheck)、`EVIDENCE/coverage_snapshot_14495.tsv`、`EVIDENCE/oracle_and_crosscheck.tsv` |
| `[已证]` | oracle `0x7775C0` 被 F/G 双双漏检（首字节 0x51、dataptr=0） | `EVIDENCE/oracle_and_crosscheck.tsv` |
| `[静态推断]` | 裁定 FUNC 20 / NOT_FUNC 38 / UNDECIDABLE 5,598 | `ENUM.tsv`、`work/pipeline.py` |
| `[静态推断]` | 2,026 个 FPU 叶函数为"无人引用但真存在"入口（反证通道不完备） | `EVIDENCE/gap_candidates.tsv`(fpu 列)、`work/inspectfpu.py` |
| `[静态推断]` | 通道 H 在本 PE 零新增（无 .pdata/LOAD_CONFIG/TLS） | `EVIDENCE/channel_H_meta.tsv`、`work/recon.py` |
| `[未证]` | 20 条新 FUNC 的具体语义/类名（本卡只裁入口） | `coverage_delta.tsv`(grade=[未证]) |

## 给审计员的 3 个核心数字（可独立复算）

**① 新通道独立发现的新入口数 = 20**（`coverage_delta.tsv` 20 行，全为 `push imm32; call; …; ret` 的静态初始化 thunk）
复算：`python work/pipeline.py` → `coverage_delta.tsv` 行数；或 `Import-Csv ENUM.tsv | ? verdict -eq FUNC`。判定=四项判据全过 ∧ 不在已知 body ∧ 不在 coverage。分母：14,495 + 20 = **14,515**（推导：当前 coverage 截面 14,495 ∪ 20 个新入口，去重 0，全在 S22；`grade=[未证]`故不改 [已证] 计数）。

**② 正对照召回率 = 86.45%（F 单项）/ 99.62%（F∪G），但为有偏对照**
复算：`EVIDENCE/recall.tsv`（gate476/resid1096/combined 三行）；或脚本重跑。86.45%=1359/1572（严格四项），99.62%=1566/1572（F∪G）。**关键反证**：独立 oracle `0x7775C0` 在 coverage 却 `chF=False/dataptr=0`（`EVIDENCE/oracle_and_crosscheck.tsv`），证明高召回源于样本由旧通道筛出，不能当完备性证据。

**③ 基线通过率 = leaf-shape 空判据 95.2%（随机 16B）/ 严格 chF 3.96%（随机 16B）**
复算：`EVIDENCE/baseline.tsv`；同质基线（atlas 体内部∧前驱 TERM）=8.83%（n=1,404，与审计 f_fp2 吻合）。leaf-shape 在随机对齐地址 95.2% 恒真 ⇒ 弃用；严格 chF 特异。

## 三组对照总判定
见 `COUNTERFACTUAL.md`：基线 ✅（据基线弃用空判据）／正对照 ❌（oracle 反证通道不完备）／负对照 ✅（0/1 真实假阳性，0x4824D4 正确拒绝）。⇒ 取 (c)。

## 写域 / 只读纪律
- 写：仅 `lead\next_re_20261117_r14\P0_RESIDUAL_2\`（含 EVIDENCE\、work\）。
- 只读：gamemd.exe（SHA 现场校验）、COVERAGE\（未改；并发改动由 M2 所为，Lead 裁定用 14,495）、各前序卡。未改游戏文件/台账/COVERAGE；未 git commit。
- 工具：Python 3.12.10 / capstone 5.0.7（skipdata=True）/ pefile 2024.8.26；未用 Ghidra。

## 交付
`ENUM.tsv`（5,656 全量）· `coverage_delta.tsv`（20 FUNC）· `CHANNELS.md` · `COUNTERFACTUAL.md` · `UNKNOWNS.md` · `DISAGREE.md` · `EVIDENCE\`（不截断）· `work\`（`pipeline.py` 可复跑）。复跑：`python work/pipeline.py`。
