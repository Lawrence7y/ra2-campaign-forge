# 卡 R196 执行 A（hy4）：RTTI 结构的**第三独立轴**取证 —— 从 COL 侧反查，而非从 vtable 侧正查

## 角色与边界
执行类。只允许写 _r196/exec_a/ 目录下的文件，不得修改任何其他文件。不得运行 gamemd.exe。
全部静态取证。必须一条命令输出全部证据（单脚本一次跑完，禁止逐条试探）。
OOM 红线：禁止对整段 .text 开 detail=True 的 md.disasm；本卡主要做数据段结构解析，不需要反汇编。
PE 映射直接用 _r185/pe185.py：P.RAW（整个文件字节）/ P.B（段字典，键名如 '.text' '.rdata' '.data'，每项有 lo/hi_file/rawptr/rawsize）/ P.dw(va) 读 4 字节小端 / P.where(va) 返回段名 / P.cstr(va,n) 读 C 串。
镜像基址 0x400000。

## 已复核前置（可直接用，不要重推）
P1 一个 CompleteObjectLocator（下称 COL）是 .rdata/.data 里的 5 个 dword 结构，
   字段语义（**外形由本卡独立验证，不要照抄**）：+0 signature、+4 一个偏移、+8 一个偏移、+12 指向 TypeDescriptor 的指针、+16 指向 ClassHierarchyDescriptor 的指针。
P2 TypeDescriptor 在 .data，布局：+0 指向 .rdata 某处、+4 == 0、+8 起是 C 串 .?AV...@@ 或 .?AU...@@。
P3 主会话用「vtable 前 4 字节 == COL 地址」这一条链得到 1214 张 vtable / 1214 个 COL / 954 个不同 ClassHierarchyDescriptor。

## 你要独立回答的五问（只要这五问）
Q1 【COL 侧反查】不借助任何 vtable，只在 .rdata + .data 上按结构外形穷举全部 COL 候选：
   +0 取值在 {0,1,2} 内、+8 == 0、+12 指向 .data 且该处 +4 == 0 且 +8 是 .?A 开头的 C 串、
   +16 指向 .rdata 或 .data 且该处 +8 是一个正整数 n（1..400）、+12 是一个数组指针。
   给出候选总数，与 1214 比对。差集元素（多出或缺少）逐个给出地址与失败原因。
Q2 【偏移字段语义】对 Q1 得到的全部 COL，统计 +4 这个字段的取值分布（给每个值 -> 张数，按张数降序）。
   主会话实测分布是 {0 有 954 张, 21784 有 3, 12 有 78, 8 有 78, 4 有 91, 1728 有 1, 24 有 6, 44 有 1, 40 有 1, 36 有 1}。
   请独立复算这份分布。并回答：21784 / 1728 这三个+一个可疑值对应的 COL 地址、其 TypeDescriptor 名字、
   以及它们是否也能通过「vtable 前 4 字节 == 该 COL」这一条轴验证。若不能，明确写「仅 COL 侧成立」。
Q3 【CHD 侧覆盖】对 Q1 的每个 COL，取其 +16 指向的 ClassHierarchyDescriptor，
   统计不同 CHD 的个数（主会话实测 954），以及每个 CHD 的 +8 字段（该链的 BaseClassArray 长度 n）分布。
Q4 【ncb 字段】BaseClassArray 是一个 dword 指针数组，元素指向 24 字节的 BaseClassDescriptor。
   对该结构：+0 指向 TypeDescriptor、+4 是一个非负整数 c、+8 是一个整数、+12 恒 -1、+16 恒 0、+20 位集。
   请独立统计 c 的取值分布（c -> 出现次数），以及 c 与「该 CHD 的 n」的关系：
   给 (c == n-1) 的命中数 / 总数、(c == n-1-j) 的命中数 / 总数（j 为数组下标，0-based）。
   注意：主会话实测数组内相邻元素的地址差是 -24（递减），请独立确认方向。
Q5 【同名不同址】统计 BaseClassDescriptor 的 +0 指向的 TypeDescriptor 里，名字是 C 串 "ss violation - no RTTI data!" 的记录：
   不同 TypeDescriptor 地址数、出现在 BaseClassArray 里的位置数。

## 三条反控（必须给数）
R1 把 Q1 的 +0 取值域从 {0,1,2} 放宽到 {0..5}，候选总数变成多少（说明该判据的敏感度）。
R2 把 Q1 的「+16 的 +8 是正整数 n」去掉，候选总数变成多少。
R3 把 Q4 的指针数组当成「内联 24 字节元素数组」（即直接读 arr+24*j 当结构起点），
   c 的分布变成什么（必须给数并说明为何这是错的判据）。

## 输出与预算
产物 _r196/exec_a/colaxis.json 与 _r196/exec_a/colaxis.txt，脚本自身打印 PASS/FAIL 断言，断言数 >= 10。
预算 12 分钟。明确区分「实测成立（给数）」「实测不成立（给数）」「没测（给原因）」。严禁预估任何数字。
