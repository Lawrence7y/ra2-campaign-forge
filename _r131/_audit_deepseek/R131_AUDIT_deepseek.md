# R131 跨家族审计报告（deepseek 侧）

角色：独立复算员。只读 ra2bench/gamemd.exe。除本目录外未写任何文件。
本报告只用缩进代码块，全文无反引号。

## 0 PE 基线（自写解析器，非 pefile）

命令：python3 _r131/_audit_deepseek/a1_sections.py

原始输出：

    filesize 4825360
    e_lfanew 0x50
    machine 0x14c nsec 5 optsz 0xe0
    opt magic 0x10b
    ImageBase 0x400000
    .text    VA=0x00001000 VSize=0x003df38d RawPtr=0x00001000 RawSize=0x003e0000 Flags=0x60000020
    .rdata   VA=0x003e1000 VSize=0x00030074 RawPtr=0x003e1000 RawSize=0x00031000 Flags=0x40000040
    .data    VA=0x00412000 VSize=0x00367be4 RawPtr=0x00412000 RawSize=0x0006c000 Flags=0xc0000040
    .rsrc    VA=0x0077a000 VSize=0x00018128 RawPtr=0x0047e000 RawSize=0x00019000 Flags=0x40000040
    .detour  VA=0x00793000 VSize=0x00002718 RawPtr=0x00497000 RawSize=0x00003000 Flags=0xc0000040

推算得到的地址区间（ImageBase + VirtualAddress）：

    .text   0x00401000 .. 0x007e038d   （RawSize 上界 0x007e1000）
    .rdata  0x007e1000 .. 0x00811074
    .data   0x00812000 .. 0x00b79be4
    .rsrc   0x00b7a000 .. 0x00b92128
    .detour 0x00b93000 .. 0x00b95718

关键 VA 到文件偏移（我自己算）：

    0x6bedb0 -> off 0x2bedb0
    0x41c250 -> off 0x01c250
    0x6bc342 -> off 0x2bc342
    0x817bc0 -> off 0x417bc0
    0x817bb0 -> off 0x417bb0

### 0.1 第一处错误与修正（如实记录）

a1_sections.py 第一版把节表 VirtualAddress 直接当 VA 用（漏加 ImageBase），
导致除节 0 以外的所有 VA 查询返回 None。修法：给 va2off/va2sec/off2va 全部改成
imagebase + s.vaddr 比较。修正后上述 5 个 VA 全部命中。

## 任务 A：调用点计数

### A.1 / A.2 capstone 线性反汇编（disasm_lite，detail=False 流式）

命令：python3 _r131/_audit_deepseek/a2_callsites.py

第一次结果（错误，得 0，如实记录）：

    .text VA=0x401000 END=0x7e1000 rawlen=4063232
    total_insn 155215 max_end 0x46f5a0 gap_to_end 3611232
    [capstone] target 0x6bedb0 count=0
    [capstone] target 0x41c250 count=2
       site 0x416bc2  op_str='0x41c250'
       site 0x44e02c  op_str='0x41c250'
    call-with-0x-form sample: 0x407100 count 6958

根因不是解析器：解析器已同时接受 0x 形式与十进制（下面有专门验证）。
真正原因是 capstone 的 md.disasm_lite() 是生成器，遇到第一个非法字节就永久停止。
它在 0x46f5a0 停下，只解出 155,215 条指令，0x46f5a0 以上的全部代码（含 0x6bedb0 的两个调用点）
根本没被扫描。修正：生成器耗尽后跳过 1 字节并在下一个地址重启，记录跳过区间。

命令：python3 _r131/_audit_deepseek/a3_callsites_resync.py

