# R105 EXEC 卡 · 19 张 switch 分派表的 292 个项值定性 —— 独立复算

## 背景（只读，不要改任何真树文件）
被测对象：
- 可执行档 /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
  sha256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
- 脱壳工具：本机已 vendored iced-x86 1.22.0 于 /home/t628/projects/ra2-campaign-forge/_r104/vendor
  用法：sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r104/vendor'); import iced_x86
- 本机没有 objdump 这个名字，真名是 i686-w64-mingw32-objdump（本轮不需要它）

上一轮（R104）的结论：B1 的 41 个「宿主起点两个解码器都解不出」的地址，其宿主 41/41
落在 jmp dword ptr [reg*4+base] 的跳转表体内。R104 自己登记的未取得项是：
「表项值指向的真实函数入口未逐一定性」。
本轮（R105）主会话的结论是：这个提法本身需要校正 —— 这 19 张表是 switch 分派表，
项值是 case 标签（函数内基本块），不是函数入口。主会话给出 292/292 的证据链。

## 你的任务：不复用主会话脚本，独立实现，逐项回答下面 5 个问题

禁止 import / 读取 /home/t628/projects/ra2-campaign-forge/_r105/r105a_tableentries.py
和 _r105/r105a_tableentries.json。请自己从 exe 字节开始写。

Q1 【表枚举】用 iced-x86 线性扫 .text（VirtualSize 取 PE 头真值），收集所有
   「jmp r/m32 且 op0 是 MEMORY、index scale==4、index 寄存器非 NONE、
   displacement 落在 .text 内」的指令，按 displacement 分组。
   对每个 disp 从 disp 起连续读 DWORD，只要读到的值仍在 .text 内就继续，直到第一个
   不在 .text 内的值或读满 512 项；保留项数 >= 2 的表。
   报：表总数、持有指令总数、项值总数。

Q2 【B1 定位】B1 的地址清单在 /home/t628/projects/ra2-campaign-forge/_r101/_exec/r101_bc.json
   的 detail 里，筛选 class == "B1" 的行，取 host 字段（十六进制字符串）。
   报：B1 行数、去重后宿主数、这些宿主落在几张表内（表的 base 去重）、
   这 19 张表合计多少个项值。

Q3 【项值是否合法单元起点】用 iced 线性扫一遍得到每个「单元起点 -> 是否 invalid」。
   报：292 个项值里，是合法单元起点（非 invalid）的有几个。
   注意一个坑：线性扫描会为 invalid 字节也产出一个 ip，所以「在该 ip 集合里」
   不等于「是合法起点」，必须另查 is_invalid。

Q4 【是不是函数入口】三条都测：
   (a) 项值是否 > 该表的持有指令地址（前向）
   (b) 项值是否是任何 call 的直接目标（CALL + op0 NEAR_BRANCH32 的 target 集合）
   (c) 每张表内项值的最大地址 - 持有指令地址（跨度）
   报三个数。

Q5 【反控，必须有】对 292 个随机 .text 地址，问「是否为合法单元起点」的比例是多少
   （跑 200 次取中位）；再从 call 目标集合里随机抽 292 个，问「是否在 call 目标集合里」。
   这两条用来证明主会话的判据 A3b 不是恒 0 的空判据。

## 交付
写 /home/t628/projects/ra2-campaign-forge/_r105/_exec/r105_exec.py（你的脚本，带正反控自测）
和 /home/t628/projects/ra2-campaign-forge/_r105/_exec/r105_exec.json（你的全部数字）
和 /home/t628/projects/ra2-campaign-forge/_r105/_exec/VERDICT105.md（结论 + 与上面 5 问逐问对照）
只写 _r105/_exec/ 下的文件，不许碰其它目录。

## 硬要求
- 每个数字必须自己算出来，不许抄本卡里的任何数字（本卡没给结果，只给方法）。
- 口径必须写清：你算的「表」的定义、每项怎么读、怎么判 invalid。
- 若你的数与主会话的预期不同，直接如实报你的数并说明口径差异在哪，不要迁就。
