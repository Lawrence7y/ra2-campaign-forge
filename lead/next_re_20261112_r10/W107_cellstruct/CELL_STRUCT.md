# W107 · CellClass 字段布局报告（stride 0x148）

> 方法：自建 Ghidra 库（`_ghidra\ghidra_WIN-B7KIC1TNL6R`，分析 241s，成功）。
> 脚本 `ghidra_scripts\CellFields.java` 三通道：① 全程序反汇编扫描 `[reg+disp]`（排除 esp/ebp、disp<0x400），1,128,051 条指令 / 1,050,294 次访问 / **169 个函数访问 +0xE4** / **137 处 0x148**（`EVIDENCE\access_dump.tsv`、`stride_0x148_sites.txt`）；② 反编译 169 函数 + 锚点，**参数别名溯源**区分 cell 指针 / 链上对象 / 加载值（`EVIDENCE\decomp_all.c`）；③ 按 A(坐标+链)/B(链+链形状)/A2(坐标) 组合并（`EVIDENCE\cell_fields_merged.txt`）。
> 复现命令：`& D:\ghidra\ghidra_12.1.4_PUBLIC\support\analyzeHeadless.bat <卡目录>\_ghidra ghidra_$env:COMPUTERNAME -process gamemd.exe -noanalysis -scriptPath <卡目录>\ghidra_scripts -postScript CellFields.java`

## 1. 分组判据（防撞车核心）

- 函数入参经签名行解析为 P1..Pn；`x=param_1` 传递 P 标签，`x=*(param+0xE4/0xE8)` 得 OBJ 标签，`x=*(...)` 其它得 VAL 标签。
- **A 组** = P 上既有 word 读 `+0x24/0x26` 又有 `+0xE4/0xE8`（坐标+链双签名，最硬）。
- **B 组** = P 上 `+0xE4/0xE8` 且链上对象走 `+0x2C`(WhatAmI 虚表)/`+0x30`(next)（链形状）。
- **A2 组** = 仅坐标签名（纯 cell 访问器）。
- **C 组（排除）** = 只有 `+0xE4` 无形状：50 个，含另一类比较运算符族（`return iVar4 < *(int*)(param_1+0xe4)`）、float 字段族（`*(float*)(param_1+0xe4)`，0x13475 域）、密集大结构族（FUN_0048ebf0/490490/511850：disp 4..340 连续）—— 明显非 cell。清单在 `cell_fields_merged.txt` 尾部。
- 已知撞车 `0x4358A9`（Lead 所指其它类构造）所在函数同样落入 C 组被排除 ✓。

## 2. CellClass 字段表（A/A2/B 组合并，全部偏移有 ≥1 条反编译级证据）

| 偏移 | 大小 | 等级 | 语义推测 | 证据函数数 | 例句（VA: mnemonic，出自 EVIDENCE\access_dump.tsv） |
|---|---|---|---|---|---|
| +0x00..0x23 | 32 | 未证 | 无任何直接访问（vtable 未被这些函数调用） | 0 | ——（留空） |
| +0x24 | word | **[已证]** | 行 row（世界坐标=v*256+128，Lead L1 复核成立） | 8 | `47DD70: MOVSX EDX,word ptr [ESI+0x24]`；`47EA10: MOVSX EAX,word ptr [EBX+0x24]` |
| +0x24(合读) | dword | [已证] | row+col 打包 dword 读（比较/拷贝用） | 8 | `47CC81: MOV ECX,dword ptr [ESI+0x24]`；`47E925: MOV EAX,dword ptr [EBX+0x24]`；另 `LEA EAX,[ESI+0x24]` 取址传参 ×5 函数 |
| +0x26 | word | **[已证]** | 列 col | 7 | `47DE8A: MOVSX EAX,word ptr [ESI+0x26]`；`47EB25: MOVSX EDX,word ptr [EDI+0x26]` |
| +0x38 | dword | [静态推断] | 与 +0x24 联动的计数/索引（A2 内与坐标同函数读写） | 4 | `47C0D9: MOV EAX,dword ptr [ESI+0x38]`；`47CC3E: MOV dword ptr [ESI+0x38],EBP` |
| +0x44 | dword | [静态推断] | 句柄/索引，**-1 = 空**（多处写 0xFFFFFFFF） | 5 | `47D378: MOV dword ptr [ESI+0x44],0xffffffff`；`47D849: 同` |
| +0x4C | dword | [静态推断] | 未定 | 1 | decomp `FUN_00483c80 :: *(undefined4*)(param_1+0x4c)` |
| +0x50 | dword | [静态推断] | 未定 | 1 | decomp `FUN_0047c620 :: *(int*)(param_1+0x50)` |
| +0xA0 | dword | [静态推断] | 未定 | 1 | decomp `FUN_0065dd30 :: *(int*)(param_1+0xa0)` |
| +0xA5 | byte | [静态推断] | 未定 | 1 | decomp `FUN_0065dd30 :: *(char*)(param_1+0xa5)` |
| +0xE0 | dword | [静态推断] | 链 A 的伴生字段（与 +0xE4 同函数出现） | 1 | decomp `FUN_0065dd30`；`9094 行: FUN_004a1d90(*(param_1+0xe0),*(param_1+0xe4))` |
| +0xE4 | dword | **[已证]** | 链 A 头（对象链，节点 next=+0x30） | **23** | `47C52A: MOV ESI,dword ptr [ECX+0xe4]`（Lead 复核一致）；`47EACF: MOV dword ptr [EDI+0xe4],ECX` |
| +0xE8 | dword | **[已证]** | 链 B 头（参数选链：`param_3!=0 → +0xE8`） | **10** | `47C4E3: MOV ESI,dword ptr [ECX+0xe8]`；`47E91F: MOV dword ptr [EBX+0xe4],EBP`/`47E90B: [EBX+0xe8],EBP` 清链 |
| +0xEC | dword | [静态推断] | 小整数状态机（写 0/3/5/0xa） | 5 | `47D53E: MOV dword ptr [ESI+0xec],0x3`；`47D8B0: CMP dword ptr [ESI+0xec],0xa` |
| +0x100 | dword | [静态推断] | 未定（仅写） | 1 | `47DA7B: MOV dword ptr [EAX+0x100],ECX` |
| +0x11B | byte | [已证] | 有符号 byte（MOVSX），Lead `0x00429E5F` 复核一致 | 2 | `47D3CA: MOVSX EAX,byte ptr [ESI+0x11b]`（FUN_0047d2b0 内 ×20+）；`47ECEB: MOVSX EAX,byte ptr [ESI+0x11b]` |
| +0x11C | byte | [已证] | 子类型/状态，与 2/3/4 比较 | 6 | `47CFBB: CMP byte ptr [ESI+0x11c],0x2`；`47D82A: CMP byte ptr [ESI+0x11c],0x4` |
| +0x11E | byte | [已证] | 状态字节，写 0x0/0x9 | 2(+1) | `47E05E: MOV byte ptr [ESI+0x11e],0x9`；`47D37F: MOV byte ptr [ESI+0x11e],0x0`；Lead 证据链另见 `4838E0: CMP [ECX+0x11e],0x10` 侧写 |
| +0x124 | byte | [静态推断] | 位掩码（TEST 0x3F） | 1 | `47C85F: TEST byte ptr [EDI+0x124],0x3f` |
| +0x128 | byte | [静态推断] | 未定 | 1 | decomp `FUN_00487720 :: *(char*)(param_1+0x128)` |
| +0x12C | dword/byte | [静态推断] | dword 读 + LSB byte 读（低字节复用） | 1 | `47ECA4: MOV EAX,dword ptr [ESI+0x12c]`；decomp `*(byte*)(param_1+300)` |
| +0x140 | dword | **[已证]** | 位域标志（OR 0x20000；`test ah,1`=Lead 0x00429E54） | 5 | `47DA88: OR dword ptr [ESI+0x140],0x20000`；`47C970: MOV EAX,dword ptr [EDI+0x140]` |
| +0x144..0x147 | 4 | 未证 | 全程序无访问 → 对齐填充或未用尾字段 | 0 | —— |

