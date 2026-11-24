# UNKNOWNS.md — S15-K5 仍未具名的 17 行（跨卡叠加 K3/K4 后）

跨卡叠加后残余 17 行：`006D0F00,006D6070,006E1830,006E4790,006E47C0,006E6310,006EA3E0,006F1920,0070F120,00721270,00727AA0,0072DDB0,0072DEF0,00751590,00752460,00763610,00763690`。
K4 卡面“余 19”是未并 K3 delta 的现场口径；本卡按台账 §992（K3 +2）与 §996（K4 +2）复算后为 17。证据：`EVIDENCE/t0_baseline.txt`。

## 通用否定边界（本卡新增检查）

- YRpp 全树地址字面量：17 个残余地址均 0 命中；`EVIDENCE/yrpp_residual_addr_matches.txt`。
- 源码/调试串：`D:\ra2mdpost\TAction.CPP` / `D:\ra2mdpost\Event.CPP` 只有源文件路径，无函数/方法名；本机无 `D:\ra2mdpost` 源码树、无 PDB；`EVIDENCE/source_string_neighborhood.txt`、`EVIDENCE/source_string_xref_sites.txt`。
- EVA 串：80 个有效 xref 站点，0 个落在残余目标函数体内；`EVIDENCE/eva_xrefs.txt`。
- INI 串：仅 4 个通用哨兵 `<none>` 落在残余目标内，无触发器/动作/事件/标签专属键可定名；`EVIDENCE/ini_key_xrefs.txt`。
- 虚表/指针：`raw dword=0`、`.rdata` 槽命中 0；`EVIDENCE/residual_channel_matrix.tsv`（与 K3 `vtable_scan2.txt`、K4 `vtable_rtti_fixed.txt` 一致）。
- 调用者语义：74 个直接 call/jmp 站点中，命中者均为共享 helper / TActionClass 序列化 / Team AI / 播放配对子步；无一同时具备权威名通道与动作本体字节证据；`EVIDENCE/call_xrefs_residual_targets.tsv`。

## 逐条不可定原因

