自报执行方（原始字符串）：provider = `bigmodel-api`，model id = `GLM-5.3-Flash`（`bigmodel-api/GLM-5.3-Flash`）
卡：R17-GLM-TXT-3 · 纯文本/表内算术第二意见（恰 8 项）· 2026-11-21
边界遵守：仅做文字一致性 + 表内数字加减自洽；未做字节级、装配形态、宿主身份、函数边界、类名正确性判定。

#1 AGREE —— 同名类 slot_count 完全一致：Aircraft 341/341、Infantry 343/343、Unit 344/344（Building 322、Techno 309 仅见于 R15 表，Foot 341 仅见于 R17 表，无同名可比冲突）。引证：R17_R15_SLOT73\slot73_107.tsv:2-6 与 R17_R17_SLOT73_MAP\four_classes.tsv:2-5。
#2 AGREE —— 六个 main_vtable 全部对上：Building 0x7E3EBC / Techno 0x7F4960 / Infantry 0x7EB058 / Unit 0x7F5C70 / Aircraft 0x7E22A4（slot73_107.tsv:2-6）、Foot 0x7E8C94（four_classes.tsv:3）；两表重叠类（Aircraft/Infantry/Unit）值一致。
#3 AGREE —— 逐行算：L2 0x007E22A4+0x124=0x007E23C8 ✓；L3 0x007E8C94+0x124=0x007E8DB8 ✓；L4 0x007EB058+0x124=0x007EB17C ✓；L5 0x007F5C70+0x124=0x007F5D94 ✓（four_classes.tsv:2-5，4/4 相等）。
#4 AGREE —— hits.tsv 数据行实测 354（表头 :1，首数据行 :2=0x403CAC，末数据行 :355=0x7C34F6）；按 class 列分组实测 call=267 / mov=70 / stack_ff5424=9 / other_test_imm=7 / other_cmp=1，和=354，与卡面完全一致。
#5 AGREE（矛盾成立）—— R17_R12_VT_OFFSET\REPORT.md:14 表头列序为「类别|0x124|0x1AC|合计|」，:19 行「附带 push/cmp/test 等 | 16 | 0 | 8」⇒ 0x124 格=16；行内 16+0≠8 已自相矛盾，且 hits.tsv 实测 other_test_imm=7、other_cmp=1（REPORT.md:27 与 :23 亦写 0x124=7 与 1）⇒ 该格应为 7+1=8，16 与 7+1 矛盾成立。同表 call 181+86=267、mov 55+15=70、总计 267+70+8+9=354 均自洽，唯此一格错。
#6 AGREE（附注）—— R17_R14_VT_STRUCT\REPORT.md:16「槽数：322；不同值：322；重复值种类：0」，:19「全部重复值已写入 `dups.tsv`（0 种）」⇒ 报告确实给出 dups.tsv 且其确为空。附注：实测 dups.tsv 为 0 字节、0 行，连表头也没有——"空"成立，但"只有表头"字面不成立（比预期更彻底的空）。
#7 AGREE —— R17_R16_SLOT73_SEM\REPORT.md:21「整体判定：BuildingClass 槽 73 覆写为 0x43F180，并在其体内显式调用 TechnoClass 槽 73 实现 0x6F4A70 —— 推断（非字节证实）」；:20「同一对象判定：强推断，未取得全区间字节证实」；:32「若必须标注推断强度：弱推断（仅形态）」——覆写读法明确标注为推断而非字节证实。
#8 AGREE —— R17_AUDIT_R13\VERDICT.md:153「## 必改项（共 3 条；第 1 条为事实底座级）」恰 3 条：必改1（:155；修法 :167-168=列名改 data_section_va_refs 并写明限定）、必改2（:170；修法 :174-175=addr 改名 name_va/统一口径）、必改3（:177；修法 :180-182=把正控/反控写进 REPORT）；三条均属报告/列名表述层面，均不动摇 A1–A5 的类名链结论（:19、:43、:62、:89、:115 均 AGREE）。

## 额外检查（不计入 8 项）：三个类名字符串逐字比对
- `.?AVBuildingClass@@`：R17_R15_SLOT73 8 处 / R17_R17_SLOT73_MAP 11 处 / R17_AUDIT_R13 13 处，全部逐字一致。
- `.?AVTechnoClass@@`：8 / 7 / 14 处，全部逐字一致。
- `.?AVFootClass@@`：4 / 15 / 5 处，全部逐字一致。
- 无大小写变体、无缺 `@@`、无 `?$` 模板化变体。注记：① R17_R15_SLOT73\REPORT.md:45「明细：.?AVBuildingClass@@@0x007E3EBC」中第三个 `@` 为"名字@地址"分隔符，名字本身仍是 `.?AVBuildingClass@@`，非变体；② 仅 R17_R15_SLOT73\class_index.tsv 存在以这三类为模板实参的**其它类** RTTI 名（:107 `.?AV?$DynamicVectorClass@PAVBuildingClass@@@@`、:127、:190、:230、:342 `.?AV?$TClassFactory@VBuildingClass@@@@`、:470、:490、:554、:594），属其它类名，非目标串变体；另两产物无此类串。

OVERALL: 有冲突（#5）—— R17_R12_VT_OFFSET\REPORT.md:19 的 0x124 单元格 16 应为 8；其余 7 项与三串类名逐字检查全部一致。
