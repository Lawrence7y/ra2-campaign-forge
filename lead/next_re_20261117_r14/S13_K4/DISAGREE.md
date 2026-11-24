# S13-K4 DISAGREE

## D1 — 卡面 proved 55 与盘上 coverage.tsv 47
卡面写「盘上约 55/240 ≈ 22.9%」。本卡自算（统一大小写，coverage.tsv ∩ atlas）得 coverage 内 `[已证]`=47/240=19.58%。
差 8 = S13-K2 coverage_delta.tsv 的 8 行（实测在 coverage.tsv 仍 [未证]，未并入）。
处理：以盘上 coverage.tsv 47 为 disk 真值；不重取 K2 的 8 行；本卡只交新增 13 行。无冲突，属未并入时滞。证据：work/baseline.py 输出 + EVIDENCE/00_SUMMARY.txt。

## D2 — DoD ≥50%（120 行）不可达，拒绝凑数
任务要求 DoD 需 ≥50%（≥120 行）。按 4 类允许证明类型穷举，本卡只能证明 13 行新增（上限 68/240=28.33%，含 K2 8 行）。
拒绝把 104 Class::slotN + 40 vslotN（占位名）升为 `[已证]`：这正是 R14_COMMON §8.1 ⑬ 判 S11-K4 整卡 FAIL 的错源（331 行 slotN，语义已证 0/331）。
立场：如实报 13 行 + 穷举证据（EVIDENCE/exhaustive_survey.tsv），不伪造覆盖率。

## D3 — 7 行为级行的 grade 由 [未证] 升 [已证] 的依据
这 7 行在 coverage.tsv 为 [未证]，semantics 带「无来源支撑，待补证」。但其 evidence_path 指向 S13-K1 EVIDENCE（实存），且本卡 behavioral7.txt 独立字节复算确认行为事实（INI 键串/resolver 调用/vptr 写）。
证明类型是「行为级语义」（函数体字节判定它做什么），非虚表归属；符合任务允许的第 3 类。若审计认为需改 name 或补字段偏移，可退回本卡修正。

## D4 — 6 B8 桩的 slot 号取定
R14_COMMON §8.2 ② 警示 69/78 类 v[11]/v[12] 同为 B8 imm32 C3，有取错槽风险。
本卡不凭字节形态定槽：用 RTTI 主虚表实测槽位（b8_verify.txt：slot11=WhatAmI/slot12=GetSize，VT 0x7e3d10/0x7ef890/0x7f0810），且 GetSize 三行做工厂 push→new→ctor→vptr 双点闭合（getsize_ctor.txt）。无取错槽。
