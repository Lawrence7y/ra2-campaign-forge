# 卡 R196 执行 B（hy4）：vtable 侧的**装点与引用面**独立复核 —— 1214 与 954 两个基数的双向交叉

## 角色与边界
执行类。只允许写 _r196/exec_b/ 目录下的文件，不得修改任何其他文件。不得运行 gamemd.exe。
全部静态取证。必须一条命令输出全部证据（单脚本一次跑完）。
OOM 红线：禁止对整段 .text 开 detail=True 的 md.disasm；全段线性扫描只用 md.disasm_lite()
或 <= 64KB 分块流式迭代并及时释放，仅对少数命中地址单独开 detail=True。后台命令必须带 timeout。
PE 映射用 _r185/pe185.py：P.RAW / P.B / P.dw(va) / P.where(va) / P.cstr(va,n) / P.r2o(va)。
capstone 已装：capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)。.text 段：P.B['.text']，lo=虚拟起点，rawptr=文件偏移，rawsize=文件内长度。镜像基址 0x400000。

## 已复核前置（不要重推）
P1 vtable 判据：一个 dword 槽位 v 若满足 (a) v 落在 .text 内、(b) v 前一个 dword 是一个 COL 地址，
   则认为 v 是该 COL 的 vtable 起点。
P2 COL 判据：.rdata/.data 里 5 个 dword：+0 在 {0,1,2}、+8 == 0、+12 指 .data 且 +4==0 且 +8 是 .?A 串、+16 指 .data 且 +8 是正整数 n、+12 是数组指针。
P3 主会话实测：1214 张 vtable、1214 个 COL、954 个不同 CHD、BaseClassDescriptor 总数 2615。

## 你要独立回答的六问
Q1 用 P1+P2 独立复算：vtable 张数、COL 个数、不同 CHD 个数。与 1214/1214/954 比对，差集逐个给地址。
Q2 【槽数分布】对每张 vtable，数它有多少个连续的 .text 指针槽（遇到第一个非 .text 值即停，上限 512）。
   给出槽数直方图（槽数 -> 张数），以及槽数总和。分别对「+4 字段 == 0 的 954 张」与「+4 字段 != 0 的 260 张」各给一份。
Q3 【.text 直接引用面】分块 + 块内逐字节重同步线性扫描整个 .text：
   统计全部 mov r32, imm32 形态里立即数等于任一 vtable 地址的指令条数；再统计立即数等于任一 COL 地址的条数；
   再统计立即数等于任一 ClassHierarchyDescriptor 地址的条数。三组各给「命中指令数 / 涉及不同目标数 / 涉及不同目标中零命中的个数」。
   请报告你实际达成的 .text 字节覆盖率（覆盖字节 / 段 rawsize），若低于 99.5% 必须说明原因。
Q4 【vtable 前 4 字节】对全部 1214 张 vtable，读「vtable 起点 - 4」这个 dword，统计它是否恰好回指该 vtable 的 COL 地址（应为 1214/1214）。
Q5 【跨段污染反控】统计这 1214 个 vtable 地址作为 4 字节序列在整个文件里的出现次数（按段分别给：.text/.rdata/.data/.rsrc/其他）。
   .text 里出现 0 次才说明「装点是数据不是代码常量」这一结论成立；若 .text 里出现非 0，逐条给地址。
Q6 【954 vs 1214 的判据】只用「COL 的 +4 字段是否 == 0」去划分 954/260 两组。
   再给一份交叉表：Q2 的槽数 × 该分组，用以说明这两组在槽数上是否有系统性差异（给两组的中位数与均值）。

## 三条反控（必须给数）
R1 把 P1 判据里的「v 前一个 dword 是 COL」放宽成「v 前 8 字节内任意位置是 COL」，vtable 张数变成多少。
R2 把 Q3 的扫描口径从「分块 + 块内重同步」换成「单次连续 disasm_lite」，覆盖率和三组命中数各变成多少。
R3 把 Q6 的划分改用「COL 的 +16 指向的 CHD 的 +8 字段（n）是否 >= 2」，两组张数各是多少（说明为何这不是 954/260 的成因）。

## 输出与预算
产物 _r196/exec_b/vtcross.json 与 _r196/exec_b/vtcross.txt，脚本自身打印 PASS/FAIL 断言，断言数 >= 10。
预算 12 分钟。明确区分「实测成立（给数）」「实测不成立（给数）」「没测（给原因）」。严禁预估任何数字。
