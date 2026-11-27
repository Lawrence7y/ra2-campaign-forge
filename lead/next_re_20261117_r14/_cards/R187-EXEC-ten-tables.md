# 卡 R187-EXEC：独立复算「10 张找不到 imm32 装点的 vtable」在字节层的装载形态

角色：执行员（只读盘上 exe，不改四件套；只可在 /home/t628/projects/ra2-campaign-forge/_r187/exec_hy4/ 下写自己的脚本与输出）。

## 背景（R186 实测数字，你要独立复算，不要照抄）
- 全镜像 RTTI 形 COL 1214 个、配对的 vtable 1214 张（判据：vtable-4 是 COL 地址，COL 的首 dword in {0,1}、+8 == 0、+12 指向 TypeDescriptor、+16 指向 ClassHierarchyDescriptor）。
- 用「C7 /0 形态的 mov dword ptr [基址+位移], imm32（含 SIB）且 imm32 命中某 vtable」这条判据做字节扫描，得 5731 条命中。
- 再与「递归下降得到的指令起点集合」取交集得 4886 条；其中基址不是 esp/ebp 且无索引的 3666 条。
- 由此 1214 张表里只有 1204 张被装过，剩 10 张「找不到 imm32 装点」，类名如下：
  1 ?$DynamicVectorClass@PAE
  2 ?$DynamicVectorClass@PAUWinsockBufferType@WinsockInterfaceClass@@
  3 ?$DynamicVectorClass@PAU_DDSURFACEDESC@@
  4 ?$DynamicVectorClass@PBVToolTip@@
  5 ?$DynamicVectorClass@V?$DistributionObject@PAVCellClass@@@?$DiscreteDistributionClass@VCellClass@@@@
  6 CarryoverClass
  7 Dial8Class
  8 PKPipe
  9 TextButtonClass
  10 TriColorGaugeClass

## 你要做的（一条命令跑完，输出全部证据）
对上面 10 个类名逐个：
- 自己从 PE 头推段表（不要只信公共模块），从 .data/.rdata 里按 .?A 前缀 + @@ 后缀的内联类型名定位 TypeDescriptor，再按 COL 与 vtable 的链接关系拿到该类的**全部** vtable 基址（一个类可能有多张，逐张列出）。
- 对每张 vtable 的 4 字节地址值，在**整个文件**里按任意对齐找全部出现位置（不要求 4 字节对齐），逐处报告：文件偏移、折算 VA、所在节。
- 对每处出现的**前 24 字节到后 24 字节**用 capstone 32 位反汇编，报告该处落在哪条指令内部（是立即数操作数、还是数据区字节）。
- 对每处给一个形态判定，至少区分这四种：
  A 直接 store：指令是 mov dword ptr [基址+位移], imm32 且 imm32 就是该 vtable；
  B 先入寄存器：imm32 是被 mov r32, imm32（B8..BF 或 BA 等）读进某通用寄存器，随后出现把**同一个寄存器**写进某内存操作数的 mov/其它 store；
  C 栈局部：store 的基址是 esp 或 ebp；
  D 其它（push 立即数、当作函数实参、看起来是数据区字节等）——把具体指令写出来。
- 最后给一张表：10 个类 × 各自的 vtable × 每处出现的形态，以及「该类是否至少有 1 处 A 或 B形态」的结论。

## 规则
- 严禁对整段 .text 一次性开 detail 反汇编；只用「定位到偏移后再局部反汇编不超过 64 字节」的方式。
- 不许写带反引号的字符串。
- 输出结尾给出 checks / fails 计数，任何被推翻的 R186 数字要**明确写出来**，不要为了对齐而改自己的实测值。
- 12 分钟内结束。
