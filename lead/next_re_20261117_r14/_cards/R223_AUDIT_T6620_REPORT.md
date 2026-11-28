# R223-AUDIT 复核报告 — 0x7c6620 八条主张 + 四张 4 项表同构性

## 环境与自校验

- 工具：python3 + capstone + pefile（无 pip install）。
- 目标：`ra2bench/gamemd.exe`，sha256 实测 `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476`，与卡面一致（先校验，通过）。
- ImageBase 0x400000；段表实测与卡面一致：`.text` VA 0x401000 off 0x1000 rawsize 0x3e0000；`.data` VA 0x812000 off 0x412000 rawsize 0x6c000 vsize 0x367be4。
- 防 OOM：全段扫描仅用 `disasm_lite` 或字节模式匹配；仅对少量目标地址开 detail。

## A 组：函数 0x7c6620

| 编号 | 判决 | 依据 |
|---|---|---|
| A1 | PASS | 函数体 `[0x7c6620,0x7c672a)` 长 0x10a；`0x7c6720..0x7c672f` 尾部字节 `...c3 cccccccccccccc`，`0x7c672a` 起 5 字节全 `cc`。 |
| A2 | PASS | `0x7c662a mov eax,[ebp+0xc]` → `0x7c6633 imul eax,dword ptr [0x8759a4]` → `0x7c663a add eax,[ebp+8]` → `0x7c663d lea esi,[esi+eax*8]`，esi 来自 `0x7c662d mov esi,[0xb0b6ec]`。步长确为内存全局 `dword[0x8759a4]`，非立即数。 |
| A3 | PASS | 全函数 `[esi+disp]` 形式仅有 `[esi]`（0x6640/0x668c/0x66a3/0x66b8/0x66c5/0x66cd/0x66da）与 `[esi+4]`（0x667d test、0x66c7/0x66dc or），即仅 +0 值与 +4 标志两字段，无第三个 disp。 |
| A4 | PASS | `0x7c6645 mov edi,-1`、`0x7c664a mov ecx,-1`；内层回边 `0x7c670b inc ecx / 0x7c670c cmp ecx,2 / 0x7c670f jl 0x7c664f`；外层回边 `0x7c6715 inc edi / 0x7c6716 cmp edi,2 / 0x7c6719 jl 0x7c664a`。两循环各 3 次（初值 -1→0→1→2 退出）。`0x7c664f mov eax,edi / 0x7c6651 or eax,ecx / 0x7c6653 test eax,eax / 0x7c6655 je 0x7c670b` 使 `(edi,ecx)=(0,0)` 那一组直接走到 `inc ecx`，不进内层。精确模拟 9 组：执行 8 组，仅 (0,0) 被跳过；(-1,-1) 因 `edi|ecx = 0xffffffff` 正常进入内层。 |
| A5 | PASS | 唯一 `call` 在 `0x7c66ee e8 2dffffff`（目标 0x7c6620）；此前 4 次 push 实参：`0x7c66e0 push ecx`、`0x7c66e1 push edi`、`0x7c66e2 push [ebp+0x14]`、`0x7c66e5 push [ebp+0x10]`、`0x7c66e8 push [ebp-0xc]`、`0x7c66eb push [ebp-8]`；调用后 `0x7c66f3 lea esp,[esp+0x10]`。需说明：push 一共 6 次（ecx/edi 是寄存器现场保护，4 个 dword 是实参），`lea esp,+0x10` 清的正是那 4 个实参。 |
| A6 | PASS | `cmp eax,0xc` 出现在 `0x7c6696` 与 `0x7c66ad`；两处之前均为 `mov eax,[esi]; sub eax,[ebp-4]; cdq; xor eax,edx; sub eax,edx`，即 `abs(邻居值 - 本记录值)`。 |
| A7 | PASS | 3 个 `ret`（0x7c66a2、0x7c670a、0x7c6729）：0x66a2 前 `xor eax,eax`；0x670a 前 `xor eax,eax`；0x6729 前 `mov eax,1`。返回值只可能 0 或 1。 |
| A8 | PASS | 全 `.text` 扫 `e8/e9 rel32` 指向 0x7c6620 仅 1 条：`0x7c66ee`（自递归）；dword 字面量 `20 66 7c 00` 全文件 0 次；`68 20 66 7c 00`（push imm32）0 次。`0x7c672a` 起全 int3，本函数无任何外部直接调用点。 |

