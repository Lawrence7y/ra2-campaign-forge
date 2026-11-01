# R-044 · L-4 大块突破：`ScriptTypeClass`（0x234）Save 载荷与「计数 + TeamType 索引数组」簇

镜像：`gamemd.exe` sha256 `73201cc0…f67476`（只读）。全部字节窗口本轮重 dump；
**地址事实源 = 单次整段 `md.disasm()` 线性解码 + 独立 raw 字节定位双坐实**，
不再采用逐块 resync 游标（本轮坐实其正是 R-041/R-042 反复出现的地址漂移根因）。
门禁 `tools/r044_scripttype_block.py`：**9/9 字节断言 PASS**（G0 指纹、X10 结构性具名不入分母）；
变异 `tools/mutate_r044_gate.py`：**15/15 killed（精确集合）**。原始输出 `r044_scripttype_block.txt`。

## 1. 结论（L-4：564 字节大块「装什么、存什么」）

`ScriptTypeClass` 的**自有 Save 载荷只有一个 dword**：`+0xA0` = 其数组的**计数**。
数组本身（`+0xA8` 起，条目步长 8）**不进 Save**，运行期由 fixup 重建（见 §3）——
与 R-042 `TEventClass+0x54`「运行时缓存不进 Save」同一族现象，但这里数组是**索引表**
而非指针缓存。类型层三个字符串字段（基类 `AbstractTypeClass::Save`）照常序列化：
`Name(+0x24)`、`+0x64`、`+0x3D`（后者经 `add esi,0x3d` 定位，与 kb/11 一致）。

⇒ L-4 的 564 字节被解成：**基类字段（含 4 个 facet vptr + Name 等串）+ 自有计数 `+0xA0` +
运行期索引数组 `+0xA8`（步长 8，TeamType 注册表索引）**。Save 侧只序列化「计数」，
数组由地图 TeamTypes 装载后 fixup 重编号填充。

## 2. 证据链（字节；地址双坐实）

| 断言 | 站点 | 钉住的字节事实 |
|---|---|---|
| X1 | 0x691F80 / 0x691F70 / 0x816FBC | GetSize slot12=`mov eax,0x234`；WhatAmI slot11=`mov eax,0x1B`；名字表第 0x1B 对 word0='ScriptType'/word1=0x1B |
| X2 | 0x691E00..0x691E20（0x21B） | Save slot13 整窗：`call 0x410BE0`（基类，rel32 复算）+ `mov eax,[esi+0xA0]`@0x691E0E（`8b86 a0000000`）+ `call 0x4A1D50`（dword writer，rel32 复算）→ **自有载荷=+0xA0 计数，仅此一项** |
| X3 | 0x410BE0..0x410BE0+0x34（0x34B） | `AbstractTypeClass::Save`：先 `call 0x410410`，再三串走 `0x4A1DB0` @ +0x24/lea+0x64/add+0x3D（三个 call 均 rel32 复算到 0x4A1DB0） |
| X4 | 0x4A1DB0（0x15B） | 串 writer 指纹 `…83c9ff 33c0 f2ae`=`repne scasb` strlen 起手段 ⇒ 按串长序列化 |
| X5 | 0x4A1D50（0x0B） | dword writer=`mov eax,[esp+4]; lea edx,[esp+4]; push 4; push edx`（与 R-042 TEvent Save 同一 writer） |
| X6 | 0x691DB4（0x16B） | slot5 Load 尾装主 vptr 0x7F1008 + 三 facet 0x7F0FEC/0x7F0FE4/0x7F0FDC（+0/+4/+8/+0xC；facet 间距 −0x1C/−0x24/−0x2C） |
| X7 | 0x691E30..51B + 0x691EB2/0x691E98/0x691E77/0x691E60/0x691E5A | fixup slot10：门 `call [arg_vt+0x2c]`→`cmp eax,0x23`（TeamType）；`mov esi,[0xA8ECB0]`@0x691E5A、`lea edx,[ebx+0xA8]`@0x691E60、`cmp [edx-4],0x12`@0x691E66；`add edx,8`@0x691EB2（步长8）、`dec eax; mov[edx],eax`@0x691E98（重编号）、`mov ecx,[0xA8ECA4]`@0x691E77（TeamTypes 向量=R-041 同一对全局） |
| X8 | 0x816FFC | 名字表第 0x23 对='TeamType'/0x23 ⇒ X7 的 WhatAmI 门 0x23=TeamTypeClass*；数组条目=**TeamType 注册表索引(int)**，TeamType 被移除时索引前移重编号 |
| X9 | 全区 census | `0x691000..0x692100` 内 `[reg+0xA0]`(disp32)：存储=`{0x6916C7,0x6918CF,0x691947,0x691A5B,0x691C8B}`、读取=`{0x691547,0x69191F,0x691940,0x691E0E,0x691E4B,0x691EAB}`（Save 读 0x691E0E 阳性对照在列） |
| X10 | symbols.json | 【结构性】主 vtable 0x7F1008 吻合；slot5/Save/GetSize/WhatAmI/fixup 五址 ∈ ScriptTypeClass.vfuncs |

