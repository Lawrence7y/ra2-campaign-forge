# R140-F01-RTTI-BLIND · 独立盲测复算 MSVC RTTI 三张表的四个计数

## 角色与边界
你是执行员。只做测量与报告，不改任何台账、看板、门禁文件。
工作根目录：/home/t628/projects/ra2-campaign-forge
目标文件：ra2bench/gamemd.exe（4,825,360 B，sha256 前 8 位 73201cc0）

## 纪律
1. 一次取证：把下面 A1..A5 五项写进一个脚本，一条命令跑完，输出 JSON + 控制台表格。禁止把一项拆成多次单点命令。
2. 内存红线：禁止对整段 .text 开 capstone detail=True；本卡只做纯字节/dword 扫描，不需要反汇编。
3. 脚本必须带 timeout，产物写 _r140/sub/ 目录，单文件不要超过 20 MB。
4. 不要读 _r140/r140a*.py r140b*.py r140c*.py r140d*.py r140e*.py r140f*.py r140g*.py —— 那些是主会话的实现，你要独立写，避免抄同一份错误。
5. 你的结论只写你实测到的数，不要猜主会话想要什么。

## 任务（全部只读 PE 字节）
用 pefile 取节表（ImageBase 0x400000）。注意：节表里的 VirtualAddress 是 RVA，不是绝对 VA；绝对 VA = ImageBase + RVA。落盘字节区间是 PointerToRawData + SizeOfRawData；虚拟尾部可能大于落盘部分，读不到就是读不到，不要当 0。

A1 · 名字串与 TypeDescriptor
在 .data 与 .rdata 的落盘字节里正则搜 .?AV 或 .?AU 开头、@@ 结尾的可打印串。对每个串起点 S 检验：dword[S-8] 是否落在 .data/.rdata 的 RVA 范围内、dword[S-4] 是否为 0。满足者记一个 TypeDescriptor，其 VA = S-8。报三个数：串总数、.?AV 个数、.?AU 个数、通过检验的 TD 数。

A2 · COL
在 .data 与 .rdata 落盘字节里，每个 4 字节对齐位置读一个 dword；若该 dword 的值恰等于某个 TD 的 VA，则候选 COL = 该位置 - 12。对每个候选检验 dword[COL+0]==0 且 dword[COL+12]==该 TD VA。报：TD 指针引用总数、通过检验的 COL 数、去重后的 COL 数、被 dword[+0] 非零否掉的引用数。

A3 · 虚表
再扫一遍 .data/.rdata 的 dword；若某 dword 值等于某个 COL 的 VA，则候选虚表 vt = 该位置 + 4，检验 dword[vt-4]==该 COL VA。报：虚表引用次数、去重虚表数、被至少一张虚表指回的 distinct COL 数、以及没有被任何虚表指回的 COL 的 VA 与类名列表。

A4 · 两个附属数
(1) dword[COL+4]==0 的 COL 数（这是 mdisp 口径）。
(2) 没有任何 COL 指向的 TD 数。
(3) 按类名后缀把 COL 对应类分成三族（Locomotion / TypeClass / Other 之外的类名按末段判断），报每族的 COL 数与 distinct 类数。

A5 · 检验一个可疑口径
报这三个数，用于判断某个历史数字的来源：
(1) dword[COL+4] <= 0x1000 的 COL 数，以及其中被虚表指回的个数；
(2) 该过滤掉的那些 COL 的 VA、dword[COL+4] 的十六进制值、类名；
(3) dword[COL+4] 的全部取值直方图。

## 交付
把结果写入 _r140/sub/REPORT_F01_BLIND.md，包含：脚本路径、一条命令、A1..A5 逐项数值表、以及一句「哪些数我没能测到、为什么」。数字必须来自实跑输出，不得估计。
