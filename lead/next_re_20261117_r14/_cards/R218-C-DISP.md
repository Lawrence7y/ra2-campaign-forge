# R218-C 虚槽高序号消费位点扫描（disp >= 0x400 的间接 call/jmp）

## 环境
工作目录 /home/t628/projects/ra2-campaign-forge 。python3 + capstone 可用。
只读模块 _r185/pe185.py：P.B[段名] 给 lo/rawptr/rawsize；P.RAW 全文件字节；P.dw(va)；P.where(va)。
防 OOM 硬红线：严禁对整段 .text 一次性 md.disasm() 且 detail=True。必须按 <= 64KB 分块，
每块用 md.disasm_lite() 迭代，及时 del 释放；只对最终命中的少量地址单独开 detail=True 复核。
产物落 /home/t628/projects/ra2-campaign-forge/_r218/ ，文件名前缀 cardC_。

## 背景（主会话已实测，作为正控必须复现）
- .text 段：lo=0x401000，文件内长 0x3e0000（raw 起点 0x1000）。
- 真虚表 1214 张，槽数最大值 344（UnitClass 0x7f5c70）。
- 已证的转发桩：函数 0x410210 内含指令 call dword ptr [edx+0x2c]（槽序号 11），共 76 处被引用。
- 每张虚表 T 的槽序号 k 对应对象内存 [this+4k]，因此「槽序号 >= 256」的消费必须在指令里出现 disp >= 0x400。

## 唯一目标 C1：全 .text 扫描「内存操作数间接调用/跳转」并按 disp 分桶
扫 call/jmp 两类指令，操作数形态为 mem，基址是通用寄存器（eax/ebx/ecx/edx/esi/edi/ebp），
且索引寄存器为空、scale 为 1（即 [reg+disp] 或 [reg]），记录：
  (a) 全部命中的总数；
  (b) disp 值直方图：把 disp 按 4 整除得槽序号 s，报 s 的分布 top 30（s, 次数）；
  (c) 单独报 s >= 256 的位点总数、涉及的 s 值清单（全部，十六进制 disp 与十进制 s）；
  (d) 对 s >= 256 的位点，逐个打印：指令地址、原始 8 字节 hex、disasm_lite 文本；
  (e) 正控 1：disp == 0x2c 的位点集合里必须包含 0x410210 函数体内的那条（报出它的地址），
      并报 disp==0x2c 的总位点数；
  (f) 正控 2：disp == 0 的位点数应远大于 disp==0x2c；
  (g) 反控：把判据改成「disp >= 0x400 且 disp 不是 4 的倍数」，计数必须为 0；
  (h) 反控：把扫描范围限制到 .text 前 64KB 时，计数应远小于全段（报两值）。

## 输出格式
一条命令输出全部证据（不要分多次试探）。逐条 (a)..(h) 给实测数字。
最后单列「异常与不确定」：特别说明你是否观察到 disp 不是 4 的倍数的间接调用（若有，全部列出），
以及是否有 [reg+reg*4+disp] 这类被排除的形态导致漏计（给出你的排除计数）。
所有数字必须实跑，禁止预估。
