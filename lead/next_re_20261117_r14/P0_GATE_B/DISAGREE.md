# P0-GATE-B · DISAGREE.md

分级仅 `[已证]` / `[静态推断]` / `[未证]`。

## D1 — 卡面假设「闸门在 `0x47C3D0` 选择子=1 分支」：放置路径上**证伪**
- 卡面 §2/§988 建议方向：`0x47C3D0` 中「选择子=1」分支可能是拒绝闸。
- 本卡实测：
  - `0x47C3D0` 体内选择子=1 只读 `[cell+0xE8]`（head B/桥上链），**且函数内 WhatAmI 虚调用=0、不含任何步兵判定**（`EVIDENCE\t_final_verify.txt`、`47c3d0_clean_full.txt`）。即便选择子=1，也只是「head B 上按距离取最近对象」，不是步兵专用闸。
  - 全镜像 5 个能置选择子=1 的 `setg` 站点（`0x4B2BCD`/`0x4B30B2`/`0x516A41`/`0x6A221D`/`0x6A2702`）归属 `0x4B2630`/`0x5164D0`/`0x6A1C80`（运动/Locomotion 函数），**与放置主循环 `0x43F180` 与 `0x47C620` 的 10 个调用点零交集**（`EVIDENCE\t2_setg_containing.txt`）。
  - `0x47C620` 内两次 `0x47C3D0` 调用（`0x47C738`/`0x47C805`）压栈 `push 0` ⇒ 选择子恒 0，只扫 head A。
- 裁定：`[已证]`（结构）。卡面假设属「候选假设」（纪律 12），本卡不据此收口；真正的闸在 `0x47C620` 的类型无关占用判定。§978「head B 在放置路径结构性关闭」的结论与此一致，不推翻。

## D2 — §983「`0x47C620` 对步兵放行」：字节层成立，**函数层须收窄**
- §983 `[已证]`：「15/1 一次未被比较」——本卡完全复现（比较集 {6,2,0x24}）。
- 但该节据此写的「静态允许」若被读成「`0x47C620` 不会拒绝步兵」则过强：`0x47C620` 在 `0x47C73F` 用**类型无关**的「head A 有任一对象即拒」判定（`0x47C3D0` 返回非 0），步兵会被该闸命中而无需比较 WhatAmI。
- 裁定：字节层 `[已证]`；「函数对步兵放行」`[静态推断]`（受 U1 可达标志影响）。建议台账/后续卡表述为「比较集不含 15/1，但存在类型无关占用闸」。`GATE.md` T2-b。

## D3 — §983「`0x47C620` 全函数 640 B」：偏小
- 本卡线性反汇编 `0x47C620..0x47CA79`（最后 `ret 0xc`），约 2656 B / 489 真实指令（含 `jne 0x47CA70` 远跳分支）。§983 的「640 B 逐指令」应为其测量的前段。
- 裁定：`[静态推断]`（长度口径差，不影响 §983 比较集结论——远跳分支 `0x47CA70` 只 `mov al,1` 放行，无新增 WhatAmI 比较）。证据 `EVIDENCE\47c620_full2_disasm.txt`。纪律 B：截断≠不存在。

## D4 — 「全镜像有 WhatAmI 15/1 比较」≠「放置路径有」
- 全镜像 WhatAmI 虚调用 1109 处，其中后随 `cmp 15` 107 处、`cmp 1` 172 处（基线证据 `EVIDENCE\t3_whatami_scan.txt`）。若只报「镜像里存在步兵比较」属空判据（违纪律 1 先测基线 + 纪律 11 门控覆盖须给位置关系）。
- 放置链三函数 `0x43F180`/`0x449440`/`0x47C620` 内此类比较 = 0。裁定 `[已证]`。

## D5 — 调用点数 ≠ 调用者函数数（纪律 8）
- `0x58865F`/`0x58886E` 分别在 `0x588570`/`0x588750`；`0x6D5A98`/`0x6D5D33` 分别在 `0x6D59D0`/`0x6D5C50`。10 个调用点分属 9 个不同函数。卡内 `CALLSITES.tsv` 用「函数区间包含」逐点判定（纪律 D），未用 `entry_at_or_before`。裁定 `[已证]`。

## D6 — `COVERAGE\coverage.tsv` 中 `00449440` 的语义登记与盘面字节不符 `[已证]`
- 盘上现值：`00449440  S12  BuildingClass::vslot107  [静态推断] Production/Economy member (rtti-vftable)  [静态推断] … conflict=1`。
- 本卡字节级证据：BuildingClass 主虚表 `0x7E3EBC + 0x1AC = 0x449440`（RTTI COL `0x7FC360`→TD `0x818D60`→`.?AVBuildingClass@@` 已确认）；`0x449440` 全文（`EVIDENCE\t4_chain_verify.txt`）取 `CellStruct*`、`this+0x520`、`this+0x21c`，`call 0x5657A0`→`call 0x47C620`→`neg/sbb/and 0xF9/add 7` 映射返回值 `{0,7}`；放置循环 `0x43F218`/`0x43F678` 的 `call [vptr+0x1AC]` 后 `test eax; jne fail`。
- ⇒ 该函数是**放置 can-place 查询**，不是「Production/Economy member」。不属本卡写域（不得改 coverage），仅在此点名并建议后续归并卡以字节证据更正该行语义/grade；本卡 `coverage_delta.tsv` 因此不复制该行（避免制造重复/conflict）。证据 `EVIDENCE\t4_vtable_check.txt`、`t4_chain_verify.txt`。
