# R223-XAUDIT — 只读复核：0x7c6620 八条主张 + 四张 4 项表同构性

## 你的角色与边界

只读复核员。不许改写任何文件，不许跑 re-tool，不许派子代理。工作目录 /home/t628/projects/ra2-campaign-forge。
目标 ra2bench/gamemd.exe，sha256 必须 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476（先自校验）。
ImageBase 0x400000。段表实测：.text VA 0x401000 off 0x1000 rawsize 0x3e0000；.rdata 0x7e1000 off 0x3e1000 rawsize 0x31000；.data 0x812000 off 0x412000 rawsize 0x6c000 vsize 0x367be4；.detour 0xb93000 off 0x497000 rawsize 0x3000。
工具 python3 + capstone + pefile，禁止 pip install。防 OOM：全段扫描只能用 disasm_lite 或 <=64KB 分块，禁止对整段 .text 一次性 detail=True。
一次取证：一条脚本跑完全部复核并打印结论。禁止逐条单点命令。

## 待复核主张（主会话提出，你不要替它辩护，只认字节）

### A 组：函数 0x7c6620

- A1 函数体 = [0x7c6620, 0x7c672a) 共 0x10a 字节；0x7c672a 起全 int3 到 0x7c672f。
- A2 记录寻址 = dword[0xb0b6ec] + (arg1 + arg2*dword[0x8759a4]) * 8，其中步长来自内存全局 dword[0x8759a4]，不是立即数。
- A3 记录只有两个字段：[rec+0] dword 值、[rec+4] dword 标志；全函数除这两个外没有第三个 [esi+disp] 访问。
- A4 双重循环：edi 与 ecx 初值均 0xffffffff，各自 cmp reg,2 + jl 回边，即 3x3=9 组；(edi,ecx)=(0,0) 那一组被 or eax,ecx + test eax,eax 提前跳出，不进内层。
- A5 递归调用点唯一在 0x7c66ee，压 4 个实参后 lea esp,[esp+0x10] 清 16 字节。
- A6 常量 0xc 出现在两处 cmp eax,0xc，比较对象是 abs(邻居值 - 本记录值)（abs 由 cdq + xor eax,edx + sub eax,edx 实现，共出现 2 次）。
- A7 全函数 3 个 ret，返回值只可能是 0 或 1。
- A8 全文件没有任何外部引用：全 .text 扫 e8/e9 rel32 指向 0x7c6620 的只有 0x7c66ee 一条自递归；dword 字面量 0x7c6620 全文件 0 次；字节序列 68 20 66 7c 00（push imm32）0 次。因此它是死代码/未被直接调用。

### B 组：四张 4 项表

- B1 0x7c6b58 内容 = 7c67c3 / 7c67d8 / 7c67e8 / 7c67f8
- B2 块2 三张表：0x7c7778 = 7c73e2/7c73f8/7c7408/7c7418；0x7c7b3c = 7c77a9/7c77c0/7c77d0/7c77e0；0x7c7f10 = 7c7b79/7c7b90/7c7ba0/7c7bb0
- B3 四张表同构：每张的 4 个目标都是同一骨架，即 entry0 = push ebp / shr ebp,4 / xor ebx,ebx / or ebp,ebp / jmp；entry1..3 = sub ebp,K（K 分别 0xc/8/4）/ push ebp / shr ebp,4 / xor ebx,ebx / inc ebp / jmp。
- B4 每张表只有 1 个 jmp dword ptr [ebx*4 + 表址] 形式的引用点（块1 在 0x7c67d3，0x7c7778 在 0x7c73f2，0x7c7b3c 在 0x7c77b9，0x7c7f10 在 0x7c7b89）；四张表的表址字面量全文件各出现 1 次。
- B5 块2 三张表与块1 那张表**是否逐字节同构**（即去掉地址差后指令序列完全一致）：请给出你的判决和逐表差异清单（哪几条指令不同、差在哪）。这是本次复核最关键的一问，主会话倾向认为同构但**尚未证明**，请你独立判定并明确写出结论用词。

### C 组：0xb0b6ec 与 0x8759a4 的性质

- C1 0x8759a4 落在 .data 的 raw 区间内，初值 0；0xb0b6ec 超出 .data 的 raw 区间（0x87e000 之后）落在 vsize 内，即未初始化 BSS，文件里无初值。
- C2 0x8759a4 在 .text 内有 18 处 dword 引用；0xb0b6ec 有 32 处。
- C3 0x8759a4 的写点至少包含 0x6b27ec（mov dword ptr [0x8759a4],eax）与 0x6b2b3b；0xb0b6ec 的写点包含 0x6b271f / 0x6b2766 / 0x6b276d / 0x6b2a89 / 0x6b2ad0 / 0x6b2ad7 / 0x6b3649 / 0x6b3a6d / 0x6b3e07 / 0x6b3e2b 等。

## 交付要求

逐条给 PASS / FAIL / 口径有误（口径有误时必须写清「数字对不对、说法错在哪」）。对 B5 与 C1 给完整推导。
报告最后单列：你认为主会话最可能错的一条是什么，以及你自己发现的、主会话完全没提到的事实（如有）。
