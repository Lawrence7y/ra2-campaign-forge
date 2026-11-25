# R128 跨家族审计（审计员 hy4）

目标文件 ra2bench/gamemd.exe，sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476，实测一致。
所有全段指令扫描使用 capstone disasm_lite，未使用 detail=True 全段实例化。脚本均经 timeout 运行，运行后本机 python3 仅见常驻服务进程 t628_stats.py / nas-hub/server.py / harness/server.py / harness/re_guardian.py，本次审计脚本无残留。

## 主张 1（对象身份，地址 0x87f7e8）

### 我实测的原始数字

1) 4 字节 little-endian 模式 e8 f7 87 00 在 .text 原始字节中的出现次数：3700。
2) 指令流操作数文本含 0x87f7e8 的指令合计 498 条，形态分布：
   493 条 mov ecx, 0x87f7e8
   2 条 push 0x87f7e8
   1 条 mov edx, dword ptr [0x87f7e8]
   1 条 mov dword ptr [edx], 0x87f7e8
   1 条 mov dword ptr [0x87f7e8], 0x7e1964
3) 形态 mov dword ptr [0x87f7e8], imm32 的站点：1 处。
   地址 0x40d1b2，立即数 0x7e1964，完整指令 mov dword ptr [0x87f7e8], 0x7e1964。
4) 以 0x7e1964 为 vtable 的 RTTI 解算：
   vt-4 = 0x7e1960，COL = 0x7fab38
   COL+12 处 TypeDescriptor = 0x816c90，TypeDescriptor+8 类名字符串 .?AVMouseClass@@
   COL+16 处 ClassHierarchyDescriptor = 0x7fab28，+8 基类数 = 12，+12 BaseClassArray = 0x7faaf0
   12 个基类项逐一解出（BaseClassDescriptor -> TypeDescriptor -> 类名，ncb，mdisp）：
   0: BCD 0x7faad8，TD 0x816c90，.?AVMouseClass@@，ncb 0xb，mdisp 0
   1: BCD 0x7faac0，TD 0x816c70，.?AVScrollClass@@，ncb 0xa，mdisp 0
   2: BCD 0x7faaa8，TD 0x816c58，.?AVTabClass@@，ncb 0x9，mdisp 0
   3: BCD 0x7faa90，TD 0x816c38，.?AVSidebarClass@@，ncb 0x7，mdisp 0
   4: BCD 0x7faa78，TD 0x816c18，.?AVPowerClass@@，ncb 0x6，mdisp 0
   5: BCD 0x7faa60，TD 0x816bf8，.?AVRadarClass@@，ncb 0x5，mdisp 0
   6: BCD 0x7faa48，TD 0x816bd8，.?AVDisplayClass@@，ncb 0x4，mdisp 0
   7: BCD 0x7faa30，TD 0x816bc0，.?AVMapClass@@，ncb 0x3，mdisp 0
   8: BCD 0x7faa18，TD 0x816ba0，.?AVGScreenClass@@，ncb 0x2，mdisp 0
   9: BCD 0x7faa00，TD 0x816b88，.?AUIGameMap@@，ncb 0x1，mdisp 0
   10: BCD 0x7fa9e8，TD 0x816b70，.?AUIUnknown@@，ncb 0x0，mdisp 0
   11: BCD 0x7fa9d0，TD 0x816b50，.?AVINoticeSink@@，ncb 0x0，mdisp 21784
5) 反控：
   0x87f7e4：4 字节字节模式出现 0 次；操作数含该地址的指令 0 条。
   0x87f7ec：4 字节字节模式出现 6 次（VA 0x4690fb，0x4f481c，0x4f49ea，0x4f4a58，0x4f4a6c，0x55cd07）；操作数含该地址的指令 1 条：0x4690fa mov dword ptr [0x87f7ec], eax。
6) 段表复核：.data 虚拟范围 0x812000..0xb79be4，raw 数据仅到 VA 0x87e000，因此 0x87f7e8 位于无静态字节的 BSS 区。

### 与卡面的主张是否一致

卡面在主张 1 中只要求复算以上项目，没有给出期望数字，除地址落在 BSS 的陈述外无可对照数字。
地址落在 BSS 的陈述：一致。
以写入立即数 0x7e1964 作 vtable 得到的类名是 .?AVMouseClass@@，不是类名列表之外的东西；审计时发现主会话相关卡片如果把 0x7e1964 当作别的对象，会与此处 RTTI 结果不同（见分歧节）。

### 判定

PASS（对卡面要求的所有可计算项均已按字节复算；卡面未给出可矛盾的数字）。

## 主张 2（方法调用约定）

### 我实测的原始数字

