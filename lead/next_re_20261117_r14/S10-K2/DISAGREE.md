# DISAGREE.md — S10-K2 与主台账/派卡前提的分歧（逐条，含处置）

## D1 · 派卡前提 `proved=28（5.46%）` 与盘上不符（**已按纪律 9 停机核验，不凑数**）

- 卡面 §1：「S10 … [已证] 仅 28（5.46%）」；卡面 §4-T1：「当前 28/513=5.46%，门槛 257，差 229」。
- 盘上现值：`COVERAGE\PANEL.md` S10 行 proved_n=**55**, proved_pct=**10.72%**；`coverage.tsv` 自数 S10 atlas 513 行 `[已证]`=**55**（全 515 行=56）。`work/t1_targets.py` 复现。
- 判定：卡面 28 是 **M2 并表前旧截面**（与 S11-K2 卡面 13→真值 17/18 同类）。**不凑 28**，以盘上 55 为准。已在 DOD/PROGRESS 并列 28(卡面)→55(盘上)→本卡 37 条升级。
- 影响：到 50% 的缺口由 229 修正为 **202（55→257）**；本卡升级后 70/513，仍差 187。

## D2 · 「196 单元桩/非桩/去重」的 7 表集合：Unit vs Radio

- 台账 §965 数值：**196 单元 = 桩 144 / 非桩 52 / 去重 43**。
- 我独立取 7 类（Mission/Foot/Infantry/Aircraft/Building/Techno/**Unit**）v129..156 → 得 196/133/63/49（`EVIDENCE/verify_counts2.txt`），与台账不符。
- 追源：S10-K1 `work/rtti_and_counts.py` 的第 7 表是 **RadioClass `0x7F0508`**（不是 UnitClass）。改用 RadioClass 复算 → **196/144/52/43 精确闭合**（`EVIDENCE/verify_counts.txt` / `work/verify_ledger.py`）。
- 判定：**台账正确，我的初选表集不同**，非台账错。已在 LAYOUT §2.1 记录并以 RadioClass 为准引用 43；本卡 T2 逐槽表仍列 UnitClass（它有真实实现，语义更全），二者用途不同，不矛盾。

## D3 · S10-K1 三处结论已被台账 §965 作废（本卡只引用不重做）

- S10-K1 PROGRESS「43 个 Mission 有实现」→ 错：43 = 非桩入口地址数（本卡确认）；实际 24/32 Mission、22/28 槽。
- S10-K1「9 项双支撑 +2 单边」→ 错：实为 **8 双支撑 + 3 单边**（+0xB8/+0xCC/+0x6C），台账 §965。
- S10-K1「`0x414B9E`=Guard→Attack 切换点」→ 错：实为 `AircraftClass::Mission_Hunt→Attack`（Aircraft 专属，不在 Guard 内）；本卡未触碰该结论。
- 处置：本卡不复用上述三条，全部以台账 §965 为前提；未写台账。

## D4 · 基线 `ret 0xC`：本卡 1651 vs §969 的 672

- 本卡全 .text 指令级 `mov eax,imm32`+ret=837 / `B8 imm32 C3` 字节严格=666 / 16B 对齐起点=36.6%（均复现 STATUS_BOARD）；但指令级 `ret 0xC`=**1651**，§969 记 **672**。
- 判定：定义/范围差（§969 可能限 vtable 函数或特定形态）。**本卡未用 `ret 0xC` 定任何槽语义或分级**，该差异不影响结论；列 UNKNOWNS #6。

## D5 · coverage_delta 37 行的 subsystem 归属

- 37 条 delta 全按派卡格式标 `subsystem=S10`；但其中 22 条 entry 在 `coverage.tsv` 现分属 S05(13)/S12(8)/S08(1)（按地址/类族分类）。S10-K1  precedent：其 delta 36 行亦全标 S10（当时均新行，未在 coverage）。
- 处置：按 task 字面格式（subsystem S10）+ precedent 保留；grade/semantics 由合并员按 entry 升级；是否改 subsystem 由 Lead 裁决。列 UNKNOWNS #8。

## D6 · 无真机 / 无 KB / 未写台账

- 本卡静态 K 卡（写域仅 `S10-K2\` 与 `_ghidra\S10-K2\`），未申请真机、未建 `KB\Sxx_Mission.md`、未写台账、未派审计；均按派卡指令，非分歧，仅备案。