原始输出（完整）：

    total_insn 1394120
    skip_bytes_total 66 skip_runs 64
    skip_runs_first20 [('0x46f5a0', 1), ('0x48db25', 1), ('0x48dd18', 1), ('0x4c8114', 1), ('0x4d926d', 1), ('0x5001e4', 1), ('0x51c889', 1), ('0x51c88d', 1), ('0x51c891', 1), ('0x51f1fc', 1), ('0x520efc', 1), ('0x58bda4', 1), ('0x5a0084', 1), ('0x5bcacc', 1), ('0x5bcaf5', 1), ('0x5bcb01', 1), ('0x5efee5', 1), ('0x62fe4c', 1), ('0x66301c', 1), ('0x69b15c', 1)]
    [capstone-resync] target 0x6bedb0 count=2
       site 0x6bc364 len=5 op_str='0x6bedb0'
       site 0x6bc3aa len=5 op_str='0x6bedb0'
    [capstone-resync] target 0x41c250 count=13
       site 0x416bc2 len=5 op_str='0x41c250'
       site 0x44e02c len=5 op_str='0x41c250'
       site 0x4db8cc len=5 op_str='0x41c250'
       site 0x4df85c len=5 op_str='0x41c250'
       site 0x51b064 len=5 op_str='0x41c250'
       site 0x521fc2 len=5 op_str='0x41c250'
       site 0x5230dc len=5 op_str='0x41c250'
       site 0x65f092 len=5 op_str='0x41c250'
       site 0x6cc999 len=5 op_str='0x41c250'
       site 0x710213 len=5 op_str='0x41c250'
       site 0x7354f2 len=5 op_str='0x41c250'
       site 0x742699 len=5 op_str='0x41c250'
       site 0x742a94 len=5 op_str='0x41c250'

数字：

    .text 合法指令 1,394,120 条；无法解码的字节 66 个，分成 64 段
    call 目标 0x6bedb0：2 条
    call 目标 0x41c250：13 条

### A.3 原始字节 0xE8 法（.text 内）

同一脚本内，原始输出：

    raw 0xE8 occurrences in .text: 81715
    [raw-E8] target 0x6bedb0 count=2 sites=['0x6bc364', '0x6bc3aa']
    [raw-E8] target 0x41c250 count=13 sites=['0x416bc2', '0x44e02c', '0x4db8cc', '0x4df85c', '0x51b064', '0x521fc2', '0x5230dc', '0x65f092', '0x6cc999', '0x710213', '0x7354f2', '0x742699', '0x742a94']
    target 0x6bedb0: capstone=2 raw=2 same_set=True
    target 0x41c250: capstone=13 raw=13 same_set=True

### A.4 全文件 0xE8 交叉核验（不限于 .text）+ 逐站点解码复验

命令：python3 _r131/_audit_deepseek/a4_wholefile.py

原始输出（节选，含全部站点）：

    whole-file 0xE8 byte count: 82661
    whole-file E8 -> target 0x6bedb0: count=2
       site 0x6bc364 in .text
       site 0x6bc3aa in .text
    whole-file E8 -> target 0x41c250: count=13
       site 0x416bc2 in .text
       site 0x44e02c in .text
       site 0x4db8cc in .text
       site 0x4df85c in .text
       site 0x51b064 in .text
       site 0x521fc2 in .text
       site 0x5230dc in .text
       site 0x65f092 in .text
       site 0x6cc999 in .text
       site 0x710213 in .text
       site 0x7354f2 in .text
       site 0x742699 in .text
       site 0x742a94 in .text

    decode verification at each reported site:
      0x416bc2 [OK] call 0x41c250  bytes=e889560000
      0x44e02c [OK] call 0x41c250  bytes=e81fe2fcff
      0x4db8cc [OK] call 0x41c250  bytes=e87f09f4ff
      0x4df85c [OK] call 0x41c250  bytes=e8efc9f3ff
      0x51b064 [OK] call 0x41c250  bytes=e8e711f0ff
      0x521fc2 [OK] call 0x41c250  bytes=e889a2efff
      0x5230dc [OK] call 0x41c250  bytes=e86f91efff
      0x65f092 [OK] call 0x41c250  bytes=e8b9d1dbff
      0x6bc364 [OK] call 0x6bedb0  bytes=e8472a0000
      0x6bc3aa [OK] call 0x6bedb0  bytes=e8012a0000
      0x6cc999 [OK] call 0x41c250  bytes=e8b2f8d4ff
      0x710213 [OK] call 0x41c250  bytes=e838c0d0ff
      0x7354f2 [OK] call 0x41c250  bytes=e8596dceff
      0x742699 [OK] call 0x41c250  bytes=e8b29bcdff
      0x742a94 [OK] call 0x41c250  bytes=e8b797cdff

