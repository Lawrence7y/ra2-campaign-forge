# S06-K2 UNKNOWNS（未证/残差）

## U1 · CellClass 46 个「无本类读点」字段
63 字段中 46 个只有 ctor 初始化写点、无本类读点（虚调用/lea 伪读已剔除）。它们被 RTTI/ctor 证明为真实存储槽，但**语义 [未证]**；不作探针。完整清单见 `PROBE_OFFSETS.md §B`、`EVIDENCE/t1_FINAL.txt`。其中：
- `+0x7C`/`+0xAC` 是 `rep stosd` 12-dword 清零区（YRpp `SensorsOfHouses`/`DisguiseSensorsOfHouses` 数组），是数组不是单值字段。
- `+0x30`：CellClass 自身无读点；任务里的「元素 +0x30=next」是 **ObjectClass+0x30 NextObject**，不是 CellClass 字段。audit 已列此异常。

## U2 · MapClass +0x13C 格数组基址的「写点」
- 绝对写 **0 处**（raw `A3/C705/8915` 全 0，399 处绝对访问全为读）。
- 写点在基 ctor `0x565090` 的 `0x565105 mov [esi+0x13C],ebx`（初始化 0）已确认；但**运行期把已分配数组基址写回该字段**的站点未能隔离：全镜像 54 处 `[reg+0x13C]` 写多属其它类的同偏移字段（offset≠semantics），以 singleton 立即数的数据流扫描得 0 处。
- 可能机制：经某个持有 singleton 指针的全局变量间接写，或构造期一次性写后数组原地 realloc 不改基址字段值。**标 [未证]，不强行归属**。读点/stride 证据完备（T3）。

## U3 · 41 个单/弱支撑字段的跨类读点
audit（S06-K1 VERDICT）曾指出 `+0x2C/+0x54/+0x58/+0xE8/+0x100` 的「读点」落在 ListClass/ControlClass。本卡已把方法集限定为 CellClass 自有（51 函数），这些误归属已剔除；剩下 17 个双支撑字段的读点均来自本类方法或经 GetCellAt 验证的 `CellClass*`。但全局窗口扫描（1439 处）依赖 `eax=GetCellAt 返回` 的数据流，交叉函数边界的读点可能仍有漏，属采样局限。

## U4 · GetSize 基线计数口径差
本卡 `.text` 内 `B8 imm C3`=666 / 全文件 raw=668；§969 记 ~837（其中 543 非 slot12），本卡非 slot12=597。差异来自扫描范围/是否含 C2(ret imm16)（本卡实测 `B8 imm (C3|C2)`=873）。**不影响**「判据不特异、必须叠加 vtable slot12」的结论，也不影响 GetSize=0x148 的双向闭合。详见 DISAGREE D1。

## U5 · 未跑真机
本卡是静态卡（写域只 S06-K2），未启动/附加 gamemd.exe。探针字段的运行时取值分布、②-b 重叠的实际构造留给 W177-D。
