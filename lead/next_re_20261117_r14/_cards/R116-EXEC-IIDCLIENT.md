# R116-EXEC-IIDCLIENT —— 执行员（deepseek）：独立复算「IID 客户端请求面」

## 身份与边界
执行员。你的任务是**独立重写实现**（不要 import 我的 r116a/r116b，不要 import 我的结果 json）
重新算出下面 9 个数字。只读盘，只在你自己的新文件里写结果。禁止使用反引号。
所有命令带 timeout。禁止对整段 .text 开 detail=True（用 disasm_lite）。

## 工作目录
/home/t628/projects/ra2-campaign-forge

## 可用的底座（可以用，但你要自己核它）
_r113/r113_lib.py 提供 PE 读写：raw / fo / u32 / TEXT0 / TEXT1 / RD0 / RD1 / HB / STARTS / MD / body
_r113/census.pkl 是全镜像 vtable/COL 普查缓存。

## 待独立复算的 9 个数字
被测镜像 ra2bench/gamemd.exe。相关常量（你要自己从盘上确认它们的位置与字节）：
OleSaveToStream 的 IAT 槽 = 0x7e15f4；OleLoadFromStream = 0x7e15f8。
IID 候选：0x7f7c70、0x7f7c80、0x7f7c90、0x7f7ca0。

N1 .rdata 里「GUID 形状」常量（+4 处 dword==0、+8 处 dword==0xC0、+12 处 dword==0x46000000）
   一共有几个？地址分别是多少？
N2 上述 IID 各有多少处「指令对齐的 push imm32」出现（即该 4 字节常量正好是某条
   push 指令的操作数）？各有多少处「指令对齐的 mov r32, imm32」出现？
N3 按**函数**去重（用 HB 函数入口集合归属），请求 0x7f7c80 的不同函数有几个？
   请求 0x7f7c70 的有几个？
N4 这些函数里，在其 QI 请求点**之后**出现对 0x7e15f4 或 0x7e15f8 的 call 的有几个？
N5 全 .text 里对 0x7e15f4 的 call（形态 ff 15 imm32）一共有几个站点？对 0x7e15f8 呢？
N6 N5 的站点里，同一函数内、在调用点**之前**请求过 0x7f7c80 的有几个？请求过 0x7f7c70 的有几个？
N7 留一法基线：把 0x7f7c80 自己排除，其余 GUID 形状常量共有多少个
   「(IID, 函数)」对，其中所在函数后续有 Ole*Stream 的有几个？
N8 在 OleSaveToStream 调用点做栈参数回溯（cdecl 最后一个 push 是第 1 实参）：
   带 QI(0x7f7c80) 的那些站点里，第 1 实参是不是寄存器形态、第 2 实参是不是另一个寄存器？
N9 在 OleLoadFromStream 调用点做同样的栈参数回溯：第 2 个实参（REFIID）的立即数是多少？
   它是不是 0x7ed358？

## 特别要你攻击的点
1. N2 的「指令对齐」判定很容易写错。请写出你的判定方法，并给一个**反控**：
   故意放宽成「任意 4 字节命中」，数量变成多少？为什么对齐后数量会减少？
2. N7 我自己的第一版基线是错的（把被测对象也算进基线，成了循环对照）。请你从零独立算，
   并明确回答：基线里到底有没有把 0x7f7c80 算进去？如果算进去，基线比例是多少？
3. N8/N9 的「最后的连续 push 序列」截断条件是否稳健？举一个会截错的例子。
4. 有任何一处你算出来跟我给的数不一致，**直接报不一致**，不要迎合。

## 输出
把结果写成 /home/t628/projects/ra2-campaign-forge/_r116/x116exec_client.json
结构自定，但必须含 N1..N9 的实测值 + 每项的复算命令/方法说明 + 你的反控结果。
最后在回复里用文字列出 N1..N9 你的数值，逐项标明与我的预期是否一致（我会从盘上核）。
