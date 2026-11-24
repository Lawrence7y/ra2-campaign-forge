# P0-GATE-B · UNKNOWNS.md

分级仅 `[已证]` / `[静态推断]` / `[未证]`。

| # | 未闭环内容 | 分级 | 证据/为何未闭环 |
|---|---|---|---|
| U1 | **拒绝闸 `0x47C738` 在真机「步兵格」上的可达性**：闸的结构 `[已证]`，但它前面有 HouseClass 标志门控 `[arg2+0x16BF]`/`[0x16BE]`/`[0x16B7]`/`[0xE58]` 与全局 `[0xA8E9A0]`（`0x47C640/0x47C6DD/0x47C6F9/0x47C701`）。这些字段的**类身份与写点未做双支撑**（纪律 4），静态无法判当前 mode 下取值 ⇒ 本卡只能判「结构存在」`[已证]`、「真机那一格确由此闸拒」`[静态推断]`。需一张卡追这些字段写点 + 取值域，或真机在 `0x47C853` 下断点。 | `[静态推断]` | `EVIDENCE\47c620_full2_disasm.txt`、`GATE.md` T2-b |
| U2 | `0x47C620` 的 arg1 `[esp+0x1c]`（比较 `-1`/`0x7E`，作表索引 `0x89EA40`）与 arg2 `[esp+0x20]`（读 `+0x16BF/+0xE54/+0xE58`）的**精确语义**：arg2 疑为 `HouseClass*`（与 `0x449440` 传参 `this+0x520` 一致），但未按该类写点+读点定谳，不写死。 | `[未证]` | `GATE.md` T2-b；纪律 4/5 |
| U3 | `0x47C3D0` 的 `[obj+0x14]&1` 过滤位语义：疑为 ObjectClass「在册/活动」标志（`R14_COMMON §4.6` 消费端第③道也是 `[+0x14]&1`），但本卡未追该类写点。若步兵此位为 0，则本闸对步兵不命中——这是 U1 之外第二个可推翻本结论的变量。 | `[未证]` | `EVIDENCE\47c3d0_clean_full.txt` |
| U4 | 第二闸 `0x47C805→0x47C818→cmp eax,6@0x47C825` 的完整分支树（命中后再按 WhatAmI 复核），本卡只列到结构级，未逐叶打全（纪律 B 要求「分支什么都不做」须入口到 ret 逐条；本卡不主张该分支为空）。 | `[静态推断]` | `EVIDENCE\47c620_full2_disasm.txt` |
| U5 | `0x47C4D0`（`CellClass::FindObjectOfType`）与 `0x47C520`/`0x47C550`/`0x47C5A0` 的完整语义：本卡只用到 `0x47C620` 内 `call 0x47C4D0`(`push 0x24`) 这一处，未逐函数解剖。 | `[未证]` | `EVIDENCE\47c3d0_full_disasm.txt`（含这些相邻函数反汇编） |
| U6 | RTTI fail-closed：`0x449440` 属 BuildingClass vtable `0x7E3EBC`（COL `0x7FC360`→TD `0x818D60`→`.?AVBuildingClass@@` 已确认），但 `0x449440` 自身的**函数名**未从 RTTI/源码定出，卡内只称「vslot107 can-place 查询」，不猜名。 | `[未证]` | `EVIDENCE\t_final_verify.txt`、`t4_vtable_check.txt` |
| U7 | `0x43F180` mode 2（`0x43F9A6`）与短路径 `0x43F5EF`（`[house+0x1571]` 门控 → `operator new 0xB0`）语义：本卡聚焦 mode1/3 挂链路径，未穷尽这两支。 | `[未证]` | `EVIDENCE\43f180_full_disasm.txt` |
| U8 | 真机侧佐证（§988 已证 L1/L2/L3 全绿、红格=(113,63) 步兵格、2/2 落格被拒）：本卡无法静态复算 `0x47C853` 是否在那两次点击中被命中；建议后续真机在该地址下断。 | `[未证]` | 台账 §988；本卡纯静态授权 |