全文件扫描没有发现 .text 之外的额外汇中，15 个站点全部落在 .text，且逐站点解码全部回读为
call 对应目标（无误报，无漏报）。

### A.5 三种方法一致性结论

    0x6bedb0：capstone（重启后）2 条 = 原始 E8 法 2 条 = 全文件 E8 法 2 条；站点集完全相同
    0x41c250：capstone 13 条 = 原始 E8 法 13 条 = 全文件 E8 法 13 条；站点集完全相同

注意：第 3 种方法（裸扫 0xE8）在无指令边界约束时天然会误报（.text 里有 81,715 个 0xE8 字节），
本次它对这两个目标恰好与 capstone 完全一致，属于两个 5 字节窗口双向解码互证，而不是「裸扫可信」。

### A.6 解析器形式覆盖验证（正面验证「同时接受 0x 与十进制」这条要求）

命令：python3 内联脚本，输出存 _r131/_audit_deepseek/d1_decform_check.txt

原始输出：

    total call mnemonics: 94786
      hex-form call operands: 68253
      decimal-form call operands: 0 []
      neither (register/indirect): 26533
    parse_imm('0x6bedb0') = 7073200
    parse_imm('eax') = None
    parse_imm('dword ptr [eax]') = None
    --- corrected equivalence test ---
      0x6bedb0 -> 7073200 ; 7073200 -> 7073200 ; equal=True
      0x41c250 -> 4309584 ; 4309584 -> 4309584 ; equal=True

事实：
- 全 .text 94,786 条 call 助记符中，68,253 条操作数是 0x 形式，0 条是十进制形式，
  26,533 条是寄存器/内存间接（如 call eax、call dword ptr [ecx]）。
- 解析器对两种形式都返回同一个整数（等值测试 equal=True）。
- 因此本题得到 0 的原因与「十进制打印」无关；真正原因是 A.1 记录的
  capstone 生成器在 0x46f5a0 提前终止。这里如实记录，避免把 0 归因错方向。
- 首次勾等值测试时我把 0x6bedb0 的十进制手抄成 7077296（正确值 7073200），
  导致两个 False；修正手抄值后为 True。解析器本身无 bug。

## 任务 B：字节体对比

命令：python3 _r131/_audit_deepseek/b1_body.py

原始输出（完整）：

    .text VA=0x401000 len=4063232
    A_off 0x2bedb0 B_off 0x1c250
    A hex: 56578bf98b0785c074068b0850ff51088b442414a81474528b4c240c8d5424105268c07b8100508b44241c5051ff15fc157e0085c07c4c8b54241052ff1500167e008bf085f67c118b4424105768c07b8100508b08ff118bf08b442410508b10ff52088bc65f5ec20c00
    B hex: 56578bf98b0785c074068b0850ff51088b442414a81474528b4c240c8d5424105268c07b8100508b44241c5051ff15fc157e0085c07c4c8b54241052ff1500167e008bf085f67c118b4424105768b07b8100508b08ff118bf08b442410508b10ff52088bc65f5ec20c00
    diff_count 1
      offset 0x4e  A=0xc0  B=0xb0
    bodyA_hit_count 1
      hit_va 0x6bedb0  off 0x2bedb0
    negative_control: A[53] 0x7c -> 0xff; changed_body==original? False
    bodyA_flipped_hit_count 0 []
      control flip offset 0 (0x56->0xff) hits=0
      control flip offset 1 (0x57->0xff) hits=0
      control flip offset 26 (0x24->0xff) hits=0
      control flip offset 52 (0xc0->0xff) hits=0
      control flip offset 79 (0x7b->0xff) hits=0
      control flip offset 105 (0x00->0xff) hits=0
    bodyB_hit_count 1 ['0x41c250']

