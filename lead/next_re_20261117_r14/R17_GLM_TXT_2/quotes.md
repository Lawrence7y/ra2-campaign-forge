# R17_GLM_TXT_2 · quotes（引文备查，均逐字抄自原文件）

## 逐项引证
- #1 R17_R13_NAME_TABLE\REPORT.md：「判定：九个均可定类名，依据为二进制内 RTTI 自证；未使用 YRpp 或相似形态猜测。」（全文 grep 无「双源」「定谳」「待审计」字样）
- #2 R17_R13_NAME_TABLE\REPORT.md：「但 vtable[-4] 全部指向 .rdata 内合法 RTTI COL；COL+12 指向 TypeDescriptor，TD 头 0x7F9594/0 且 TD+8 为装饰名。」
- #3 R17_R13_NAME_TABLE\REPORT.md：「等距指针数组：有，但不是一张 988 项总表。命中 3 段长度≥4 的 stride 0x18 数组，共 17 项」；另见结论摘要「未在 .data/.rdata 找到单一 988 项指针数组」。
- #4 R17_R14_VT_STRUCT\REPORT.md：「类名/继承层级/函数语义：**未取得**；缺反汇编、RTTI/对象布局与调用点类型证据，本卡按铁律不取。」另「结构判定：更像一个类的正常 vtable……（仅按本卡字节结构判据；不涉及类身份）」；grep 证实全文零装饰名、零 "@@"、零 XxxClass 词。
- #5 R17_R12_VT_OFFSET\REPORT.md：「| 附带 push/cmp/test 等 | 16 | 0 | 8 | 4063232 |」；对照「细分其他类: other_cmp: 0x124=1 …other_test_imm: 0x124=7」合计 8。卡面三行原文：「| call [reg+disp32] | 181 | 86 | 267 |…」「| jmp [reg+disp32] | 0 | 0 | 0 |…」「| mov reg,[reg+disp32] | 55 | 15 | 70 |…」均自洽。
- #6 R17_R12_VT_OFFSET\REPORT.md：「每类扫描字节数 4063232 B（全 .text raw，含尾部 raw padding；virtual size 0x3DF38D）」；表列「扫描字节数/类」五行均 4063232；「.text raw 0x1000..0x3E1000，RAWSIZE 0x3E0000 = 4063232 B」。
- #7 R17_R7_REJECT_LAYER\ERRATA.md：「勘误 1 · `jne` 指令起始：0x47C73D → 0x47C73F」「勘误 2 · `xor al,al` 地址：0x47C853 → 0x47C856（0x47C853 = `5F` pop edi）」「勘误 3 · 1 字节笔误：0x47C615 不是 `C2 08 00`（实为 `5E` pop esi；`C2 08 00` 在 0x47C616）」
- #8 R17_R7_ERRATA\REPORT.md：「只读打开 `R17_R7_REJECT_LAYER\REPORT.md`……未写、未重命名、未改 mtime。」「SHA-256（写前 = 写后）：`0EB3D37B41C8777BB9EA2FF7C645D6000D4F05B533AE5E5EC27E0D4FD7E4FB72`」「mtimeMs（写前 = 写后）：`1795239104954.8674`」

## 额外检查引证（三个类名，R17_R13_NAME_TABLE\REPORT.md）
- `.?AVBuildingClass@@` ×4：Q2 四条 bullet（offset 0/4/8/12）逐字相同；字节例行「0x818D60 `94 95 7f 00 …2e 3f 41 56 42 75 69 6c 64 69 6e 67 43 6c 61 73 73 40 40 00`」的转写与该名一致（2E 3F 41 56=".?AV"，40 40="@@"）。
- `.?AVTechnoClass@@` ×5：Q2 四条 bullet + Q3「全部指向 ".?AVTechnoClass@@"」逐字相同。
- `.?AV?$DynamicVectorClass@H@@` ×2：Q2 offset 0 bullet 与 Q3 旁证句逐字相同。
- 变体筛查：全文唯一装饰名集合不含任何大小写/缺 @@ 变体；"TechnoClass" 第 6 处出现为未修饰短语「0x6F2B40 = TechnoClass 构造器」（引述 §2.6），非装饰名。

## 跨文件一致性旁证（同一事实、不同文件的文字表述）
- gamemd.exe sha256：R13/R14_VT_STRUCT/R12/R7_REJECT_LAYER.ERRATA/R7_ERRATA 五份文件均写 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476，逐字一致。
- vtable 0x7E3EBC 的 COL：R13「0x7E3EBC：COL 0x7FC360 -> TD 0x818D60 -> ".?AVBuildingClass@@"（offset 0）」与 R14_VT_STRUCT 槽表行「T2 | 0x007E3EB8 | 0x007FC360 | —」表述一致（0x7E3EBC 的 vtable[-4] 槽位即 0x7E3EB8）。
- 区域边界：R13 列 BuildingClass 四 vtable VA 0x7E3EBC/0x7E3EA0/0x7E3E98/0x7E3E90（offset 0/4/8/12）；R14_VT_STRUCT 主表 [0x7E3EBC,0x7E43C4) 322 槽、小表 [0x7E3E90,0x7E3EBC) 11 槽（T0/T1/T2 分界 0x7E3E98/0x7E3EA0）——两文件对同一区域的文字表述相容。
- 三处勘误数值：R17_R7_REJECT_LAYER\ERRATA.md 与 R17_R7_ERRATA\REPORT.md 摘要「三处勘误：全部写入（jne 0x47C73D→0x47C73F；xor al,al 0x47C853→0x47C856，0x47C853=5F pop edi；0x47C615 笔误→5E pop esi，C2 08 00 在 0x47C616）」逐字一致。
- 未取得文件：无（五份目标文件全部读到）。
