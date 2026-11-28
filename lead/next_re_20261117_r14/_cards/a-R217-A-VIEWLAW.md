# R217-A 独立复现结果（exec / hy4 / hy4flash-free）

- 目标二进制：ra2bench/gamemd.exe
- SHA-256：73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- 脚本：_r217/cardA_survey.py（SHA-256 d40d1c35007bd3f433173dc6f4d51237a0cc3748b804a380abc9cd290859acd9）
- 完整证据：_r217/cardA_evidence.txt（506 行，SHA-256 2a92ebe07d1fe58a3965bbf373b0110ca486bfa4bb91f2b33816811e947aeeb9）
- 分节：.text=00401000..007E1000，.rdata=007E1000..00812000，.data=00812000..0087E000
- 全程使用 disasm_lite 流式反汇编；仅对不超过 64 字节的片段使用 detail 反汇编。

## A1 视图骨架普查

实测：

- CompleteObjectLocator 候选数：1203
- 虚表数：1208
- 其中 mdisp 不等于 0：264
- slot0 不落在 .text 的虚表数：5
- mdisp 分布：0 -> 944，4 -> 95，8 -> 78，12 -> 78，24 -> 6，36 -> 1，40 -> 1，44 -> 1，1728 -> 1，21784 -> 3
- 槽数分布（槽数 -> 表数）：

0->5, 1->199, 2->14, 3->82, 4->8, 5->160, 6->85, 7->405, 8->10, 9->62, 10->20, 11->6, 12->1, 15->2, 16->2, 17->6, 18->4, 22->1, 23->2, 24->26, 25->3, 27->13, 28->1, 30->1, 31->1, 33->4, 34->6, 35->1, 36->3, 38->2, 39->1, 40->7, 41->3, 42->1, 44->1, 45->1, 46->1, 48->6, 49->1, 50->13, 51->2, 52->8, 53->1, 54->2, 55->4, 122->10, 123->1, 124->1, 125->1, 157->1, 161->1, 256->6

实现要点：

- MSVC COL 的实际可靠特征是 sig=0、pCD=0、pTD 指向 .?AV/.?AU TypeDescriptor、pCHD 指向 sig=0 且 nb 在 1..64 的合法 CHD。此二进制中 COL 的 +0x14 self 字段经常为 0，不能拿 self==COL 当必要条件；用 self==COL 会得到 0 个候选的错误结果。
- 虚表按数据段内每个 DWORD 是否等于某个 COL 地址来定位，V=该 DWORD 地址+4；槽数从 V 开始逐 DWORD 读取，值不在 .text 即停止，硬上限 256。

## A2 adjustor thunk 律（律U）

实测：

- thunk 形表数：101
- 律U 成立数：101
- 违例数：0
- 违例逐条：无
- 反控判据 N 等于 mdisp 减 1：成立数 0（101 张全部不满足）。

实现要点：

- 对每张 mdisp 非零表，用 disasm_lite 取 slot0 函数前两条指令，要求第一条是 sub dword ptr [esp + 4], N，第二条是 jmp 绝对地址。
- 目标表集合取所有 slot0 指向同一 jmp 地址的表；期望值集合为当前表 mdisp 减各目标表 mdisp，N 落在集合内即成立。注意 disasm_lite 返回四元组（地址、长度、助记符、操作数），操作数索引不能写错。

## A3 主对象转发桩

实测：

- 命中函数数：1
- 涉及表数：76
- K 取值分布：0x2C -> 1 个函数（十进制 44）
- 命中函数地址：0x00410210，出现在 76 张表中，每次均在槽序号 3（0 起）。
- 槽序号分布：3 共 76 次。

完整五条指令：

00410210  8b442404  mov eax, dword ptr [esp + 4]
00410214  8b50fc    mov edx, dword ptr [eax - 4]
00410217  8d48fc    lea ecx, [eax - 4]
0041021A  ff522c    call dword ptr [edx + 0x2c]
0041021D  c20400    ret 4

实现要点：

- 先按虚表槽函数扫描，再补一轮 .text 原始字节扫描，锚点是 8b442404（mov eax,[esp+4]），随后按五条指令的助记符和操作数逐条校验。
- 单纯只扫 A1 枚举到的槽函数会漏掉它，因为这个共享桩虽然出现在很多表的槽 3，但不是独立 COL 主槽候选集合里的唯一入口。

## A4 接口查询函数 0x410260

实测反汇编（0xb0 字节，逐条地址、字节、汇编）：

