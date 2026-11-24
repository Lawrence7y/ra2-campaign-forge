R93 执行卡 · 独立复核「20 站差额」的每站分类（只读，禁写 live 树）

背景：主会话有两个既有实现，同一命题得到不同数字：
  V1（_r92/vt_this_r92.py，主会话 R92 自写）严格口径 851/929
  V2（_r92/_exec2/exec_vt_independent.py，hy4 执行员独立实现）严格口径 871/929
两套实现在全库 929 个 call [reg+0x48] 站点上恰好有 20 站分类不一致，
差额就在这 20 站。你的任务是**从字节出发**独立裁定这 20 站，不猜、不引用
任何一方的结论数字。

一、前置（必须自己算，不许抄）
  1. 校验 ra2bench/gamemd.exe 的 sha256，应为 73201cc0 开头那串全长 64 位。
  2. 用 i686-w64-mingw32-objdump -d -M intel 反汇编，用地址行建立全库指令
     起始集。报告总指令条数。注意不要用 capstone 从头线性扫（会少 9 倍）。
  3. 统计 call DWORD PTR [reg+0x48] 站点，报告站点数。

二、给定 20 个争议地址（这是唯一允许的输入）
  0x41a401 0x448606 0x4ae115 0x4ae1dd 0x4b3749 0x4b427a 0x51aeab 0x53b0ff
  0x5db567 0x68ae5c 0x68ae6c 0x692552 0x6925bd 0x6a2d98 0x6a38a6 0x6f80fb
  0x7be88c 0x7be908 0x7be9e3 0x7c379b
  另有 2 站 0x6933b1 与 0x6abf9d 两方在 P1/P3 归属上不同，也要一并裁。

对每个站点，自己反汇编取该地址前 15 条指令原文（含字节），逐站给出：
  A. 该站的 call 目标寄存器（reg）。
  B. this 寄存器 ecx 在该站点的值：是「某函数入参」「某条指令的立即数」
     「某次 call 的返回值」「某地址处的内容」，还是「无法确定」，并给依据指令地址。
  C. reg（vt 寄存器）在该站点的值，同样给形态与依据指令地址。
  D. 判定：
       HIT  表示 vt 的值恰好等于「this 值这个地址处的内容」（即 vt == [this]）
       MISS 表示不等于，或任一侧无法确定
     无法确定就必须写 MISS，不许因为「看起来像对象」就判 HIT。
  E. 若 D 判 HIT，必须写明：vt 与 this 的等式是在**哪几条指令**上成立的，
     即把从 ecx 赋值到 call 的那条链和从 vt 寄存器赋值到 call 的那条链
     都列出来，证明二者是同一个表达式。

三、必须注意的三个陷阱（这几条会直接决定结论）
  1. push 不是写者。指令 push esi 的 operand0 是 esi，但它读 esi，不写 esi。
     若把 push 当写者，回溯会在此截断。
  2. lea 与 mov 不同层。lea r,[m] 得地址，mov r,[m] 得该地址处的内容。
     二者不能互换。
  3. 回溯不得跨越「前驱不唯一」的基本块边界。若 reg 在块入口处没有唯一来源，
     它就是未知量，不能继续向前找一条线性路径上的写者当作它的值。
     注意：只跨一个前驱的块是可以继续上行的，不要一律到块首就停。
  4. 两个不同的未知量不相等。两个 call 的返回值即使都是 eax，也不是同一个值，
     除非它们是同一条 call 指令。

四、输出（只写这个目录）
  _r93/_exec/verdict.tsv
    表头：site	reg	this_form	vt_form	verdict	chain_evidence
    22 行数据，verdict 只能是 HIT 或 MISS。
  _r93/_exec/REPORT.md
    逐站一段，给地址与字节，说明判定依据。
    最后给三个汇总数字：HIT 几站、MISS 几站、其中「无法确定」几站。
  _r93/_exec/selftest.log
    至少 12 项断言，带正控与反控各一条，逐项打印 PASS/FAIL。
    正控要求：手工构造一条 mov edx,[esi] / mov ecx,esi / call [edx+0x48] 的
    窗口，断言你的判定器判 HIT。
    反控要求：把同窗口的 mov ecx,esi 改写成 mov ecx,edi，断言判 MISS。

五、纪律
  - 只读 ra2bench/gamemd.exe，只写 _r93/_exec/。
  - 禁止复制 live 树任何目录；产物总量上限 20 MB。
  - 不许修改 check_disc.py、DISC_RECHECK.tsv、R14_COMMON.md、看板、台账。
  - 不许引用 V1 或 V2 的任何数字当作依据，只认你自己反汇编出来的字节。
  - 单次运行控制在 8 分钟内，脚本只跑一次，不要反复调试。
  - 卡面上不要出现反引号字符。