数字：

    B.1 体 A = 0x6bedb0 起 106 字节，体 B = 0x41c250 起 106 字节
    B.2 不相等字节数 1；偏移 0x4e（十进制 78）：A = 0xc0，B = 0xb0。恰为 1 个，符合预期
    B.3 全 .text 中与体 A 完全相同的字节串命中数 1，唯一命中在 0x6bedb0 自身
    B.4 反控：体 A 中段（偏移 53，原值 0x7c）改 0xff 后命中 0
        另加 6 个偏移（0, 1, 26, 52, 79, 105）单字节翻位，命中全部为 0

### B.5 差异字节的定位（为什么会差这一个字节）

命令：python3 _r131/_audit_deepseek/b2_diff_locate.py

原始输出：

    imm32 0x817bc0 inside bodyA at offset 34
    imm32 0x817bb0 inside bodyB at offset 78
    diff offset 0x4e = 78 -> A[0x4e]= 0xc0 B[0x4e]= 0xb0
    surrounding A 0x48..0x53: 8b4424105768c07b8100508b
    surrounding B 0x48..0x53: 8b4424105768b07b8100508b
    imm32 spans bodyA offsets 0x22..0x25; differing byte 0x4e is byte index 44 of the imm32

上面最后一行是脚本的措辞缺陷，如实标注：b2_diff_locate.py 用 str.find 只取到
0x817bc0 的第一次出现（偏移 0x22），于是把 0x4e 减出 44。0x4e 并不是同一 imm32
的第 44 字节，而是体 A 里第二次出现的 4 字节 0x817bc0 字段的首字节（对齐到 4 字节：
0x4e, 0x4f, 0x50, 0x51）。修正依据是同一脚本更早的两行：
body A 里 0x817bc0 出现在 0x22 与 0x4e 两处；差异字节 0x4e 正是第二处的首字节。
objdump 侧（B.6）也印证：偏移 0x4d 处的 push 立即数在体 A 是 0x817bc0，在体 B 是 0x817bb0。
报告采用修正后的口径，不采用 44 这个数。

结论（纯字节位置，无推测）：
- 体 A 里 0x817bc0 的小端 4 字节出现在偏移 0x22 和 0x4e 两处。
- 体 B 里 0x817bc0 只出现在偏移 0x22；偏移 0x4e 处是 0x817bb0。
- 差异就是第二个 push 的立即数 0x817bc0 对 0x817bb0，两体的其余 105 字节完全相同。

补充核验命令（脚本内联，输出存 b3_addendum_out.txt）：

    python3 - <<EOF  (读 ra2bench/gamemd.exe，统计体内 imm32 位置与全文件体 A 命中)
    ...

原始输出：

    body A occurrences of imm32 0x817bc0: ['0x22', '0x4e']
    body A occurrences of imm32 0x817bb0: []
    body B occurrences of imm32 0x817bc0: ['0x22']
    body B occurrences of imm32 0x817bb0: ['0x4e']
    A tail 8 bytes: 088bc65f5ec20c00  B tail 8 bytes: 088bc65f5ec20c00
    whole-file occurrences of bodyA(106):
      file offsets: ['0x2bedb0']

注意：上面的偏移指体内相对偏移，0x4e 处那 4 字节的原值是 0xb0 7b 81 00（体 B），
0xc0 7b 81 00（体 A）。全文件搜索也确认体 A 这份 106 字节串在整文件里只出现 1 次，
这一点与 B.3 的 .text 内统计一致（.text 外再无第二份）。

### B.6 objdump 独立交叉核验（体 A / 体 B 各 106 字节）

命令：

    i686-w64-mingw32-objdump -D -b binary -m i386 -M intel bodyA.bin
    i686-w64-mingw32-objdump -D -b binary -m i386 -M intel bodyB.bin

原始输出（关键两行，两体只在 0x4d 处不同）：

    体 A:
     4d:  68 c0 7b 81 00        push   0x817bc0
    体 B:
     4d:  68 b0 7b 81 00        push   0x817bb0

