# R188 执行卡 · gamemd.exe 间接调用形态与 vt==[esi] 传播独立普查

## 你的角色与边界
只读静态取证。禁止运行 gamemd.exe，禁止动态注入。禁止修改任何已有文件；
唯一允许写入的目录是 /home/t628/projects/ra2-campaign-forge/_r188/exec_hy4/。
禁止碰触 R14_COMMON.md / LEAD_LOCK / STATUS_BOARD.md / FACT_INDEX* / R17_LEAD_BASELINE。

## 环境与硬红线（必须遵守）
- 工作目录 /home/t628/projects/ra2-campaign-forge，二进制 ra2bench/gamemd.exe（4,825,360 B）。
- 可用：python3 + capstone + pefile，rg，i686-w64-mingw32-objdump。
- 防 OOM 硬红线：严禁一次性对整段 .text 开 md.detail=True 调 md.disasm()。
  全段线性扫描只能用 md.disasm_lite()，并且按 <=65536 字节分块流式迭代、每块用完即释放。
  只有极少数命中地址才允许单独 new 一个 detail=True 的反汇编器解那几条。
- 所有命令带 timeout（建议 timeout 600）。不要留后台孤儿进程。
- VA 到文件偏移必须走 PE 节表映射（读节表头，用 rawptr + (va - va_base)），
  不得用 va - 0x400000 之类的减法近似。

## 要交付的四组数字（全部先实测再填，禁止预估）

A1 间接调用形态普查：在 .text 全部指令边界上（disasm_lite 线性扫描即可）统计
   mnemonic == call 且 operands 形如 "dword ptr [...]" 的站点总数，
   并按 [ ] 内的基址寄存器分类计数（eax / ecx / edx / ebx / esp / ebp / esi / edi /
   绝对地址 / 带 index 的），每一类给出计数。
A2 其中「基址是 esi 且带位移」的站点：总数、位移去重后的个数、位移是否全部 4 字节对齐
   （给出对齐数与不对齐数，不对齐的逐条给地址）。
A3 vt 传播普查（这是本卡核心）：找出形如
   先有 mov r32, dword ptr [esi]   （把虚表指针从对象基址 esi 读出）
   之后在有限窗口内出现 call dword ptr [同一个 r32 + disp]
   且两者之间没有任何指令写这个 r32（保守判定：任何以该寄存器为第一操作数且
   助记符属于 mov/lea/xor/add/sub/and/or/pop/inc/dec/mul/imul/div/idiv/neg/not/shl/shr/sar
   或 pop 该寄存器的指令都算写入，命中即放弃这一对）
   的配对数。窗口取 32 条指令。给出：配对数、涉及的 call 站点去重数、
   位移取值去重个数、以及每个位移对应的表槽下标（disp 除以 4）。
   同时给出「mov r32,[esi] 站点总数」与「这类站点里最终没有配到 call 的数量」。
A4 槽位覆盖：用下面这条固定规则枚举虚表（不要自己另发明规则，保证与我方可比）：
   在 .rdata 与 .data 里按 4 字节步进滑动，取 5 个连续 dword d0..d4；
   若 d0 属于 {0,1}、d2 == 0、d3 落在 .data 段、d4 落在 .rdata 段、
   且从 d3+8 起读到以 ".?A" 开头并以 "@@" 结尾的 C 串，
   则记该处 20 字节为一个 COL，键为它的 VA。
   随后在 .rdata 与 .data 里按 4 字节步进找 dword v 落在 .text 文件范围 [lo, hi_file) 内，
   且该 dword 前一个 dword 恰是某个 COL 的 VA，则记该处为一个 vtable，键为其 VA。
   报出 COL 个数与 vtable 个数。
   然后对 A3 里出现频次最高的 5 个位移，分别报：该槽下标下「槽数够长的 vtable 个数」
   与「这些 vtable 在该槽上取值的去重个数」。
   槽数定义：从 vtable VA + 4 起逐 dword 向后走，直到取值不再落在 .text 文件范围为止
   （注意 vtable VA 处的第一个 dword 本身也算一个槽，从它开始数）。

## 自证与反控（必须真跑、真给出反控数字）
N1 把 A1 的判据从 call 改成 "jmp" 再跑一遍，给出 jmp 形态的间接站点数（应与 call 不同，
   若恰好相同要如实说明）。
N2 把 A3 的窗口从 32 条指令改成 1 条指令，给出配对数（必须显著变小，给出前后两个数）。
N3 把 A3 的「中间不得写该寄存器」这条检查整体关掉，给出配对数（必须变大或相等，
   给出前后两个数并说明差值来自哪里）。
N4 在 A4 的 COL 判据里把 d2 == 0 改成 d2 == 1，报出 COL 个数（必须明显小于原值）。

## 输出
- 一个自测脚本，路径 _r188/exec_hy4/r188_scan.py，脚本内自己写 assertions（至少 12 条），
  末尾打印 "断言 N 条，FAIL M 条"，有 FAIL 就以非 0 退出码退出。
- 一个结果 JSON，路径 _r188/exec_hy4/r188_report.json，含 A1–A4 与 N1–N4 全部数字。
- 一段不超过 25 行的纯文本结论，路径 _r188/exec_hy4/r188_summary.txt，
  逐条列出你测到的数字，一个数字都不许留空、不许写占位。
- 一条命令即可复跑：python3 _r188/exec_hy4/r188_scan.py，必须在 600 秒内跑完。

卡面纪律：本卡文件里不得出现反引号字符，你写脚本时正常使用即可。
