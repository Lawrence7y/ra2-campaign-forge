R92 审计卡 · 独立复算 vt == [this] 值树判据（只读，禁写 live 树）

背景：R91 报 call [reg+0x48] 中 905/929 = 97.42% 的 vt 寄存器来自
      mov (obj),%reg，并据此宣称 vt == [obj]。R92 复算怀疑该数字有两处
      方法缺陷，换用值树判据重测得 849/929 = 91.4%，并把剩余站点分为
      P1/P2/P3/PX 四类。你的任务是独立实现一遍，不复用任何既有脚本。

必须独立完成的机械统计（全部只读 ra2bench/gamemd.exe）：

1) 用 i686-w64-mingw32-objdump -d -M intel 反汇编，用地址行建立
   全库指令起始集，统计指令条数与 call DWORD PTR [reg+0x48] 站点数。
   同时报告 capstone 从头线性扫 .text 得到的指令条数，两者必须差 8 倍以上。

2) 缺陷 1 验证：把「第一条 operand0 写该寄存器的指令」当写者的旧口径
   实现一遍，统计 push 指令被误当作写者的情况有几处。
   给出这 5 个站点的地址。

3) 缺陷 2 验证：分别用 lea 与 mov 装载 vt 寄存器，统计各自站点的
   「vt 寄存器值是否为 load(this)」。必须区分 lea（得地址）与
   mov（得该地址处内容），报告二者计数。

4) 值树判据独立实现：
   为每个寄存器在站点处的值构造表达式（imm / load(addr) / plus(e,d) / reg0），
   地址表达式的基址寄存器也必须先求值。this = ecx 的值。
   统计 val(vtreg) == load(this) 的站点数（P1），
   val(vtreg) == load(plus(this,d)) 且 d!=0 的站点数（P2），
   val(vtreg) == load(imm A) 且 this==imm A 的站点数（P3），
   其余计入 PX 并给出 PX 中「vt 不是 load 形态」「vt 基址不是 this」的分布。

5) 反控：随机取 800 个 .text 地址 + 随机寄存器，同一判据的命中率，
   以及观测/基线的倍数。

6) 抽查 6 个 PX 站点，逐个给出该处前 10 条指令的反汇编原文，
   并说明为什么它不满足 vt == [this]。

工具：python3 + capstone + pefile 或 i686-w64-mingw32-objdump。
反汇编起始集必须用 objdump 地址行，不要用 capstone 从头线性扫。

产物目录：_r92/_audit/  （只允许写这个目录）
禁止：复制 live 树任何目录、写 _r92/_audit 之外任何路径、修改 gamemd.exe。
不读也不 import _r92/vt_this_r92.py（那是被审对象）。产出上限 20 MB。

自测要求：至少 12 项断言，必须带正控与反控各一条，打印每项 PASS/FAIL。
最终把结论写 _r92/_audit/REPORT.md，逐条给数字，不写形容词。