其余指令逐条相同，末尾均为：

    67:  c2 0c 00              ret    0xc

两体指令条数相同（各 44 条，objdump 计数），字节长度相同（106），
差异落在文件偏移 0x4d 处那条 push 的 imm32 里（该指令为本体第 32 条）。

objdump 指令行计数命令与输出：

    i686-w64-mingw32-objdump -D -b binary -m i386 -M intel bodyA.bin | sed -n '7,60p' | grep -cE '^\s+[0-9a-f]+:'
    44

## 任务 C：两个 GUID 常量

命令：python3 _r131/_audit_deepseek/c1_guids.py

原始输出（完整）：

    VA 0x00817bb0  off 0x00417bb0  bytes 90320f074198d111b70900a024ddafd1
       Data1/2/3 = 0x070f3290 / 0x9841 / 0x11d1  Data4 = b70900a024ddafd1
       GUID = {070F3290-9841-11D1-B709-00A024DDAFD1}
       section = .data  (range 0x812000..0xb79be4)
       raw 4 dwords LE: ['0x70f3290', '0x11d19841', '0xa00009b7', '0xd1afdd24']
    VA 0x00817bc0  off 0x00417bc0  bytes 0000000000000000c000000000000046
       Data1/2/3 = 0x00000000 / 0x0000 / 0x0000  Data4 = c000000000000046
       GUID = {00000000-0000-0000-C000-000000000046}
       section = .data  (range 0x812000..0xb79be4)
       raw 4 dwords LE: ['0x0', '0x0', '0xc0', '0x46000000']

    section list for reference:
      .text    0x00401000 .. 0x007e038d  (rawsize 0x3e0000)
      .rdata   0x007e1000 .. 0x00811074  (rawsize 0x31000)
      .data    0x00812000 .. 0x00b79be4  (rawsize 0x6c000)
      .rsrc    0x00b7a000 .. 0x00b92128  (rawsize 0x19000)
      .detour  0x00b93000 .. 0x00b95718  (rawsize 0x3000)

    imm32 0x817bc0 in .text: count=9
       at 0x413dd9
       at 0x41c272
       at 0x437f59
       at 0x517b6c
       at 0x67d0d1
       at 0x67e5b5
       at 0x6bedd2
       at 0x6bedfe
       at 0x6bee20

    imm32 0x817bb0 in .text: count=4
       at 0x413e01
       at 0x41c29e
       at 0x41c2c0
       at 0x517b93

数字：

    C.1 0x817bb0 = {070F3290-9841-11D1-B709-00A024DDAFD1}
        0x817bc0 = {00000000-0000-0000-C000-000000000046}
    C.2 两个常量都落在 .data（0x812000..0xb79be4），
        都不在 .rdata（.rdata 上界 0x811074，比 0x817bb0 低 0x6b3c）
    C.3 0x817bc0 的小端 imm32 在 .text 中出现 9 次：
        0x413dd9, 0x41c272, 0x437f59, 0x517b6c, 0x67d0d1,
        0x67e5b5, 0x6bedd2, 0x6bedfe, 0x6bee20

### C.4 上方 9 个地址是「立即数起始」，不是指令起始（我自己纠正一次口径）

命令：python3 _r131/_audit_deepseek/c3_imm_capstone.py（capstone 逐指令 detail，操作数用完即丢）

原始输出：

    capstone imm==0x817bc0 instruction count in .text: 9
      0x413dd8  push 0x817bc0
      0x41c271  push 0x817bc0
      0x437f58  push 0x817bc0
      0x517b6b  push 0x817bc0
      0x67d0d0  push 0x817bc0
      0x67e5b4  push 0x817bc0
      0x6bedd1  push 0x817bc0
      0x6bedfd  push 0x817bc0
      0x6bee1f  push 0x817bc0
    capstone imm==0x817bb0 instruction count in .text: 4
      0x413e00  push 0x817bb0
      0x41c29d  push 0x817bb0
      0x41c2bf  push 0x817bb0
      0x517b92  push 0x817bb0

