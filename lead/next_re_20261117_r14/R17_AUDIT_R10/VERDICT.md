# R17-AUDIT-R10 VERDICT（异族审计，独立实现）

目标：ra2youli\gamemd.exe，4825360 B，SHA-256 73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476，ImageBase 0x400000。
只读打开；未建进程、未调试、未启动；未修改 R17_R10_DISPATCH 下任何文件；产物仅写 R17_AUDIT_R10。
本审计未 import / 复用执行方 work.py；实现见 audit.py。中间结果：raw_results.json、candidates.tsv、jmp_tables.tsv、name_refs.tsv、bytes.tsv。

## 扫描声明
- A1：全文件原始字节匹配 4825360 B。
- A2/A3：.text raw 0x1000..0x3E1000，4,063,232 B，逐字节；含 .text 节尾 raw padding，不扩到全镜像。
- A5：全文件 4825360 B 做名字 VA 的 4 字节小端匹配；host 体及前后各 4KB 复核；正控用锚点对齐解码。
- 反汇编锚点：0x418DDB 为数据区；0x59C97B/0x59C9BE 由前序 ret+填充锚点解码；0x5C62B0、0x756590、0x7CC0DC 为实测/给定锚点；A5 正控锚点 0x5A9C40。

## A1 · 装饰名计数与所在节 —— AGREE（执行方纠正正确；卡面与 R9 旁注错）
匹配口径：全文件逐字节、不要求 4 字节对齐的前缀计数。
- .?A：988 处，988/988 在 .data，.text 0；首处 raw 0x415de8 → VA 0x815de8。
- .?AV：962 处，全在 .data；.?AU：26 处，全在 .data；二者合计 988。
- ??_7：0 处。
结论采用 .?A 宽口径，真值 988，全在 .data。卡面「989 个 .?AV… 都在 .text」错；R17_AUDIT_R9 B4 旁注同样错，而且是错源：它举的 raw file offset 0x415DE8 映射 PE section 后 VA 是 0x815DE8（.data），只有把它误当 VA 才看似落在 .text。所以不是卡面与 R9 二选一，而是两者同错、执行方纠正对。

## A2 · call [reg+reg*4] 0 命中 —— DISAGREE（原否定口径不成立/过窄）
- 执行方那组固定字节 FF14{80,88,90,98,A0,A8,B0,B8}（base=eax、mod00）确实 0 命中。
- 但全 .text 的 FF /2 + SIB scale=4 字节候选存在：0x418DDB FF 14 89（数据区伪命中）、0x756843 FF 14 B5 40 68 84 00（锚点 0x756590 下真指令 call [esi*4+0x846840]）、以及 0x7CC172/21B/257 的 FF 54 .../mod01 真实间接 call。故「FF 14 scale=4 形态全无」为假；「真实 base+index*4 无 disp 的 call 为 0」只能写成窄口径结论。
- 正控：0x756843 是真 FF 14 scale=4 指令。反控：逐字节扫描（非 4 对齐）、合成 pattern 首尾/中段注入 3/3 命中、截断不命中、.text raw end <= file size，见 controls.tsv。

## A3 · 不能触达 #73/#107 —— DISAGREE（主结论未推翻，但支撑叙述有两处硬错）
8 处逐个结论见 candidates.tsv：
1. 0x418DDB 伪命中：处于 0x418DD8 起的重复跳表数据记录，非指令。
2. 0x59C97B 伪命中：真实流 0x59C97A 83 FF 64 cmp edi,0x64 / 0x59C97D 8B F7 mov esi,edi。
3. 0x59C9BE 伪命中：真实流 0x59C9BD 83 FF 64 cmp edi,0x64 / 0x59C9C0 8B C7 mov eax,edi。
4. 0x5C64C3 伪命中：从 0x5C62B0 锚点对齐后落在 0x5C64C2 33 FF xor edi,edi 内部；FF 24 80 还是 jmp 不是 call。执行方把它当字符串循环内真实 call，错。
5. 0x756843 真指令：call [esi*4+0x846840]；表 0x846840 前 32 项为 .text 函数指针，#32 起为 0/小整数，触达不到 73/107。
6-8. 0x7CC172/0x7CC21B/0x7CC257 真指令，base 来自 SEH 异常链结点数组，index 为 12 字节结点步长的派生值，与 0x7E3EBC 槽段无关。
387 处 jmp [reg*4+disp32]：独立复算确为 387；表地址真值 0x4059d0..0x87d44e，386 个在 .text、1 个在 .data，落槽段 0。执行方报的 0x8069D0..0xC7E44E 是给真值整体加了 0x401000（把绝对 VA 当 RVA 再加基址），并据此误说「全在 .data」。未找到能把基址设为 0x7E3EBC 附近且 index 达 73/107 的链；但证据正文必须改，故本项 DISAGREE。

## A4 · host2 fn_end —— AGREE（真值 0x43BCDE）
字节行 0x43BCD0: E8 8B F1 21 00 8B C6 5F 5E 5D 5B C2 08 00 | 6A 01 8B CE E8...。
0x43BCDB..0x43BCDD = C2 08 00 是 3 字节 ret 8；fn_end 用半开区间时应为下一条指令起点 0x43BCDE。0x43BCDB 是 ret 指令首字节地址，不是 fn_end；0x43BCDE 不是把 ret 算进去，而是 ret 8 三字节之后的下一函数首字节 6A 01（push 1）。执行方 REPORT/hosts.tsv 现值 0x43BCDE 正确。

## A5 · host 内装饰名引用 0 —— DISAGREE（结论幸存，证据/正控不成立）
- 全文件 .?A 名字 VA 的 4 字节小端 raw 匹配确为 6 处，但锚点/指令操作数复核后 有效立即数引用 0 处：0x42B481 跨 pop eax+jmp；0x5159DA 跨 ror/test/add；0x5F3957、0x6E8B20 是 mov byte [esi+0x82],bl 的 opcode/modrm/disp8+0；0x87C5F8 在 .data 数据表；0xB85FE0 在 .rsrc 字符串资源。都不是指向名字 VA 的立即数操作数。详见 name_refs.tsv。
- 三个 host 体及前后各 4KB 的 raw 匹配数均为 0（host1/host2/host3 全 0），所以「引用计数 0」本身成立；但执行方把 6 个 raw coincidence 写成「全文件只有 6 处引用」，且无有效正控，按 R14_COMMON §2.8 规则 A 不可采信。
- 正控改用锚点对齐的真立即数指令：0x5A9C83: 68 40 99 5A 00 push 0x5A9940（锚点 0x5A9C40），同一扫描/解码链能命中真 push imm32。反控：6 个名字 raw 匹配逐个被指令边界/操作数类型排除；host 窗口仍为 0。

## 必改项（4 条）
1. A1：卡面与 R17_AUDIT_R9 B4 旁注把 raw file offset 当 VA，须改为 .?A 988/988 .data、.text 0；.?AV 962、.?AU 26、??_7 0。
2. A2：把「call [reg+reg*4] 全 .text 0 命中」改成窄口径，并补 0x756843 正控与 0x418DDB 数据伪命中排除；补正反控行。
3. A3：把 387 处表地址范围改为 0x4059d0..0x87d44e（386 .text + 1 .data），删除「全在 .data」；0x5C64C3 改判伪命中；保留「槽段 0 命中、未发现触达链」。
4. A5：删除「全文件只有 6 处引用」的断言，改报 raw=6/valid=0 并列出 6 处；补 §2.8 正控（0x5A9C83）与反控。

最终：A1 AGREE；A2 DISAGREE；A3 DISAGREE；A4 AGREE；A5 DISAGREE。
