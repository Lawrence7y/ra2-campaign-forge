# R139 执行报告 · F29 字节级复算 + F35/F23 现盘状态

执行员：hy4（R139-EXEC-F29F35） ｜ 工作目录：`/home/t628/projects/ra2-campaign-forge` ｜ 全程只读 lead/ 与 _r139/
证据：`/tmp/r139hy4/raw.txt`（含每条命令原文与完整输出）；脚本 `a_tasks.py` / `b_tasks.py` 的 sha256 与输出详见 raw.txt。
二进制：`ra2bench/gamemd.exe`，4825360 B，sha256 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`。

## A1 · TClassFactory RTTI 名统计
- 实测：正则 `\.?AV\?\$TClassFactory@([ -~]{1,120}?)@@` 命中 **77**；去重模板实参 **77** 个，每个恰好出现 1 次（all_unique_count_1=True）；全部 77 处落在 **`.data`** 节（`.data` VA=0x412000 / RawPtr=0x412000，命中偏移均在 0x412000..0x47E000）。
- 与背景主张（77 张表）**一致**；判据：整段匹配落在单一节 raw 区间内才归属该节。

## A2 · 8 字节桩 `B8 01 00 00 00 C2 04 00`
- 实测：全文件命中 **40**；`.text` 内 **40**，其他节 **0**，跨节边界 **0**（40 处偏移最小 0xd230、最大 0x36f640，均在 .text raw 区间 0x1000..0x3e1000 内）。
- 与主张中隐含的 63/64 类数量**不直接等同**（此序列是 8 字节桩，非完整 17 字节模板）；本节只报实测。

## A3 · 17 字节序列 `8B44240483C00450FF15C8117E00C20400`
- 节表（先于换算打印）：`.text` VA=0x1000 / VSize=0x3df38d / RawPtr=0x1000 / RawSize=0x3e0000；ImageBase=0x400000 ⇒ .text 段 `file_off = VA − 0x400000`。
- 实测命中 **80** 处，全部在 `.text`：文件偏移 0x2beec0..0x3ad620，VA 0x6beec0..0x7ad620（完整清单见 raw.txt）。
- `0x6C2AC0`（off 0x2c2ac0）与 `0x6C51C0`（off 0x2c51c0）均逐字节等于该 17 字节模式，且两者互相**逐字节相同**（compare_two_sites=True）。

## A4 · IAT 槽 0x7E11C8
- 遍历 16 个 IMAGE_IMPORT_DESCRIPTOR / ILT / IAT / IMAGE_IMPORT_BY_NAME（372 个导入项）后定位：
- `0x7E11C8`（RVA 0x3e11c8）属于 **`KERNEL32.dll`**，函数名 **`InterlockedIncrement`**，Hint **432**（0x1B0）。
- idx：DLL 内 0-based = **62**；全局 0-based = **63**；全局 1-based = **64**。

## B1 · proved_strict 定义的现盘代码级实现
- 判据：同一行同时含字面 `proved_strict` 与字面 `[未证]`。全库扫描（b_replay 口径：17,289,753 行）命中 **1938** 处 / 652 文件；其中 `.py` 脚本命中 **11** 处（其余为台账散文/备份/JSON/TSV）。
- 11 处 `.py` 命中（文件:行）与原文见 raw.txt 的 “B1 CODE-LEVEL SUBSET”。其中 2 处是**判据实现本身**：
  - `lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py:14`：`  proved_strict_n    proved_n 中 one_line_semantics 不含 [未证]`
  - `lead/next_re_20261117_r14/RULING_R15_20261119/work/strict_panel.py:78`：`            if "[未证]" not in sem:`（第 78 行独立复核一致；文件共 144 行）
- 其余 `.py` 命中：`_r88/tiers_r88.py:150-151`（扫描判据）、`_r137/r137c_f35_criterion.py:138`、`_r137/sub_hy4/r137_f35_audit.py:183`、`_r138/r138e_write_fourpiece.py:185`、`_r137/r137f_write.py:101/139/183`、`_r139/r139b_f35_def.py:13/49`。
- 结论：F35 主张“proved_strict 的定义只在已失的 COVERAGE/PANEL.md（M52）”与现盘**不一致** —— strict_panel.py 第 14 行声明定义、第 78 行以代码实现了该定义（一字面 `[未证]` 排除）。

## B2 · strict_panel.py 声明的输入文件现盘状态
- `os.path.exists("lead/next_re_20261117_r14/COVERAGE/coverage.tsv")` = **False**
- `os.path.exists("lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv")` = **False**
- `isdir("lead/next_re_20261117_r14/COVERAGE")` = **False**；`isdir("lead/next_re_20261112_r10")` = **False**。
- strict_panel.py 确为声明者（`COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")`、`ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")`）。

## B3 · F23 算术与归属说明
- 算术：6 + 2 + 3 = **11**，与 total 12 差 **1**。
- FACT_INDEX v5.33（`lead/.../R17_R105_FACTINDEX_V533/FACT_INDEX.tsv`）F23 行仅 1 条（第 24 行），已含 R138 补注明确写出「6+2+3=11，与 total=12 差 1 行，该行在上述分解里没有归属」。
- 检索词在 F23 行的命中数：第 12 = 0、第12 = 0、余 1 = 0、余1 = 0、剩 1 = 0、剩1 = 0、另一类 = 0、未归类 = 0 —— 即**没有**对「第 12 行」的具体归属说明。
- 表扫描：扫描 `lead/` + `_r137/` + `_r138/` + `out/` 下全部 **50** 个 `.tsv/.csv`，行数在 1600..1700 区间的候选 **0**（约 1654 行的表不在现盘）。

## 边界与注意
- B1 的扫描期间另一代理在 `_r139/` 写入文件，导致两次命中计数 1937 vs 1938；两者 `.py` 命中均为 11，不影响判决。
- 本执行卡任务 A 仅做纯字节/节表/导入表遍历，未对 .text 开 Capstone detail=True；未修改任何 lead/ 与 _r139/ 文件。