vtable 0x7ea564 的前 5 个槽逐一读回：
slot0 0x7ea564 = 0x429210
slot1 0x7ea568 = 0x4e8240
slot2 0x7ea56c = 0x4e8250
slot3 0x7ea570 = 0x429270
slot4 0x7ea574 = 0x4e8260
与卡面列出的五个函数地址一致。

各函数入口正向反汇编遇到的第一条 ret 及其栈弹出字节数：
0x429210：0x429221 ret 0xc，数字 12
0x4e8240：0x4e8245 ret 4，数字 4
0x4e8250：0x4e8255 ret 4，数字 4
0x429270：0x429285 ret 0x10，数字 16
0x4e8260：0x4e8262 ret 8，数字 8

五个数字按 slot0..slot4：12，4，4，16，8。

### 与卡面的主张是否一致

卡面只要求给出五个数字，未列出期望数字，因此无数值冲突。卡面 vtable 槽列表本身与实测一致。
附带 RTTI 核对：vtable 0x7ea564 的 COL = 0x8023b8，TD = 0x823ef8，类名 .?AVTiberianSunClassFactory@@，基类数 3（.?AVTiberianSunClassFactory@@，.?AUIClassFactory@@，.?AUIUnknown@@）。

### 判定

PASS。

## 主张 3（CreateInstance 的实参位置，函数 0x429270）

### 我实测的原始数字

0x429270 入口起前 0x60 字节内的关键指令（完整文本）：
0x429270    mov eax, dword ptr [esp + 0x10]       读取 [esp+0x10] 存入 eax
0x429288    mov ecx, dword ptr [esp + 0x18]       读取 [esp+0x18] 存入 ecx
0x4292a2    mov ebp, dword ptr [esp + 0x1c]       读取 [esp+0x1c] 存入 ebp
0x42928c    mov dword ptr [eax], 0                mov dword ptr [reg], 0 形态的清零出参指令，存在，唯一一处，reg = eax

即读取寄存器依次为 eax、ecx、ebp；清零出参站点 0x42928c，目标寄存器 eax。
该函数第一处 ret 为 0x429285 ret 0x10，cdecl 风格栈清理 16 字节，符合 CreateInstance 接收 4 个栈上参数的形态。

### 与卡面的主张是否一致

卡面未给出寄存器名称或清零站点的期望值，只要求给出地址与指令文本，故无数值冲突；以上为原始复算结果。

### 判定

PASS。

## 主张 4（IID 常量 0x7ea6e8 的全部引用点）

### 我实测的原始数字

全 .text 用 disasm_lite 扫描，操作数文本含 0x7ea6e8 的指令：2 条。
0x42930f    mov edi, 0x7ea6e8
0x4293a5    mov edi, 0x7ea6e8

0x7ea6e8 处 16 字节小端原始序列（十六进制）：c7 2e f0 96 e8 6f d1 11 b6 fd 00 a0 24 dd af d1
按 GUID 8-4-4-4-12 格式化：
{96f02ec7-6fe8-11d1-b6fd-00a024ddafd1}
其中 Data1 = 0x96f02ec7，Data2 = 0x6fe8，Data3 = 0x11d1，Data4 前 2 字节 b6 fd，后 6 字节 00 a0 24 dd af d1。

### 与卡面的主张是否一致

卡面未提供期望引用点数量、地址或 GUID 字符串，仅要求算出并报告；无对照数字冲突。

### 判定

PASS。

## 分歧与复算不出来之处

1) 卡面主张 1 要求把写入 0x87f7e8 的立即数当 vtable 解类名。实测唯一写入立即数是 0x7e1964，其 RTTI 类名为 .?AVMouseClass@@，基类 12 个，基类列表首项也是 MouseClass 自身。若主会话其他材料把 0x87f7e8 说成 ClassFactory 对象（例如指向 0x7ea564 的 .?AVTiberianSunClassFactory@@），则与本次字节复算不一致：0x87f7e8 的唯一静态写入是 0x7e1964，而非 0x7ea564。卡面本身没有直接写出类名，因此本分歧针对卡面之外的周边说法，列出供主会话核对。
2) 0x87f7e8 的 4 字节模式在 .text 中出现 3700 次，但操作数含该地址的指令只有 498 条；两者差异巨大，原因是大量字节模式落在指令中间或立即数/位移的不同对齐位置，不能把字节出现次数当引用次数。卡面同时要求这两类数字，已分别给出，无冲突。
3) 主张 2 的卡面文字写了“ret 4 就报 4，ret 0xc 报 12，纯 ret 报 0”，但未预先给出五个数字；本次五个 ret 均带立即数，没有纯 ret。若主会话其他材料声称 slot0..slot4 全部是 ret 0xc 或全部 ret 4，则与实测 12/4/4/16/8 不符。
4) 无其他复算不出来的项目；四条主张的所有指示项均已完成字节级复算。