计数相同（9 与 4），但两种口径的地址必须区分：
- 原始 4 字节搜索给出的是 imm32 字段在文件里的字节位置（= 指令地址 + 1，因 68 前缀占 1 字节）；
- capstone 给出的是包含该立即数的指令地址。

9 个包含 0x817bc0 立即数的指令全部是 push，无一条是偶然字节命中。

命令：python3 _r131/_audit_deepseek/c2_imm_context.py

原始输出（逐条上下文，节选每站点一行）：

    site_va 0x413dd9 ... 0x413dd8  push 0x817bc0
    site_va 0x41c272 ... 0x41c271  push 0x817bc0
    site_va 0x437f59 ... 0x437f58  push 0x817bc0
    site_va 0x517b6c ... 0x517b6b  push 0x817bc0
    site_va 0x67d0d1 ... 0x67d0d0  push 0x817bc0
    site_va 0x67e5b5 ... 0x67e5b4  push 0x817bc0
    site_va 0x6bedd2 ... 0x6bedd1  push 0x817bc0
    site_va 0x6bedfe ... 0x6bedfd  push 0x817bc0
    site_va 0x6bee20 ... 0x6bee1f  push 0x817bc0

## 附：产物清单（全部位于 _r131/_audit_deepseek/，只读对象为 ra2bench/gamemd.exe）

    a1_sections.py           PE 节表解析（含一次修正记录）
    a2_callsites.py          首版调用点统计（暴露 capstone 生成器提前停止问题）
    a3_callsites_resync.py   加入重启的调用点统计（A.1/A.2/A.3 正式数字）
    a3_out.txt               上述脚本完整输出
    a4_wholefile.py          全文件 0xE8 扫描 + 逐站点解码复验
    b1_body.py               体 A/体 B 对比、全 .text 命中、反控
    b1_out.txt               上述脚本完整输出
    b2_diff_locate.py        差异字节在 imm32 内的定位
    b3_addendum_out.txt      体内 imm32 出现位置、全文件体 A 命中
    c1_guids.py              GUID 格式化与节归属、imm32 计数
    c1_out.txt               上述脚本完整输出
    c2_imm_context.py        9 个立即数的指令级上下文
    c3_imm_capstone.py       capstone 侧立即数独立计数
    c3_out.txt               上述脚本完整输出
    d1_decform_check.txt     call 操作数 0x/十进制两种形式的覆盖率与解析器等值测试
    R131_AUDIT_deepseek.md   本报告

## 附：最终数字汇总表

    项目                                            值
    call -> 0x6bedb0 条数（capstone / E8 法 / 全文件） 2 / 2 / 2
    call -> 0x41c250 条数（capstone / E8 法 / 全文件） 13 / 13 / 13
    0x6bedb0 调用点地址                              0x6bc364, 0x6bc3aa
    0x41c250 调用点地址                              0x416bc2, 0x44e02c, 0x4db8cc, 0x4df85c,
                                                     0x51b064, 0x521fc2, 0x5230dc, 0x65f092,
                                                     0x6cc999, 0x710213, 0x7354f2, 0x742699,
                                                     0x742a94
    体 A / 体 B 长度                                 106 / 106
    不相等字节数                                     1（偏移 0x4e，A=0xC0，B=0xB0）
    全 .text 中体 A 完全相同命中数                    1（0x6bedb0 自身）
    反控（中段翻 0xff）命中数                        0
    0x817bb0 GUID                                    {070F3290-9841-11D1-B709-00A024DDAFD1}
    0x817bc0 GUID                                    {00000000-0000-0000-C000-000000000046}
    两 GUID 所在节                                   .data（0x812000..0xb79be4）
    0x817bc0 imm32 在 .text 出现次数                 9
    对应指令地址（含它的 push）                      0x413dd8, 0x41c271, 0x437f58, 0x517b6b,
                                                     0x67d0d0, 0x67e5b4, 0x6bedd1, 0x6bedfd,
                                                     0x6bee1f
    .text 合法指令总数（含 64 段各 1 字节跳过）      1,394,120
