# 卡 R17-LEDGER-1060 · 书记员起草台账 §1060（R17 第 7–8 轮：vtable 定名 + slot73 全映射 + 两审 + GLM 两卡）

角色：书记员（只起草，不改台账）。只写自己目录；台账由 Lead 逐字追加。

## 一、必须覆盖的事件
1. **R12（`R17_R12_VT_OFFSET`，hy4）**：首个「定偏移虚派发」扫描（此前只扫过 `[reg+reg*4]` 索引型）。
   `call [reg+0x124]` **181** + `[reg+0x1AC]` **86** = **267**；`jmp` 两类均 0；`mov reg,[reg+disp32]` **55+15=70**；
   另 `stack_ff5424` **9**、`other_test_imm` **7**、`other_cmp` **1**；hits.tsv 数据行 **354**（Lead 从原始数据复核）。
   ⇒ 形态大量存在但**无一处能把基址寄存器钉成目标类对象**，全判 `NO_CALLER_LINK`。
   🔴 **该报告表格有一处算术错**（GLM 发现、Lead 从 `hits.tsv` 复核）：「附带 push/cmp/test 等」行写 `16 | 0 | 8`，
   `0x124` 单元格应为 **8**（`other_test_imm` 7 + `other_cmp` 1），合计 8 正确、16 是错的。
2. **R13（`R17_R13_NAME_TABLE`，hy4）— 本轮 headline**：用 `vtable[-4]` → COL → `+12` pTD → `+8` 内联名 把 vtable 定名：
   `0x7E3EBC`/`0x7E3EA0`/`0x7E3E98`/`0x7E3E90` = **`.?AVBuildingClass@@`**；`0x7F4960`/`0x7F4944`/`0x7F493C`/`0x7F4934` = **`.?AVTechnoClass@@`**；
   `0x7E4E78` = `.?AV?$DynamicVectorClass@H@@`。Q3 独立检验：TechnoClass 组**与 §2.6 一致**。
   另：装饰名 **988**，全在 `.data`（`.?AV` 962 / `.?AU` 26 / 其它 0），**不是一张 988 项总表**（命中 3 段 stride `0x18` 数组共 17 项）。
3. **AUDIT-R13（deepseek，跨家族）— A1–A5 全 AGREE**，且给全表闭环：1201 条 COL 的 pTD **全部**命中 988 个 TD（100%）；
   1201 条 COL 全被某 vtable 以 `[-4]` 指回；954 个主 COL 的 `pSelf` 恰为 `COL−0x10`；`.text` 内各有 3 处连续 `C7 06/46 04/46 08/46 0C` 写作独立旁证。
   A4 分辨力：自选 `0x7E22A4`→AircraftClass、`0x7E4EEC`→CellClass、`0x7E8C94`→FootClass（另 `0x7EA8A0`→HouseClass、`0x7E3278`→AlphaShapeClass）；
   **`0x7E22A4` 与 `0x7E8C94` 的 slot0 同为 `0x410260` 却给出不同类名** ⇒ 结果不被槽内容带偏。必改 3 条（均属报告表述，非结论）。
4. **R14（`R17_R14_VT_STRUCT`，hy4）**：322 槽 **322 个不同值、重复 0 种**；`0x43F180` 仅 #73、`0x449440` 仅 #107；
   三张小表 2/2/7 槽且与主表同值重叠 **0**；结构判定「更像一个类的正常 vtable」，且**全文零类名（未越界）**。
5. **R15（`R17_R15_SLOT73`，hy4）**：索引 1211 vtable / 951 类名。五类主 vtable 与槽值：
   BuildingClass `0x7E3EBC` 322 槽 #73 `0x43F180` #107 `0x449440`；TechnoClass `0x7F4960` 309 槽 #73 `0x6F4A70` #107 `0x4264C0`；
   InfantryClass `0x7EB058` 343 槽、UnitClass `0x7F5C70` 344 槽、AircraftClass `0x7E22A4` 341 槽，三者 #73 **均 `0x4D3780`**。
   ⇒ 判定：两函数为 **BuildingClass 专有**。
