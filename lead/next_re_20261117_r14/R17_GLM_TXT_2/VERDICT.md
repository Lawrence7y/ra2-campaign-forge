# R17_GLM_TXT_2 · VERDICT（纯文本一致性检查，限 8 项）

- 执行者自报：provider = bigmodel-api；model id = GLM-5.3-Flash；原始字符串：`bigmodel-api/GLM-5.3-Flash`
- 卡面：R17-GLM-TXT-2。边界遵守：仅判断同一事实在不同文件里的文字表述一致性；未做字节级、装配形态、宿主身份、函数边界、类名正确性判定。
- 检查日期：2026-11-21

## 逐项结论（8 项）
1. AGREE —— R17_R13_NAME_TABLE\REPORT.md：全文无「双源」「定谳」表述，未写成"已双源定谳"（按卡面括号后半句成立）；注：亦无「待审计/单源」显式标记，属单源自证口吻。引证：「判定：九个均可定类名，依据为二进制内 RTTI 自证；未使用 YRpp 或相似形态猜测。」
2. AGREE —— 同报告明确写出方法链。引证：「但 vtable[-4] 全部指向 .rdata 内合法 RTTI COL；COL+12 指向 TypeDescriptor，TD 头 0x7F9594/0 且 TD+8 为装饰名。」
3. AGREE —— 对"未找到单一 988 项总表"有明确表述。引证：「等距指针数组：有，但不是一张 988 项总表。命中 3 段长度≥4 的 stride 0x18 数组，共 17 项」
4. AGREE（未越界）—— R17_R14_VT_STRUCT\REPORT.md 全文未声称任何类名（grep 证实：无任何 `.?AV…@@` 装饰名、无 "@@"、无 XxxClass 类名词），并显式声明未取得。引证：「类名/继承层级/函数语义：**未取得**；缺反汇编、RTTI/对象布局与调用点类型证据，本卡按铁律不取。」
5. DISAGREE（限全表口径）—— R17_R12_VT_OFFSET\REPORT.md：卡面所列三行自洽（call 181+86=267、jmp 0+0=0、mov 55+15=70 均成立），但同表「附带 push/cmp/test 等」行合计不自洽。引证：「| 附带 push/cmp/test 等 | 16 | 0 | 8 | 4063232 |」（16+0≠8；"细分其他类"合计 1+7=8 与行首 0x124=16 相互矛盾）
6. AGREE —— 明确写出扫描字节数且各表对齐。引证：「每类扫描字节数 4063232 B（全 .text raw，含尾部 raw padding；virtual size 0x3DF38D）」；命中数表"扫描字节数/类"列五行均为 4063232，与「.text raw 0x1000..0x3E1000，RAWSIZE 0x3E0000 = 4063232 B」一致。
7. AGREE —— R17_R7_REJECT_LAYER\ERRATA.md 三处勘误齐备、格式统一（①原文片段②权威值③字节依据④定谳出处），且与 R17_R7_ERRATA\REPORT.md 摘要数值逐字一致。引证：「勘误 1 · `jne` 指令起始：0x47C73D → 0x47C73F」「勘误 2 · `xor al,al` 地址：0x47C853 → 0x47C856」「勘误 3 · 1 字节笔误：0x47C615 不是 `C2 08 00`」
8. AGREE —— R17_R7_ERRATA\REPORT.md 明确写明未修改 REPORT.md 并给出写前=写后 sha256 与 mtime。引证：「SHA-256（写前 = 写后）：`0EB3D37B41C8777BB9EA2FF7C645D6000D4F05B533AE5E5EC27E0D4FD7E4FB72`」

## 额外检查（不计入 8 项）：三个类名字符串逐字一致性（R17_R13_NAME_TABLE\REPORT.md）
- `.?AVBuildingClass@@` ×4、`.?AVTechnoClass@@` ×5、`.?AV?$DynamicVectorClass@H@@` ×2（精确串匹配计数）。
- 逐字一致证据：raw 子串计数 BuildingClass=4 / DynamicVectorClass=2 与完整装饰名计数相等（每处出现均为完整逐字名）；TechnoClass raw=6，多出的 1 处是引述 R14_COMMON §2.6 的未修饰短语「0x6F2B40 = TechnoClass 构造器」，非装饰名变体。
- 全文装饰名唯一值集合为 {.?AVBuildingClass@@, .?AVTechnoClass@@, .?AV?$DynamicVectorClass@H@@, .?AVFileClass@@, .?AVSmudgeTypeClass@@}，全部 .?AV 前缀、@@ 结尾，无大小写或拼写变体。
- 结论：三个类名字符串在各处拼写/大小写/@@ 结尾逐字一致。

## OVERALL
OVERALL: 有冲突（#5：同表「附带 push/cmp/test 等」行 16+0 与合计 8 不自洽；卡面所列 call/jmp/mov 三行合计自洽；其余 7 项一致，三个类名逐字一致）