00410260  8b44240c           mov eax, dword ptr [esp + 0xc]
00410264  53                 push ebx
00410265  85c0               test eax, eax
00410267  7509               jne 0x410272
00410269  b803400080         mov eax, 0x80004003
0041026E  5b                 pop ebx
0041026F  c20c00             ret 0xc
00410272  8b54240c           mov edx, dword ptr [esp + 0xc]
00410276  56                 push esi
00410277  57                 push edi
00410278  b904000000         mov ecx, 4
0041027D  bf907c7f00         mov edi, 0x7f7c90
00410282  8bf2               mov esi, edx
00410284  33db               xor ebx, ebx
00410286  c70000000000       mov dword ptr [eax], 0
0041028C  8b5c2410           mov ebx, dword ptr [esp + 0x10]
00410290  f3a7               repe cmpsd dword ptr [esi], dword ptr es:[edi]
00410292  7502               jne 0x410296
00410294  8918               mov dword ptr [eax], ebx
00410296  55                 push ebp
00410297  b904000000         mov ecx, 4
0041029C  bf807c7f00         mov edi, 0x7f7c80
004102A1  8bf2               mov esi, edx
004102A3  33ed               xor ebp, ebp
004102A5  f3a7               repe cmpsd dword ptr [esi], dword ptr es:[edi]
004102A7  7502               jne 0x4102ab
004102A9  8918               mov dword ptr [eax], ebx
004102AB  b904000000         mov ecx, 4
004102B0  bf707c7f00         mov edi, 0x7f7c70
004102B5  8bf2               mov esi, edx
004102B7  33ed               xor ebp, ebp
004102B9  f3a7               repe cmpsd dword ptr [esi], dword ptr es:[edi]
004102BB  5d                 pop ebp
004102BC  7502               jne 0x4102c0
004102BE  8918               mov dword ptr [eax], ebx
004102C0  8bf2               mov esi, edx
004102C2  b904000000         mov ecx, 4
004102C7  bfe09a7e00         mov edi, 0x7e9ae0
004102CC  33d2               xor edx, edx
004102CE  f3a7               repe cmpsd dword ptr [esi], dword ptr es:[edi]
004102D0  5f                 pop edi
004102D1  5e                 pop esi
004102D2  750d               jne 0x4102e1
004102D4  85db               test ebx, ebx
004102D6  7405               je 0x4102dd
004102D8  8d4b04             lea ecx, [ebx + 4]
004102DB  eb02               jmp 0x4102df
004102DD  33c9               xor ecx, ecx
004102DF  8908               mov dword ptr [eax], ecx
004102E1  833800             cmp dword ptr [eax], 0
004102E4  7509               jne 0x4102ef
004102E6  b802400080         mov eax, 0x80004002
004102EB  5b                 pop ebx
004102EC  c20c00             ret 0xc
004102EF  8b03               mov eax, dword ptr [ebx]
004102F1  53                 push ebx
004102F2  ff5004             call dword ptr [eax + 4]
004102F5  33c0               xor eax, eax
004102F7  5b                 pop ebx
004102F8  c20c00             ret 0xc
004102FB  90                 nop
004102FC  90                 nop
004102FD  90                 nop
004102FE  90                 nop
004102FF  90                 nop
00410300  b801000000         mov eax, 1
00410305  c20400             ret 4
00410308  90                 nop
00410309  90                 nop
0041030A  90                 nop
0041030B  90                 nop
0041030C  90                 nop
0041030D  90                 nop
0041030E  90                 nop
0041030F  90                 nop

(a) 栈上 IID 指针的读取次数：1 次。

推算过程：入口处 delta=0；0x410264 执行 push ebx 后 delta=4，jne 跳到 0x410272 时该 push 仍然有效，所以 0x410272 的 [esp+0xC] 对应原始 esp+8（IID 指针）。0x410276、0x410277 又 push esi、push edi，使 delta=12，所以 0x41028C 的 [esp+0x10] 对应原始 esp+4（this 指针）。0x410260 的 [esp+0xC] delta=0，对应原始 esp+0xC（输出指针）。

(b) 输出指针来自原始 esp+0xC，即 stdcall 的第一个实参 ppv；进入函数时 eax 保存该值，后续所有 mov [eax], ... 都写到它。

(c) 四个 16 字节常量地址与 GUID：

- 0x007F7C90 -> 00000000-0000-0000-C000-000000000046（IID_IUnknown）
- 0x007F7C80 -> 00000109-0000-0000-C000-000000000046
- 0x007F7C70 -> 0000010C-0000-0000-C000-000000000046
- 0x007E9AE0 -> 170DAC82-12E4-11D2-8175-006008055BB5

(d) 第 4 个常量匹配成功时，写入输出指针的值是实参 this（原始 esp+4，保存在 ebx）加 4，即 lea ecx, [ebx+4]，随后 mov [eax], ecx。加数 4 是 lea 指令里的立即数，不是从表里查出来的。

实现要点：

- 对 0x410260 起 0xb0 字节用 Capstone 全量逐条反汇编；栈偏移按控制流块跟踪 push/pop 引起的 esp 变化，不把 jne 跳转后的 push ebx 误当成已撤销。
- 四个常量来自 mov edi, imm32 的操作数，再按 GUID 的 4-2-2-2-6 字节布局拆解；第 4 个匹配分支单独看 lea ecx,[ebx+4] 与 mov [eax],ecx。

## 我复核出与我方基线不一致的项

- 调度卡背景声称 COL 的 +0x14 self 字段指向自身，并且 pCD 处恒 0；本二进制中符合严格 self==COL 特征的记录只有 BCD 样结构，真正的 1203 个 COL 里绝大多数 +0x14 为 0。若按背景的 self 字段筛 COL，会得到 0 个候选，A1/A2/A3 全部塌成 0。
- 其余项目因为没有给出我方具体基线数字，只给了待验证的规律描述，无法逐项对照；就规律本身而言，律U 成立、反控为 0、主对象转发桩 K=0x2C 且恒在槽 3、QueryInterface 的四个 GUID 与 this+4 写入均已在上面给出实测证据。
