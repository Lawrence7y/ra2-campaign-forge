# W106_classid6 PROGRESS（一卡一问：WhatAmI()==6 是哪一类）

1. 读 R10_FACTS.md + LEAD_FINDINGS_R09.md L1/L2 ✔
2. 建卡目录 + 自有 Ghidra 工程，`analyzeHeadless -import gamemd.exe` 全量分析 245s 成功（job pwsh-7504623001e44011）✔
3. `_w106_bytescan.py` 原始字节扫描：3 处 `mov [esi],0x7E3EBC` 写点（0x43B721/0x43B9FC/0x43BCFF，均紧跟 `mov [reg+4],0x7E3EA0` 次级 vptr）；vtable 6 vs 15 共享槽 61 个 → EVIDENCE\bytescan_out.txt ✔
4. WhatAmI 邻域解码：0x459E70=`mov eax,1824;ret`（槽12）；vptr6 紧前 0x7E3EB8 处发现 RDATA 指针网（非字符串）→ EVIDENCE\whatami_ladder.txt ✔
5. 识别出 .data 有 MSVC RTTI TypeDescriptor（`.?AVBuildingClass@@` 等）→ EVIDENCE\rtti_names.txt ✔（与 §629-2"镜像无 RTTI"相悖 → DISAGREE.md）
6. COL 链证明：vt6[-1]=0x7FC360=COL{TD=0x818D60=".?AVBuildingClass@@", CHD 15基类}；同法验证 vt15[-1]=0x8033B8→".?AVInfantryClass@@"（对照组通过）→ EVIDENCE\col_tda_proof.txt ✔
7. Ghidra 脚本 ClassId6.java 首跑编译错（getMnemonicName 不存在），改 getMnemonicString 重跑成功：FUN_0043b680/0043b740/0043bcf0 反编译 + REFS 0x7E3EBC=3 处 + 13 个构造调用者 → EVIDENCE\ghidra_classid6.txt ✔
8. 删除器 0x459F20 字节检查：无 push 0x720（VC6 无尺寸 delete），尺寸证据定格为 ctor+0x718 与槽12=0x720 双指纹 ✔
9. 写 CLASSID6.md / UNKNOWNS.md / DISAGREE.md ✔（结论：类 6 = BuildingClass）
