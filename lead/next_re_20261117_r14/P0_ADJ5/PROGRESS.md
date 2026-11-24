# P0-ADJ5 PROGRESS（最终）

## 0 · 只读目标 / 写域
- 目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476`（全值现场复算，见 work/summary.json），ImageBase 0x400000；只读未改。Python 3.12.10 / capstone 5.0.7(skipdata=True) / pefile。写域仅 `P0_ADJ5\` 与 `_ghidra\P0_ADJ5\`；未写 COVERAGE/STATUS_BOARD/ra2youli/其它卡/\_audit；未改 coverage.tsv（只交 coverage_delta.tsv）。

## 1 · 第一步 三个去重数（自算，与 Lead 一致）
- ENUM UNDECIDABLE **5,598**；其中已在 coverage（entry 大写求交）**3,929**；尚未在 coverage **1,669**。自算 == Lead 独立核算（5598/3929/1669），无分歧，未停机。
- ENUM 数据行 5,656（UNDECIDABLE 5598 / FUNC 20 / NOT_FUNC 38）；coverage 数据行 18,479（本次盘面，比 COMMON 的 18,431 新，见 UNKNOWNS U1）。脚本 `work/step1_dedup.py`。

## 2 · 第二步 100 行裁定（address 升序前 100，00402F80..00438E60）
- **FUNC 54 / NOT_FUNC 46**；其中「仅结构证据」**54**（=全部 FUNC，因主判据在本池 0 命中，见 §3）。裁定明细 `ADJ_100.tsv`，逐行特征 `EVIDENCE/adjudication_detail.tsv`。
- NOT_FUNC 46 的构成：内部 jcc/jmp 目的（函数体内标签/共享尾声）8、仅硬边界无自洽体 34、仅叶体无硬边界 3、其它 1。

## 3 · 判据式（严格遵守：前置条件不计入判据）
- **前置条件（ENUM 建池定义，零区分力，仅申报不计分）**：16B 对齐 ∧ 粗前驱∈{nop,ret,jmp,int3} ∧ 首字节∉{E8,E9,EB} ∧ 可解码。
- **主判据（要求给出，但本池 0 命中）**：(a) 指令边界 E8 call rel32 目标（强）/ E9 jmp rel32 目标（弱，错源②）；(b) RTTI 可解虚表的槽值直指。**实测本池 a_call=0/1669、b_vt=0/1669** —— 因 ENUM 池正是用通道 b/c 把全部带 call/虚表引用的地址先收编进 coverage 后才建池，故残差天然无 (a)/(b)。这是结构性事实，非扫描失败（自检：0x4093B0 等已知 call 目标均命中；call 目标全集 6,728 = 项目已知值）。
- **辅证（本池唯一有作用，均标「仅结构证据」）**：(c) 严格硬边界 —— 地址前 ≤15 个 90/CC padding 之后有一条 ret/retf/int3/hlt/ud2（**排除 jmp**，粗前驱是池定义故不用）；(d) 体自洽 —— 线性解码 96B 内到 ret、无 jmp-out、≥2 条（排除裸 ret 共享尾声）。
- **负向标签判据**：地址是指令边界 jcc(70–7F/0F8x) 或 jmp 的目的 ⇒ 函数体内标签 ⇒ NOT_FUNC。此即「入口 vs 体内标签」的直接区分，非建池条件（jcc 目的未被 ENUM 排除：池内 153/1669）。
- **裁定规则**：(a)强∨(b) ⇒ FUNC(非仅结构)；否则 (c)∧(d)∧非分支目的 ⇒ FUNC(仅结构证据=Y)；否则 NOT_FUNC。全程未用 atlas entry+size。

## 4 · 第三步 区分力基线（全部同判据）
- **池内随机 100**（seed 20261119，1,669 中抽）：FUNC **48%**。本卡 100 行 FUNC **54%**，差 **6pp < 10pp** ⇒ **本判据在池内区分力低**（如实记录，不宣称判据有效）。
- **全域随机 100**（.text 内 16B 对齐随机）：FUNC **6%** ⇒ 作全域判据不过宽（54% vs 6% 说明池/全域有差异，但池内无区分力）。
- **正负对照**：正 5（atlas 已知入口 00401000/00401080/004010A0/004010C0/00401170，均不在本卡 100 行）FUNC **5/5**；负 5（P0_RESIDUAL NOT_FUNC internal_label 00403247/00403BBC/00403BDC/00403BFE/00405112）NOT_FUNC **5/5**。合计 **10/10**。
- **独立复核**：ADJ4 审计点名的 5 行（00402F80/00405AB0/004063A0/0040A600/00407080）本判据逐行 **5/5 NOT_FUNC** 一致（共享尾声被 jcc 标签判据正确剔除）。

## 5 · 停机核验
- 本卡 FUNC 率 **54%**，在 5%–90% 内，不停机。池内基线差 6pp < 10pp ⇒ 已按纪律写「本判据在池内区分力低」（§4）。主判据池内 0 命中已如实申报（§3），未伪造 a/b 证据。

## 6 · 核心数字（审计复算）
- 三个去重数 **5,598 / 3,929 / 1,669**。
- 本卡 100 行 **FUNC 54 / NOT_FUNC 46**；仅结构证据 **54**。
- 池内随机 100 FUNC 率 **48%**（本卡 54%，差 6pp）；全域随机 100 FUNC 率 **6%**。
- 正负对照通过 **10/10**；ADJ4 审计 5 行一致 **5/5**。

## 7 · 交付
`PROGRESS.md`、`ADJ_100.tsv`(100 行+表头)、`coverage_delta.tsv`(54 数据行+表头)、`EVIDENCE\`、`work\`(脚本可复跑)、`UNKNOWNS.md`、`DISAGREE.md`。复跑：`python work/step1_dedup.py && python work/engine.py && python work/jcc_sweep.py && python work/final_adjudicate_v2.py`。
