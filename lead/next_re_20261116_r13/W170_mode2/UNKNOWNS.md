# W170 · UNKNOWNS（分级未证清单）

> 只列真正未证/判不出的项；每条注明"排除了什么"与"下一条最有区分力的证据"。

## U1 · `CellClass+0x10A` 的引擎级名字与语义 `[未证]`

- **已证部分**：`0x5F6960` 用 `MapClass::GetCell(0x565730)` 由建筑坐标得 `CellClass*`，mode 2 读 `word [CellClass+0x10A]`（`EVIDENCE/Q1_followup_disasm.txt`）；该 word 经槽 `+0x464` 做 ±500/1500 偏置。
- **排除**：它不是建筑自身字段；不是 vptr/型号。
- **已试**：grep 主台账 `+0x10A` → 只有 §664-2 的同一处引用；Ghidra 无符号名。
- **下一条最有区分力的证据**：在 `.rdata` 找 `CellClass` 的 `WhatAmI`/`GetCell*` 实现里对 `+0x10A` 的读写，看它参与何种计算（本卡预算内未做）。

## U2 · `[this+0x55C]` 的 21 个对象是什么类 `[未证]`

- **已证部分**：mode 2 用两段 21 次循环（`0x43FA34 mov [esp+0x10],0x15`）遍历 `+0x55C` 起的对象指针数组，写 `[obj+0xD4]/[+0xFC]/[+0x178]`，门控 `[obj+0xC8]` 与 `[[obj+0xC8]+0x35C]`（`EVIDENCE/Q1_mode2_branch.txt:49-112`）。
- **排除**：它们不是建筑自身的 footprint cell 链节点（那条链只在 `0x5683C0/0x5687F0` 里改，mode 2 完全不调）。
- **已试**：反编译 `0x43FB20`（调用者）未给出类名（Ghidra 无 RTTI 符号）。
- **下一条最有区分力的证据**：真机在 `0x43FA62` 读 `[obj]` 的 vptr，与 `class_atlas_v2.tsv` 比对（本卡禁真机）；或静态对这些写点做 pcode 指向分析。

## U3 · `+0x700` / `+0xF0` / `+0x6ED` 的引擎级名字 `[未证]`

- **已证部分**：`0x43FA19` 写 word `[this+0x700]`；槽 `+0x464` 以 `[this+0xF0]&2` 为门；`0x43FA6E` 读 byte `[this+0x6ED]`，==0xF 时经 `call [vptr+0x68](0,0)` 结果==5 改用 0x10。
- **已试**：grep 主台账三字段 → 0 命中；capstone 反汇编只能给字节链。
- **下一条最有区分力的证据**：Ghidra decompile `0x43F180` 的整体 C（本卡已拿到 260 行上限，其中 mode2 段因 switch 展开不完整未直接命名）。

## U4 · `0x70E380/0x70E4B0` 的 9 路跳表各分支含义 `[未证]`

- **已证部分**：两函数都读计时起止字段、算帧差，按 `mode = [this+0x1A4]/[+0x1C0]`（1..9）跳 `0x70E48C/0x70E574`，产生插值值（`EVIDENCE/Q1_helpers.txt`）。
- **排除**：不是"空操作"——每个分支都有实际算术（`shl 8`、`imul 0x2aaaaaab` 等）。
- **下一条最有区分力的证据**：逐分支反汇编 + 与动画类型（RA2 AnimType）帧表对照。

## U5 · ②-b "10 格重叠"最终成因 `[未证]`（继承 R13_COMMON §2.3）

- 本卡未推进此条：mode 2 已证不碰 grid，故它**不是**"绕过摘链的摧毁机制"；销毁侧仍以 §912 的穷举排除为准；放置侧 `0x43F180` 有完整 can-place 检查。剩余未知仍是运行期字段读数（需真机 W172），本卡不越界。

## U6 · `0x5F4D30/0x5F4EC0` 所属类的精确类名 `[部分已证]`

- **已证**：二者在多个 vt 中被引用（`0x7E47B8/0x7E47BC` = `BulletClass@@` slot 53/54 邻域，另有 `0x7EDD94/0x7EF134/...` 等），是**多类共享的 Limbo/Unlimbo 包装**。
- **未证**：精确的 MSVC 类名（Ghidra 无 RTTI 符号；naive 最近 vt 反查噪声大，`EVIDENCE/Q2_vtclass_resolve.txt` 已记录为不可靠）。
- **下一条最有区分力的证据**：按 v2 规则重扫 `vtables_canonical.json` 的槽范围（本卡的 `w170_vtclass.py` 因只给起点无槽数而失败，已如实记录）。
