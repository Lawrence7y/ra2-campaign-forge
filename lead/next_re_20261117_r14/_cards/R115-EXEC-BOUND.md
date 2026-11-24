# R115-EXEC-BOUND —— 执行员（deepseek）：独立复算「接口方法表槽数的结构上界 S 尺」

## 身份与边界

执行员。**独立复算**，不得复用主会话结论当输入。只读盘、只在 _r115/ 下写新文件、不改任何既有文件。
禁止使用反引号。禁止整段 .text 开 detail=True；一律 disasm_lite 或 64KB 分块。
所有命令带 timeout；收口前确认无孤儿进程。

## 工作目录

/home/t628/projects/ra2-campaign-forge

## 已知输入（可直接读，但结论必须自己算）

- ra2bench/gamemd.exe（PE，sha 见 _r113/census.pkl 的 sha 字段）
- _r113/r113_lib.py（PE/RTTI/HB/COL 普查底座，只读复用）
- _r113/census.pkl（1214 个 vtable 的 V2C / T / E / B / colptr / cols）
- _r113/r113c_slots.json（R113 链 H 的接口子对象表；注意 detail 字段被截断到每接口 80 行）
- _r115/iface_subobj_full.json（未截断的 260 个接口子对象，主会话重建）

## 要你独立回答的四个问题

1. MSVC 的 vtable 布局里，vtable 起点前 4 字节是 COL 指针。据此定义一把**新尺子**：
   从 vtable 起点 v 沿 .rdata 线往后扫，第一个「其值本身是一个合法 COL 起点」的 dword 下标记为 S。
   请**自己实现** valid_col 与这把尺子（不要 import 主会话的 _r115/r115_lib.py），
   算出全镜像 S，并报告：S 有定义的数量、无定义的数量与地址、无定义的原因。

2. 对 260 个接口子对象 vtable（_r115/iface_subobj_full.json 的并集），
   逐一比较 T（census.pkl 的 T）、E（census.pkl 的 E）、S 三把尺子。
   报告：三者逐点相等是否成立？各自是否恒定（对每个接口）？给出每个接口的取值集合。

3. 反控（**必须每条都跑，并报告是否真的失败**）：
   (a) 把 S 的边界后移一格（S+1）当槽数，该 dword 是否落在 .text 且是已知指令起点？
   (b) 把 S 的边界前移一格（S-1）当槽数，该 dword 是否仍落在 .text？
   (c) 把 S 的判据从「值 ∈ 合法 COL」放宽成「值 ∈ .rdata 区间」，全镜像有多少个 vtable 被改判？
   (d) 全镜像 T==S 的比例；与接口子对象上的比例对照，判断「三尺同值」是不是平凡性质。

4. 独立判断：这些数字能否支撑命题
   「接口方法表的槽数是接口自身的属性，而不是承接类的属性」？
   请明确写出你认为**成立**的部分与**不能支撑**的部分。

## 输出

- 脚本：_r115/x115exec_bound.py（自己写，带断言，失败即非零退出）
- 结果：_r115/x115exec_bound.json
- 回报里逐条给：问题 1/2/3/4 的实测数字（不要只说 PASS），以及你与主会话数字的**差异**（若有）。
- 如果你认为主会话的判据有缺陷，直接写出来，不要客气。