6. **三重印证（Lead 亲自核算术）**：`coverage` 行 `entry 004D3780`（早已 `[已证]`）语义称 slot73 位于 `0x7E23C8`/`0x7E8DB8`/`0x7EB17C`/`0x7F5D94`；
   实测四类主 vtable + `0x124` 恰好等于这四个地址（Aircraft `0x7E22A4+0x124=0x7E23C8`、Foot `0x7E8C94+0x124=0x7E8DB8`、
   Infantry `0x7EB058+0x124=0x7EB17C`、Unit `0x7F5C70+0x124=0x7F5D94`）⇒ **该 `[已证]` 行被独立字节分析印证**。
7. **R17（`R17_R17_SLOT73_MAP`，hy4）反向映射**：`0x43F180` **1**、`0x449440` **1**、`0x4D3780` **4**（Aircraft/Foot/Infantry/Unit）、`0x6F4A70` **1**；
   FootClass `0x7E8C94` 341 槽 #73 `0x4D3780` #107 `0x4D9C10`。另观察到 `0x4264C0` 出现在 **17 个类**的 #107（典型基类方法整族继承）。
8. **GLM 两卡（`zcode/GLM-5.3-Flash`，自报身份 `bigmodel-api/GLM-5.3-Flash`）**：
   卡1 8 项全 AGREE、`OVERALL: CONSISTENT`、未发现「②-b 已证」误述；
   卡2 7 项 AGREE、**#5 DISAGREE**（R12 表格那处算术错，见事项 1）⇒ 证明 GLM 在「≤8 行纯文本/表内算术」上有实效，但**仍不用于字节级判定**。
9. **R7 勘误（`R17_R7_ERRATA`）**：新建 `R17_R7_REJECT_LAYER\ERRATA.md`（独占创建，未覆盖），三处勘误全部写入；
   `REPORT.md` 的 sha256 与 mtime **写前写后完全一致**（未改动一字节）。三处：jne `0x47C73D`→`0x47C73F`（目标 `0x47C853` 正确）、
   `0x47C853`=`5F`(pop edi)、xor `32 C0` 在 `0x47C856`、`0x47C615`=`5E`(pop esi) 而 `C2 08 00` 在 `0x47C616`。

## 二、写法要求
- 凡数字**必须自己从盘上复算**（尤其事项 1 的 354 与分类计数、事项 6 的四条加法）；与卡面不符时并列报出并说明差异。
- 事项编号 1–9，每项给证据路径（相对仓库根）。取不到写「未取得」，严禁编造。
- **必须写明「类名结论已过跨家族审计且 A1–A5 全 AGREE」**，同时写明其**证据强度**：链条字节证实 + 全表闭环，但「哪张 vtable 属于哪个类」是**由 COL→TD 推得**，不是从代码调用推得。
- **不得**把「BuildingClass 覆写 TechnoClass 槽 73」写成已证（见 `R17_R16_SLOT73_SEM`：该读法只是**推断**，`edi` 保持未字节证实）。
- 指令地址用 0x 前缀；entry 用 8 位大写十六进制不带 0x。逐条理由**必须互异**。
- 结尾必须写：「本草为 §1060 草稿，由 Lead 逐字追加；书记员未自行改动台账。」

## 三、要读的（只读）
`R17_R12_VT_OFFSET\`、`R17_R13_NAME_TABLE\`、`R17_AUDIT_R13\`、`R17_R14_VT_STRUCT\`、`R17_R15_SLOT73\`、
`R17_R17_SLOT73_MAP\`、`R17_GLM_TXT_1\`、`R17_GLM_TXT_2\`、`R17_R7_ERRATA\`、`R17_R7_REJECT_LAYER\ERRATA.md`、
`R17_R16_SLOT73_SEM\REPORT.md`（仅用于事项 2 的强度限定）、`COVERAGE\coverage.tsv`（只读 `entry=004d3780` 那一行）

## 四、产物（只写本目录）
`R17_LEDGER_1060\`：SECTION.md（标题行以 «## §1060 · 书记员覆盖 R17 第 7–8 轮（…）：…» 起）、numbers.tsv、SELFCHECK.md
严格 8 分钟；先落 numbers.tsv 再写正文。不执行逆向、不启动 gamemd、不写仓库根。