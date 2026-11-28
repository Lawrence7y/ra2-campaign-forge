# R224-EXEC-ARGS — 0x7c7371 的六个实参与四个入口的消费方式

## 边界（必须遵守）

- 只读。不改任何文件，不派子代理，不装包。工作目录 /home/t628/projects/ra2-campaign-forge。
- 目标 ra2bench/gamemd.exe，sha256 必须等于 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（先自校验再干活）。
- 段表：.text VA 0x401000 off 0x1000 rawsize 0x3e0000；.rdata VA 0x7e1000 off 0x3e1000 rawsize 0x31000；.data VA 0x812000 off 0x412000 rawsize 0x6c000。
- 工具只有 python3 + capstone + pefile，禁止 pip install。
- 防 OOM 硬红线：禁止对整段 .text 开 detail=True 跑 md.disasm()。全段扫描只用 disasm_lite 或 64KB 分块；只有命中的小窗口才允许 detail=True。
- 一次取证纪律：写一个脚本，一条命令跑完全部问题并打印结论。控制在 15 回合内，不要逐条命令试探。脚本与输出都存到 _r224/ 下（文件名以 x_args_ 开头）。

## 已确认的起点（可直接用，但必须自己复算一遍）

- 0x7c7371 是函数入口，首字节 55 8b ec 56 57 53 51 52，随后 mov ebx,dword[ebp+0x1c]，mov cx,word[ebp+0x10]，mov dx,word[ebp+0x14]。
- 该函数被 rel32 call 引用的站点只有两处：0x7c24a2 与 0x7c2557。请自己用全 .text 线性扫 e8/e9 复算，并把结果数字报出来。
- 分支骨架：cx==8 且 dx==2 跳 0x7c75cc；cx==8 且 dx==1 跳 0x7c75cc；cx==0x10 且 dx==2 跳 0x7c7788；cx==0x10 且 dx==1 落到 0x7c73c3。

## 必答问题（每条都要给地址 + 字节，不许只给结论）

### 一、实参映射

对 0x7c24a2 与 0x7c2557 两个调用点，逐条列出 call 之前的 push 序列（地址、字节、push 的操作数表达式），按 cdecl 从右到左的压栈规则推出 arg1..argN，并给出：

- 每个实参的来源（是局部变量、还是 obj 的哪个偏移字段、还是 lea 出来的地址）；
- 调用后 add esp,imm 的立即数，据此判定被调方是 cdecl 还是 stdcall、真实参数字节数；
- 0x7c7371 内部对 arg1..arg6 的每一次读取地址（给出 mov reg,[ebp+0xXX] 的地址）。

已知其中一处 push 是 lea edx,[ebx+0x7d0]，请说明它是第几个参数、在 0x7c7371 里被当成什么（哪个 [ebp+0xXX] 对应、之后每次读写它的偏移是什么）。

### 二、[ebp+0x18] 的语义

0x7c7371 里 mov ebp,dword[ebp+0x18] 之后依次出现 cmp ebp,0x10 / jl / and ebx,3 / shr ebp,4 / inc ebp / sub ebp,0xc / sub ebp,8 / sub ebp,4。请回答：

1. [ebp+0x18] 传入的到底是输入字节数、还是样本数、还是块数？用循环体的步进算术证明（循环体内 add esi,imm 与 add edi,imm 各是多少、每次迭代消耗多少输入字节产出多少输出字节）。
2. 三个 stub 里 sub ebp,0xc / sub ebp,8 / sub ebp,4 之后紧跟 inc ebp，配合 jmp dword ptr [ebx*4+...] 的索引来源（and ebx,3 取值 1..3），说明这段做的是什么补偿（对齐补偿？头部补偿？）。给出 ebx 取值与 stub 索引的对应表（ebx=1/2/3 分别落到哪个 stub 地址）。
3. 0x7c73d6 处 cmp ebp,0x10 之后的 jl 分支与 shr ebp,4 分支，各自对应什么规模输入。

### 三、[ebp+0x10] 与 [ebp+0x14] 的消费方式

1. 这两个 word 参数在 0x7c7371 里只被 cmp 到哪几个立即数？逐个给出 cmp 的地址、字节、立即数。
2. 四个入口（cx=8/0x10 乘 dx=1/2）各自的地址、以及每个入口在 0x7c7371 内的落点；两条 cx==8 的分支为什么都跳到 0x7c75cc（那里是什么，返回值是什么）。
3. 判定：dx==2 与 dx==1 是否对应 stereo 与 mono。依据必须是字节（例如 dx==2 的那条路径里是否有两遍解码、第二遍相对第一遍的基址差、状态块里 ch2 相关偏移是否只在 dx==2 路径上被读写）。0x7c7371 的 4 个状态块偏移是 obj+0x7d0(dword 值)/+0x7d4(word step)/+0x7d6(dword ch2 值)/+0x7da(word ch2 step)，请指出每个偏移分别在哪条路径上被读或被写（给地址）。
4. cx==8 与 cx==0x10 分别是什么（采样位宽？8/16 bit？）。若 0x7c7371 自身字节不足以定性，就明确写「静态不足」，并给出你查到的辅助证据（例如 cx 的来源字段 byte[obj+0x3f] 的写入者，见下题）与不足的具体缺口。

### 四、两个来源字段的写入者

调用方用 movzx cx,byte[obj+0x3f] 与 movzx ax,byte[obj+0x3e] 取值。请全 .text 对齐扫描，列出所有**真实指令起点**上读写 obj+0x3e 与 obj+0x3f 的站点（地址、字节、助记符、操作数）。要求：

- 用线性 disasm_lite 得到指令起点集合，只在起点上匹配，报告「对齐命中数」与「直接字节字面量扫描命中数」两个数字，差值是伪命中；
- 给出每个站点的读/写方向，以及所属函数入口（用「向前找最近的 int3 或 ret 之后的第一条指令」这种可复算规则，规则写进脚本）。

## 输出格式

写一个脚本 x_args_scan.py 与它的输出 x_args_scan_out.txt 到 _r224/，脚本必须带正反控自测（至少 3 条断言：自校验 sha256、分支地址集合、调用点集合），最后打印 PASS/FAIL 计数。报告里每个数字都要能在输出里找到对应行。

报告末尾给一张表：问题编号 → 结论 → 支撑地址。无法定性的项写「静态不足」并说明缺口，不许猜。