A 组结论：A1–A8 全部 PASS。

## B 组：四张 4 项表

| 编号 | 判决 | 依据 |
|---|---|---|
| B1 | PASS | `0x7c6b58` 四项实测：7c67c3 / 7c67d8 / 7c67e8 / 7c67f8。 |
| B2 | PASS | `0x7c7778` = 7c73e2/7c73f8/7c7408/7c7418；`0x7c7b3c` = 7c77a9/7c77c0/7c77d0/7c77e0；`0x7c7f10` = 7c7b79/7c7b90/7c7ba0/7c7bb0。 |
| B3 | PASS | 16 个入口逐一反汇编，骨架全部吻合：slot0 = push ebp / shr ebp,4 / xor ebx,ebx / or ebp,ebp / jmp；slot1/2/3 = sub ebp,0xc/8/4 / push ebp / shr ebp,4 / xor ebx,ebx / inc ebp / jmp。 |
| B4（口径有误，数字对） | 口径有误 | 表址字面量全文件各出现 1 次，数字正确；每张表只有 1 条 `jmp dword [ebx*4 + 表址]` 引用点也正确。但卡面把 **disp32 操作数起始地址**当成了引用点地址：`ff 24 9d <disp32>` 实测 jmp 指令起始为 0x7c67d0 / 0x7c73ef / 0x7c77b6 / 0x7c7b86，而 disp32 起点正是 0x7c67d3 / 0x7c73f2 / 0x7c77b9 / 0x7c7b89（= jmp 起始 +3）。若"引用点"指整条指令，卡面地址各偏 3；若"引用点"指表址字面量所在字节，则卡面数字正确。另 ModRM 应为 `9d`（scale=4,index=ebx,disp32），非 `8d`。 |
| B5 | PASS（独立判定：同构） | 逐表归一化反汇编序列 16/16 完全一致，逐字节去掉 rel32 差异后所有非地址字节全同（完整推导见下）。 |

### B5 完整推导

方法：对每张表的 4 个 slot，取入口到终止 `jmp` 的字节，反汇编为 `(mnemonic, operand)` 序列（把 ≥6 位十六进制立即数归一为 `<ADDR>`），再比较序列；并把原始字节中 `e9 <rel32>` 的 rel32 去掉后比较剩余字节。

四张表的 slot 序列（全部一致）：
- slot0：`push ebp; shr ebp,4; xor ebx,ebx; or ebp,ebp; JMP`
- slot1：`sub ebp,0xc; push ebp; shr ebp,4; xor ebx,ebx; inc ebp; JMP`
- slot2：`sub ebp,8; push ebp; shr ebp,4; xor ebx,ebx; inc ebp; JMP`
- slot3：`sub ebp,4; push ebp; shr ebp,4; xor ebx,ebx; inc ebp; JMP`

原始字节示例与差异清单：

| slot | 块1 (0x7c6b58) | 块2-1 (0x7c7778) | 块2-2 (0x7c7b3c) | 块2-3 (0x7c7f10) | 差异 |
|---|---|---|---|---|---|
| 0 | `55 c1ed04 33db 0bed e9b1010000` | `…e9b2010000` | `…e9b3010000` | `…e9b3010000` | 仅末条 jmp rel32 不同 |
| 1 | `83ed0c 55 c1ed04 33db 45 e985020000` | `…e985020000` | `…e911030000` | `…e915030000` | 仅末条 jmp rel32 不同 |
| 2 | `83ed08 55 c1ed04 33db 45 e9c9020000` | `…e9c9020000` | `…e9c5020000` | `…e9c9020000` | 仅末条 jmp rel32 不同 |
| 3 | `83ed04 55 c1ed04 33db 45 e985020000` | `…e985020000` | `…e981020000` | `…e985020000` | 仅末条 jmp rel32 不同 |