## 3. stride 0x148 复核（第 6 问）

- 直接站点 137 处，含 Lead 两条：`0x005663C3: push 0x148`、`0x00566AA6: add ebp,0x148`（`stride_0x148_sites.txt`）。
- 合并表最大访问端 = `+0x140(dword)` → **maxEnd=0x144 ≤ 0x148** ✓。0x148 = 0x144 上取整到 8 字节 —— 与「最后字段+对齐」自洽，无越界矛盾。
- RTTI 正面验证（Lead 补充）：CellClass vtable = `0x007E4EC0/C8/D0/EEC`（`_lead_rtti_map.json:260-263`）。对 VT 常量 `C0 4E 7E 00` 全文件字节搜索得 4 个写入点，修正 ImageBase=0x400000 后 VA=`0x47B38C/0x47BB92/0x47BD8C/0x483A4B`（自制 PE 头解析脚本，输出见 EVIDENCE）。**±160B 内无 `push 0x148`** → 构造函数与 stride 的直接绑定未闭合（写入点可能是析构/二次赋值），见 UNKNOWNS。但这 4 点全部落在 0x47B–0x483 cell 方法簇内，旁证该簇 = CellClass 方法。

## 4. 哨兵可用性结论

- `obj+0xE4` / `obj+0xE8` 双链、`+0x30` next、`+0x24/0x26` 坐标、`+0x140` 标志、`+0x11B/0x11C/0x11E` 字节 —— 本表可直接支撑崩溃哨兵的字段通路；`+0x30`/`+0x2C` 属**链上对象**（AbstractClass 侧），不是 cell 字段，勿混用。
- A 组三重签名函数（FUN_0047dd70/47e8a0/47ea90：坐标+双链读写俱全）可作为哨兵的活体参照实现。

## 5. 撞车排除处置（Lead 第 3 条）

- 静态侧：C 组 50 函数已隔离（判据=坐标/链形状缺失），`0x4358A9` 族在内。
- RTTI 侧（本轮新增硬判据）：候选函数若写**已知 vtable 常量**（vt2name 命名类）→ 该 this 非 CellClass。已对 CellClass 自身 VT 常量完成 4 点定位；对其余 1304 个 vtable 的批量判据脚本列为 UNKNOWNS 后续项。

## 6. 局限

- 溯源基于反编译文本的别名传播（straight-line、last-assign-wins）；循环内重赋值可能使个别 OBJ 标签退化为 OTHER（会**漏收**而非误收，偏保守方向）。
- 经"加载值"再解引用的嵌套访问（`*(int*)(*(int*)(p+0x24)+0xe4)` 外层）未归入 cell 表 —— 该形态本就不是直接 cell 字段。
- 约 20 个同时读 `+0xE4` 与 `+0xE8` 但无形状/坐标签名的函数（0x65Axxx 族等）保守留在 C 组，未计入合并表 → `+0xE4` n=23、`+0xE8` n=10 是**下界**。