## 3. fixup（slot10 @0x691E30）语义（字段级，不多推）

入参 `[esp+0xC]`（ebp）若为 TeamType（WhatAmI 门 `==0x23`），则遍历本类条目数组
`[+0xA8]`（步长 8，`[+0x9C]=条目A/[+0xA4]=条目B` 型双字段条目），在**全局 TeamTypes
注册表向量** `[0xA8ECA4]/[0xA8ECB0]`（R-041 X4 同一对）里线性找 ebp 的下标 ecx；
命中后对每个 `>ecx` 的条目索引做 `dec`、`==ecx` 的清零——即 **TeamType 从注册表被删时，
把引用它的 ScriptType 条目前移重编号**。门与步长/重编号三处字节独立钉牢。

## 4. 本轮抓到并修复的坑（诚实账）

1. **手敲 hex 漏 `00` 尾巴**：`ret 4` 是 `c2 04 00` 三字节，X2/X3 首版写成 `…c204`、
   X4/X5 写长了 2/1 字节 ⇒ 恒假 FAIL。机器 dump 正确窗（X2=0x21、X3=0x34、X4=0x15、X5=0x0B）后修。
2. **rel32 基址笔误**：`Save→基类` 下一条指令是 `+0x0E`（我写 `+0x0A`）——G-55 同型。
3. **★ resync 漂移真实机制——用消融实验纠正了两条错误自诊（本轮最大发现）**：
   本轮首版把 `add edx,8` 的归属写错（漂到 0x691F34）。**两次错误自诊都被推翻**：
   - 本轮 docstring 初稿猜「16 字节窗口截断指令致漂移」——**消融证否**：窗口放大到
     255B 覆盖整段仍漂到同一假址 0x691F34，窗口大小无关。
   - R-042 台账当时记「跳字节时忘了同步 PC（少推进）」——**方向恰好相反**：真实缺陷是
     助手同时维护**两个游标**（缓冲偏移 o 与地址 a），每解一条 `o+=size; a+=size`，
     且把 `a+o` 喂给 disasm ⇒ 地址以 2× 指令长前进（第一步即 push ebx@0x691E30 之后
     push ebp「显示」在 0x691E32 而非 0x691E31）。
   **正确形式**：只传一个锚点（`start+o`）、只推进 `o`。本轮 X7 三处真址（`add edx,8`@0x691EB2、
   `dec eax;mov[edx],eax`@0x691E98、`mov ecx,[0xA8ECA4]`@0x691E77）由**单次整段线性解码**
   与**独立 raw 字节 find**（`83c208`/`488902`/`8b0da4eca800`）互相印证才落定。
   ⇒ 教训（G-63）：**修 bug 时连自己的机制解释一起复测**；错误自诊比错误本身更难发现，
   且会写进台账传染到后续轮次。
4. **变异用例偏移逐字节 raw 复核**：首版 M4 目标 0x691E0F 实为 `mov` 的 reg 位（改成
   a0→a1 会同时破坏 Save 读与 X9 阳性对照），改指到真正的 disp 低字节 0x691E10，
   并把 M6/M10/M11/M14 等按 raw dump 逐个校正到 imm/disp 落位——**先对产物核再定预期**。

## 5. 边界与债务

- 条目步长 8 的**语义**（两 dword 各是什么字段）本轮只钉 `[+0xA0]`计数/`[+0xA8]`数组/
  条目索引 vs 注册表下标这层，**未**定谔条目内两 dword 的字段名 ⇒ L-4 记「Save 载荷与
  计数/索引簇已解；条目内双 dword 细分」转按需补充。
- X9 的存储站点 `{0x6916C7,…,0x691C8B}` 各自归属函数未逐个反查（census 精确集合已钉，
  功能归属未推）。
- 未做异族盲验（本线 R-035…R-044 全部待 C 会话队列）。
- 本结论是类布局定谳，**不宣称任何地址可改写**（charter §8）。