| entry | 不可定原因 | 证据 |
|---|---|---|
| `006D0F00` | 15B helper：置 `[this+0x5545]=1` 后虚调 `[vptr+0x38]`；`+0x5545` 远超 `TActionClass` size `0x94`，14 站点跨 Execute/动作 slave，非动作本体；无权威名。 | `EVIDENCE/disasm_targets/006D0F00.txt`; `EVIDENCE/call_xrefs_residual_targets.tsv` |
| `006D6070` | waypoint→坐标→相机目标字段 `+0xd64/+0xd68/+0xd74/+0xd78/+0xd7d` 的共享 helper；14 站点跨多类，`this` 字段远超 `0x94`；K3 U2 已排除为动作本体，本卡无第二命名通道。 | `EVIDENCE/disasm_targets/006D6070.txt`; `..\S15-K3\UNKNOWNS.md` U2 |
| `006E1830` | 唯一直接调用在动作 99 块 `0x6DE871`；函数体只做 waypoint→`CellStruct`→取格/取 building/terrain；YRpp 真动作 `0x6E18B0` 另址；无权威名。 | `EVIDENCE/disasm_targets/006E1830.txt`; `..\S15-K3\UNKNOWNS.md` U2 |
| `006E4790` | `strncpy(dst,src,0x1F)` 包装；3 站点在 Execute 的 TimerSet/TimerText 内联块；非 ACTION_FUNC 本体，无权威名。 | `EVIDENCE/disasm_targets/006E4790.txt`; `EVIDENCE/call_xrefs_residual_targets.tsv` |
| `006E47C0` | 两段 `rep movsd` 拷贝；3 站点与 `006E4790` 成对；无符号/虚槽/唯一 INI 键；无权威名。 | `EVIDENCE/disasm_targets/006E47C0.txt` |
| `006E6310` | TagType 名字查找/未命中时 `new 0xA4` + ctor；`<none>`/`none` 只是通用哨兵；YRpp `FindByNameOrID` 是 `0x6E5E70`，另址；无显式源码名。 | `EVIDENCE/disasm_targets/006E6310.txt`; `EVIDENCE/ini_key_xrefs.txt`; `..\S15-K4\UNKNOWNS.md` |
| `006EA3E0` | TeamClass::slot23 内 helper：写 `this+0x76..0x7e`，构造 `TagClass` 并虚调 `[vptr+0x20]`（事件 0x17）；`this` 偏移不属于 `TActionClass(0x94)`；无权威名。 | `EVIDENCE/disasm_targets/006EA3E0.txt`; `EVIDENCE/call_xrefs_residual_targets.tsv` |
| `006F1920` | TeamTypeClass 名字查找/未命中时 `new` + ctor；仅 `<none>` 哨兵、无唯一 INI 键；YRpp 无此地址；无权威名。 | `EVIDENCE/disasm_targets/006F1920.txt`; `EVIDENCE/ini_key_xrefs.txt` |
| `0070F120` | TalkBubble 显示子步；`0x6E4040` 内两次调用；YRpp `TalkBubble=0x6E4040` 另址；非动作本体，无权威名。 | `EVIDENCE/disasm_targets/0070F120.txt`; `..\S15-K3\UNKNOWNS.md` U2 |
| `00721270` | `this+0x18` 数组、`this+0x24` 计数的主题名索引 getter；`this=0xA83D10` 来自 `PrepareSaveToINI` mode=1；旧文档只写“ThemeClass@0xA83D10”语义，YRpp 无 ThemeClass 声明/方法地址；只有字节+调用上下文，不命名。 | `EVIDENCE/disasm_targets/00721270.txt`; `EVIDENCE/save_load_call_sites.txt`; `EVIDENCE/yrpp_residual_addr_matches.txt` |
| `00727AA0` | TriggerType 名字查找/未命中时 `new 0xB4` + ctor；`<none>` 为通用哨兵；YRpp `FindByNameOrID` 是 `0x727120` 另址；无权威名。 | `EVIDENCE/disasm_targets/00727AA0.txt`; `EVIDENCE/ini_key_xrefs.txt` |
| `0072DDB0` | PlayMovie 配对前半：查/置 `[0xB0FBE0]`，11×`LoadWholeFileEx` / 3×`CreateFromFile`；`PlayMovie` 真身 `0x6E16D0` 另址；给任一叫 PlayMovie 会错配后半。 | `EVIDENCE/disasm_targets/0072DDB0.txt`; `..\S15-K3\UNKNOWNS.md` U2 |
| `0072DEF0` | PlayMovie 配对后半：清 `[0xB0FBE0]` + `delete` 释放；与 `0072DDB0` 共享 flag；无权威名。 | `EVIDENCE/disasm_targets/0072DEF0.txt` |
| `00751590` | Voc 索引→名字串 helper：`[0xB1D37C]/[0xB1D388]` + `Invalid Voc`/`<none>`；`<none>` 是通用哨兵，YRpp `FindIndex=0x7514D0` 另址；EVA 串无交；无权威名。 | `EVIDENCE/disasm_targets/00751590.txt`; `EVIDENCE/save_load_call_sites.txt`; `EVIDENCE/eva_xrefs.txt` |
| `00752460` | Vox 索引→数组元素指针：`[0xB1D4A4]/[0xB1D4B0]` + `none`；YRpp `VoxClass::GetName` 显式地址为 `0x753330`，且该处返回值/边界字节与本行不同；`0x752460` 无独立命名通道。 | `EVIDENCE/disasm_targets/00752460.txt`; `EVIDENCE/save_load_call_sites.txt`; `YRpp/VoxClass.h` |
| `00763610` | `wsprintfA` 串拼 helper，被 `PrepareSaveToINI` 与 TeamType 块多处调用；无源码名、无唯一 INI 键。 | `EVIDENCE/disasm_targets/00763610.txt`; `EVIDENCE/call_xrefs_residual_targets.tsv` |
| `00763690` | 两个 CRT 包装各 2 次（`0x7C990E`/`0x7C97D3`），被 `LoadFromINI` 与 TeamType 块调用；无字符串/虚槽/源码地址锚。 | `EVIDENCE/disasm_targets/00763690.txt`; `EVIDENCE/call_xrefs_residual_targets.tsv` |

## 结论

本卡未定出任何名字，**仍差 2**。不写 `Class::sub_XXXXXXXX` 充数，不把共享 helper 当动作实现体，不把语义描述升成权威方法名。
