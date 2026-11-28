# R222-A 执行卡：gamemd.exe ADPCM 编解码器结构与状态机取证（hy4 执行员）

## 角色
执行员。可以写脚本到 /home/t628/projects/ra2-campaign-forge/_r222/ 下，脚本命名 A_*.py，输出写 _r222/A_out.txt。不要修改任何既有项目文件（四件套、FACT_INDEX、_r221 下的文件一律只读）。

## 环境要点（必须照做，违反会 OOM 或读错）
- 只读 PE 映射模块：import sys; sys.path.insert(0,"/home/t628/projects/ra2-campaign-forge"); import _r185.pe185 as P
  P.RAW 是全文件字节；P.r2o(va) 给文件偏移；P.SECS 是段表；P.sec_of(va) 给段名。
- capstone：from capstone import *; md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata = True
- 本卡只反汇编 0x7c6000..0x7c8000 这 8 KB 范围（一次 md.disasm 即可，不要对整段 .text 开 detail=True）。
- 数字一律实测后填写，禁止照抄本卡文字当结论；本卡给的是口径，不是期望值。

## 取证任务（一个脚本一次跑完，全部打印）

T1 函数入口表：在 0x7c6000..0x7c8000 里按字节搜 55 8b ec（push ebp; mov ebp,esp）给出全部命中地址列表。

T2 两张跳转表（按小端 dword 读，各给 hex 与十进制地址）：
  0x7c7758 起 8 个 dword；0x7c7778 起 4 个 dword。

T3 解码器展开体里的样本起点：搜所有指令文本恰为 add eax, dword ptr [edx*2 + 0x879b30] 的位置（只在本 8 KB 范围内），给地址列表、总数，以及相邻地址差的直方图。

T4 三段展开体同构判定：以 0x7c7428、0x7c77f0、0x7c7bc0 为三个候选基址（这是待验证假设，若 T3 显示不同就按实测基址改）。
  对每一段取到下一个候选基址为止的指令序列，把指令文本里出现的、落在该段自身区间内的目标地址减去该段基址做归一，然后逐条比较三段序列：给每段指令条数、逐条 mnemonic+op_str 相同的条数、第一处不同的偏移（没有就写 none）。

T5 参数分派矩阵：反汇编 0x7c7371..0x7c73d3，把（word[ebp+0x10], word[ebp+0x14]）到跳转目标的映射写成四行表（比较 cx,8 / cx,0x10 与 dx,2 / dx,1 的组合），并说明不匹配时落到哪个地址。同时给 0x7c75cc 起的收尾指令序列。

T6 收尾重放分派（0x7c75b2..0x7c75c1 与 0x7c7694..0x7c7757）：对 T2 的 8 个目标逐个反汇编，抽三件事：(a) sub edi,imm 的值；(b) sub esi,imm 的值（没有就写 0）；(c) 该处理块末尾 jmp 的目标地址。按表列 index 0..7。

T7 编码器内联差分 vs 表 0x879b30：编码器 0x7c6315..0x7c635d 用 test eax,4 / test eax,2 / test eax,1 / shr edx,3 / test eax,8 内联算 delta，其中 step = word[ebx+0x20]。
  读 .data 的 0x8758e4 处 89 个 word 当 step 表 s[m]（m=0..88），读 0x879b30 处 1424 个有符号 int32 当差分表。
  对 m=0..88、n=0..15 逐项比较：内联式 d = (s>>3) + (s if n&4 else 0) + ((s>>1) if n&2 else 0) + ((s>>2) if n&1 else 0)，符号按 n&8 取负；表项 = int32 at 0x879b30 + 4*(16*m+n)。给命中数/1424 与首个失配（若有）。

T8 编码器 index 更新 vs 0x8758c4 索引表：读 0x8758c4 起 8 个有符号 16 位字。说明 0x7c639b..0x7c63c3 的 clamp 逻辑（cmp 0x8000 / cmp 0x58 两个门限），给出等价的 index 更新式与钳位范围，并核对：0x8758d4 处 16 B 是否与 0x8758c4 处 16 B 逐字节相同。

T9 引用计数（.text 逐字节 resync 全扫，禁 md.detail）：统计下列地址作为绝对位移（32 位 disp）出现在任何指令操作数里的次数，各给次数与前 3 个位点：
  0x8758c4、0x8758d4、0x8758e4、0x8759b4、0x876ff4、0x877b14、0x877c14、0x879b30、0x87b170、0x87bc90、0x87bd90、0x7c7758、0x7c7778。
  做法：扫 RAW 里 .text 原始字节找 4 字节小端模式，命中后确认该位移落在指令内（简单做法：同时用 md.disasm_lite 全 .text 线性扫一遍，逐条检查指令字节里是否含该 4 字节模式，只对含模式的指令开一次 disasm）。

T10 反控（必须跑，报实测命中数）：
  C1 把 T7 的符号判据从 n&8 改成 n>=8（等价性检查，应相同，报是否相同）；
  C2 把 T7 的 step 表基址右移 2（0x8758e6 起读）命中数；
  C3 把 T3 的 0x879b30 换成 0x87b170（律 S 表）后按 dword 读，命中数应为 0 附近，报实测。

## 输出要求
把全部 T1..T10 结果写进 _r222/A_out.txt，并在最终回复里给出简洁汇总：每条任务一行，写实测数字。遇异常（段外地址、读不到）如实写，不要猜。禁止逐条命令试探，一个脚本一次输出全部。
