# DISAGREE.md — 与台账 / P0_GATE_B 的不一致
## 更正 §994（[0xA8E9A0] 写点数）
- 台账 §994 引 a10 脚本报 [0xA8E9A0] **36 处写点**。
- 本卡按 capstone 5.0.7 `op.access & CS_AC_WRITE` 对 .text 线性 skipdata 扫描：
  **23 写 / 100 读 / 总 123**（EVIDENCE/p6_verify.txt；脚本 work/p6_verify.py，同法见 work/t1_field_scan.py）。
- 助记词直方图：mov=110, **cmp=13**。36 − 23 = 13，恰等于 cmp 条数 ⇒ 根因：a10 把 13 处
  `cmp byte ptr [0xA8E9A0],...`（**读**）误记为写。cmp 是只读比较，op.access 不含 CS_AC_WRITE。
- 写入地址全集（复算用）：52D9D7 55FC96 55FD9A 6472AA 6472F0 6474AC 6475BE 647ADC 6481FE 64826F
  652351 6858EA 6859F9 685B33 685BC7 685C23 686035 68620F 6863C3 6866EF 6BE1CC 78EC41 78EEAD。
- 【更正 §994】[0xA8E9A0] 写点 = 23（不是 36）；a10 的 36 含 13 处 cmp 误分类。

## P0_GATE_B UNKNOWNS U2「arg2 疑为 HouseClass*」作废
- 本卡实测：gate 0x47C620 的 arg2 = `.?AVBuildingTypeClass@@`，COL 0x7FC618 → TD 0x8193A8 → TD+8 名字逐字符读得
  `.?AVBuildingTypeClass@@`（EVIDENCE/t_final_verify.txt；脚本 work/t_final_verify.py；HouseClass 对照 TD 0x824500，名字不同）。
- 按纪律「类名只认 RTTI TD（COL+0xC→TD+8；读不到 fail-closed）」：U2 猜测无 TD 支撑，**作废**。

## P0_GATE_B U1 的关系（推进而非否定）
- U1 只确认「结构存在」；本卡把结论推进到「路径条件 + 运行时取值代入」：
  0x47C620 的 4 个字段判定 + 0xA8E9A0/0xA8E7AC/0xA8ED6B 代入 → 落点 0x47C738（FINAL_PATH.txt），
  且 0x47C427 的 `and al,1` 与工厂构造 path 的 `or al,1` 对齐 ⇒ 步兵恒命中。
- 与 U1 不冲突：U1 是存在性前提，本卡在其上追加可复算条件表达式；总判断仍按 [静态推断]（UNKNOWNS U6）。