结论用词：**逐字节同构（byte-isomorphic modulo jmp rel32）**。块2 三张表与块1 逐 slot 比较，指令序列 100% 相同，全部差异仅为每个入口末尾无条件 `jmp` 的 4 字节相对位移（由各跳转目标地址不同自然产生）；没有任何一条非 jmp 指令不同。

## C 组：0xb0b6ec 与 0x8759a4

| 编号 | 判决 | 依据 |
|---|---|---|
| C1 | PASS | 推导见下。 |
| C2 | PASS | 全 `.text` 精确扫描（moffs `a1/a3` + ModRM mod=00 rm=101 两类绝对寻址，排除立即数巧合）：`0x8759a4` 18 处；`0xb0b6ec` 32 处。与主张一致。 |
| C3 | PASS | 写点实测（局部 capstone lite 复核）：`0x8759a4` 写点含 `0x6b27ec mov dword [0x8759a4],eax`、`0x6b2b3b mov dword [0x8759a4],eax`；`0xb0b6ec` 写点含 `0x6b271f / 0x6b2766 / 0x6b276d / 0x6b2a89 / 0x6b2ad0 / 0x6b2ad7 / 0x6b3649 / 0x6b3a6d / 0x6b3e07 / 0x6b3e2b`，全部命中。 |

### C1 完整推导

- `.data` 段：VA 0x812000，raw 区间 `[0x412000, 0x412000+0x6c000) = [0x412000, 0x47e000)`，对应虚拟地址 `[0x812000, 0x87e000)`；vsize 0x367be4，虚拟区间到 `0x812000+0x367be4 = 0xb79be4`。
- `0x8759a4`：落在 `[0x812000,0x87e000)` 内，文件偏移 `0x412000 + (0x8759a4-0x812000) = 0x4759a4`，读得 dword = **0x00000000**。即位于 raw 内且初值为 0。
- `0xb0b6ec`：大于 raw 末端 0x87e000，小于 vsize 末端 0xb79be4，落在 `.data` 的 virtual-only 区（BSS）。按 VA→文件偏移换算 `d = 0xb0b6ec - 0x812000 = 0x2f96ec > 0x6c000(rawsize)`，`va2off` 返回 None，文件中无对应字节，无初值。
- 因此主张成立：0x8759a4 是 raw 内已初始化为 0 的全局；0xb0b6ec 是 BSS 未初始化全局。

## 最后单列

**主会话最可能错的一条**：没有实质性错误。A1–A8、B1/B2/B3/B5、C1–C3 全部 PASS；唯一需要澄清的是 B4 的"引用点地址"口径——卡面给的 0x7c67d3 等是 `jmp dword [ebx*4+表址]` 指令中 disp32 操作数的起始地址，整条指令实际起始于 0x7c67d0 等（各 -3）；ModRM 为 0x9d。这属于表述口径，不影响"每表仅 1 个引用点、表址字面量各 1 次"的结论。

**自己发现、主会话未提到的事实**：
1. A4 精确模拟 9 组循环：只有 `(0,0)` 被 `or eax,ecx; test` 早退跳过，实际进入内层 8 组（(-1,-1) 正常进入，因 `edi|ecx = 0xffffffff`）。
2. A5 的 push 实为 6 次：`push ecx`/`push edi` 是调用现场保护，`lea esp,[esp+0x10]` 只清 4 个 dword 实参；把 `ecx/edi` 的 push 与实参混在一起会误读栈帧。
3. B4 的 4 个表址字面量在文件里各出现 1 次，且唯一出现位置就是那 4 条 `ff 24 9d` 指令自身（无其他代码/数据引用）。
4. C2 的 18/32 中混有 `a1/a3` moffs 与 `8b/89/c7/af` ModRM 两种绝对寻址形式；仅按 `8b 05` 一类模式计数会漏掉大半（例如 0x8759a4 的 18 处里 9 处是 moffs）。
