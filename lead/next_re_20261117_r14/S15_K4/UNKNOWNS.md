# UNKNOWNS.md — S15-K4 未具名/不可定清单

本次现场重算仍有 21 行 `sub_`；本卡定出 2 行，余 19 行如下。所有行均未写台账、未编名。

## U-K3 · K3 已报的 2 行本卡不重签

| entry | 不可定原因（本卡口径） | 证据 |
|---|---|---|
| `006E2A10` | K3 用 YRpp `ACTION_FUNC(DeleteTrigger,0x6E2A10)` + 字节语义；本卡未找到第二条独立“命名”通道（全项目裸/带零十六进制 grep 仍只命中 YRpp 同表），按派卡规则保持 `sub_`，不重复计入本卡 delta。K3 delta 已单独交付，跨卡统计会计入。 | `S15-K3/EVIDENCE/yrpp_addr_matches.txt`; `EVIDENCE/source_grep_bare_hex.txt` |
| `006E2AA0` | 同上，YRpp `ACTION_FUNC(ForceTrigger,0x6E2AA0)` 是唯一命名通道；字节体只能证明“强制触发”，不能独立给出方法名。 | 同上 |

## 其余 17 行：具体不可定原因

| entry | 不可定原因（本卡实查） | 证据 |
|---|---|---|
| `006D0F00` | 体仅 15B：置 `[this+0x5545]=1` 后虚调 `[vtable+0x38]`；14 调用站点随 Execute 内联 timer/tag 分支出现，无 YRpp 地址字面量、无虚表槽命中；字段 `+0x5545` 超出 TActionClass size 0x94，是宿主级 helper，非动作本体。 | `EVIDENCE/targets_disasm.txt`; `EVIDENCE/targets_xrefs.txt`; `EVIDENCE/source_grep_bare_hex.txt` |
| `006D6070` | waypoint→cell→相机目标字段 `+0xd64/+0xd68/+0xd74/+0xd78/+0xd7d` 的共享 helper；14 站点/多类调用、写点远离 TActionClass size；K3 U2 已复核，无权威名。 | `S15-K3/UNKNOWNS.md` U2; `EVIDENCE/targets_xrefs.txt` |
| `006E1830` | 唯一调用者是 ACT99 handler `0x6DE871`，体只做 waypoint→`CellStruct`→`TryGetCellAt` 与取格building/terrain；声音播放由同 handler 的 `0x68BD00` 完成；YRpp 该动作真身是 `0x6E18B0`，本行无权威名。 | `S15-K3/UNKNOWNS.md` U2; `EVIDENCE/targets_disasm.txt` |
| `006E4790` | `strncpy(dst,src,0x1F)` + 末字节置 0；3 个调用点全在 Execute 的 TimerSet/TimerText 内联块，仅有语义无方法名；不是 ACTION_FUNC 本体。 | `EVIDENCE/targets_disasm.txt`; `EVIDENCE/targets_xrefs.txt` |
| `006E47C0` | 两段 `rep movsd`（8 dword）拷贝；3 个调用点与 `006E4790` 成对出现于 Execute 内联计时器块；无符号/虚槽/字符串锚。 | 同上 |
| `006E6310` | `TagTypeClass` 名字查找器：比 `<none>`/`none`、扫 `[0xB0E780]`、miss 时 `new 0xA4`+ctor；YRpp `FindByNameOrID` 已占 `0x6E5E70`，本行无显式源码名；不能据“find_by_name”合同自造 `FindByNameOrCreate`。 | `EVIDENCE/targets_disasm.txt`; `EVIDENCE/vtable_rtti_fixed.txt`; `EVIDENCE/source_grep_bare_hex.txt` |
| `006EA3E0` | 唯一直接调用者在 `TeamClass::AI/slot23` 宿主 `0x6E9140` 体内；函数构造 `TagClass`（`call 0x6E53A0`）并虚调 `[edx+0x20]`，属 Team AI helper，非 TActionClass 动作体；无权威名。 | `EVIDENCE/vtable_rtti_fixed.txt`; `EVIDENCE/targets_xrefs.txt` |
| `006F1920` | 与 `006E6310` 同骨架但数组为 `[0xA8ECA4/0xA8ECB0]`、new 后调 `0x6F06E0`（TeamTypeClass ctor，RTTI 锚定）；无显式源码方法名。 | `EVIDENCE/targets_disasm.txt`; `EVIDENCE/vtable_rtti_fixed.txt` |
| `0070F120` | 写 talk-bubble 全局 + 虚调显示；YRpp `TalkBubble` 真身 `0x6E4040` 内调本行 2 次；K3 U2 已定为显示子步，非动作本体。 | `S15-K3/UNKNOWNS.md` U2; `EVIDENCE/targets_xrefs.txt` |
| `00721270` | GetMode=1 的主题名查找 helper：从 `[0xA83D10]+0x18/+0x24` 取表/计数，含 `none` 回退；只被 `TActionClass::PrepareSaveToINI` 调用，无 YRpp 方法地址。 | `EVIDENCE/targets_disasm.txt`; `docs/re/trigger_system_manifest.md` §5.1 |
| `00727AA0` | `TriggerTypeClass` 名字查找/新建器：比 `<none>`/`none`、new 后 `call 0x726C80`（TriggerTypeClass ctor，RTTI 锚定）；YRpp `FindByNameOrID` 是 `0x727120`，本行无权威名。 | `EVIDENCE/targets_disasm.txt`; `EVIDENCE/vtable_rtti_fixed.txt` |
| `0072DDB0` | PlayMovie 配对前半：检查并置位 `[0xB0FBE0]`，11×`LoadWholeFileEx`/3×`CreateFromFile`；被 Execute 与 `PlayMovie 0x6E16D0` 共同调用，非 ACTION_FUNC 本体。 | `S15-K3/UNKNOWNS.md` U2; `EVIDENCE/targets_xrefs.txt` |
| `0072DEF0` | PlayMovie 配对后半：首清 `[0xB0FBE0]`，8×`CRT::_delete`；与 `0072DDB0` 共享 flag，给任一叫 PlayMovie 都会错配。 | 同上 |
| `00751590` | GetMode=3/0x26 的 Voc 名查找：`[0xB1D37C]/[0xB1D388]` 数组/计数 + `Invalid Voc`/`none` 回退；YRpp `VocClass::FindIndex` 是 `0x7514D0`，本行无权威名。 | `EVIDENCE/targets_disasm.txt`; `docs/re/trigger_system_manifest.md` §5.1; `YRpp/VocClass.h` |
| `00752460` | GetMode=4 的 Vox 名查找：`[0xB1D4A4]/[0xB1D4B0]` 数组/计数 + `none` 回退；YRpp `VoxClass::GetName` 是 `0x753330`，本行无权威名。 | `EVIDENCE/targets_disasm.txt`; `YRpp/VoxClass.h` |
| `00763610` | `%c%c` 与全局 `[0xB72654]` 的串拼 helper；3 个 PrepareSaveToINI 调用 + TeamType 块调用；无源码名，且 `0x68BFCC` 是 tail-jmp 而非函数入口。 | `EVIDENCE/targets_disasm.txt`; `EVIDENCE/targets_xrefs.txt` |
| `00763690` | 只调 `0x7C990E`/`0x7C97D3` 各两次的包装；被 LoadFromINI 和 TeamType 块调用，无字符串/虚槽/源码地址锚。 | 同上 |

## 通用否定边界

- 21 条目标在 `.rdata` 的 dword 虚表槽命中均为 0（`EVIDENCE/vtable_rtti_fixed.txt`），故“槽即函数”这条通道对本组无增量；这不等于“不是函数”。
- 全项目裸十六进制 grep 有语义描述（如 find_by_name、getter、helper）但无第二类权威方法名；按纪律不把语义描述升成类名。
