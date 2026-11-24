# P0-ADJ4 · PROGRESS（完成）

> 卡号 P0-ADJ4｜目标 `ra2youli\gamemd.exe` 只读（SHA-256 73201CC0…F67476 现场重算一致，ImageBase 0x400000）
> 环境 Python 3.12.10 + capstone 5.0.7（skipdata=True）+ pefile 2024.8.26；`.text=[00401000,007E038D)`。
> 写域仅 `P0_ADJ4\`（含 work/ EVIDENCE/）；未改台账/R14_COMMON.md/coverage.tsv/ra2youli/其它卡/COVERAGE；未 git commit。

## 1 · 核心数字（给审计复算）

| 指标 | 值 |
|---|---:|
| ENUM.tsv 数据行 | 5,656（verdict: FUNC 20 / NOT_FUNC 38 / UNDECIDABLE **5,598**） |
| **UNDECIDABLE 实际总数** | **5,598** |
| 本卡裁定 | **100 行**（address 升序前 100：004011B0..0040B3E0，确定性取样） |
| **本卡 FUNC / NOT_FUNC** | **95 / 5** |
| 正负对照通过 | **5/5 + 5/5 = 10/10** |
| 抽样推广预计可裁 | **≈5,361 / 5,498**（40 行样本 97.5% 强判据；≈137 需 P1） |

## 2 · 判据式（一行说清）

**FUNC ⇔ G1a(16B对齐) ∧ G1b(前驱∈{nop,ret,jmp,int3}) ∧ C1(首字节∉{E8,E9,EB}) ∧ C2(非jcc目的) ∧ C3(首指令∈data/prologue形态∧∉{pop,leave,ret,nop,int3,jmp,call}) ∧ C4(首个push/sub-esp之前无pop/leave/add-esp) ∧ C5(512B内skipdata解码到ret/jmp且无`.byte`)**，缺任一即 NOT_FUNC。所有通道纯字节解码+控制流扫描，**无一条依赖 atlas entry+size**（满足 §6 纪律 1）；capstone skipdata=True（纪律 2）。复跑 `work/criterion.py` → `work/finalize.py`。

## 3 · 正负对照与判据修正（过程如实）

- 阳性 5（从 P0_RESIDUAL FUNC 集等距取：00401BB0/004C1440/005BDC00/00645D10/00729480）：首版 5/5 PASS。
- 阴性 5（从 P0_RESIDUAL NOT_FUNC 集等距取：00403247/004A0242/005EF589/0061DD95/007573D4）：**首版 3/5 FAIL**（00403247、005EF589 被误判 FUNC）。
- **修正**：两失败行均非 16B 对齐——首版把 G1(对齐/前驱) 当"ENUM 已给定"未显式校验。补入 G1a/G1b 为显式通道后重跑，阴性 **5/5**、阳性仍 5/5。修正已固化进 criterion.py 并全量复算。
- 全量复算（`work/validate_full.py`）：历史 FUNC 1057/1096 判对（96.4%），历史 NOT_FUNC 1385/1395 判对（99.3%）；10 FP 全是 `data` 子类浮点表（0x40F220..0x410100，在本批区间外），39 FN 为 C5/C2 严格侧。

## 4 · 100 行裁定摘要

- FUNC 95：FPU 叶（DD/DB 首字节 29 行，如 00403CE0/0040AD90）、mov getter（8B/A1 31 行）、xor 清零（33，8 行）、const 返回（B8/B9，9 行）、push ecx thiscall（51，8 行）、test/cmp/add/lea 短叶（余）。
- NOT_FUNC 5（逐行见 EVIDENCE/NOT_FUNC_DETAIL.tsv）：
  - 00402F80：`call` 开头 + jcc 目的（je@00402F71）+ 首 push 前已 restore → 函数内标签；
  - 00405AB0 / 004063A0：jcc 目的 + 未push先pop → 孤儿尾段/内部分支汇合点；
  - 00407080：`jmp 0x407170` 纯转发桩（首字节 E9）→ stub；
  - 0040A600：`pop edi` 开头（无序言的栈恢复片段）+ jcc 目的 → 孤儿 epilogue。

## 5 · 停机核验（FUNC 率 95% > 90%——先诊断、不凑数）

按 §954 纪律停机诊断：95% 是**真实分布**不是口径错误。根因——这些行正是被 (c4a|leaf) 形态过滤器筛掉的入口，而该过滤器系统性漏检真实叶函数：FPU 常数函数（首字节 DD/DB）、mov getter（8B 81 / A1）、xor 清零（33）、常量返回（B8）、push ecx（51，即 P0_RESIDUAL_2 的 oracle 0x7775C0 形态）。RESIDUAL_2 已实证漏掉 2,026 个 FPU 叶 + 该 oracle。低地址段 `[004011B0,0040B3E0)` 恰是这类小叶函数密集区。全量复算判据特异度 99.3% 佐证非"全判 FUNC"的空判据。故**如实报告 95/5，不调整**。

## 6 · 可推广性

40 行等距样本（`work/generalize.py`，剩余 5,498 行取 0040B400..007B0BD0）：FUNC 强 39 / NOT_FUNC 弱 1。强判据率 97.5% ⇒ 预计 5,498 行中 **≈5,361 可裁、≈137 需 P1**（弱判据：单项 C2/C4/C5 失败）。依据：判据在历史集特异度 99.3%/召回 96.4%。`[静态推断]`，未逐行跑完。

## 7 · 交付与只读纪律

`ADJ_100.tsv`(100) · `coverage_delta.tsv`(95, S22/[静态推断]) · `EVIDENCE/ADJUDICATION_DETAIL.tsv`(100 全通道) · `EVIDENCE/NOT_FUNC_DETAIL.tsv` · `UNKNOWNS.md` · `DISAGREE.md` · `work/*`（recon/dump100/inspect_amb/criterion/validate_full/generalize/finalize 可复跑）。SHA/PE/验证见 EVIDENCE 与 work。
