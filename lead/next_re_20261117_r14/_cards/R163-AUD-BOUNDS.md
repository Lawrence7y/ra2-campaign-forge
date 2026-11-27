# R163-AUD · 跨家族只读复核：bounds 生成规则复原 + 86.19% 口径滑移

你是跨家族审计员（deepseek，只读）。不要执行任何写操作，不要改任何文件。
工作根目录：/home/t628/projects/ra2-campaign-forge

## 一 · 被审对象（主会话 R163 的两条结论）

结论甲 · bounds 的生成规则：
  gamemd.exe 的 .text（VA 0x401000，SizeOfRawData 4,063,232，VirtualSize 4,060,045，
  VirtualSize 尾界 0x7E038D，raw 尾界 0x7E1000）上，
  a2_sites.json 的 bounds 段（1,392,592 条 VA）**逐条等于**
  capstone skipdata=True 的 disasm_lite 起点集中「地址 < 0x7E038D」的那一部分。
  据此，R162 记的「bounds = 指令起始集 + 65 条指令内位移」中那 65 条**不是指令内位移**，
  而是「用 plain 反汇编起点当基准」这一基准选错造成的假遗留。

结论乙 · F24 正文 86.19% 的口径滑移：
  R95 REPORT.md §5.3 那段（4,743 份文本 EVIDENCE、961 份供行、192,341/1,392,592=13.81%、
  其余 1,200,251 条 86.19%「盘上没有任何字节与之对应」）测的是**盘上语料覆盖率**，
  而 F24 正文把「盘上语料没覆盖到」写成了「二进制里没有字节」。
  两者是不同命题，故 R136 用二进制判据测得 99.992% 与 86.19% 不构成矛盾。
  另：R95 依赖的 4,743 份文本 EVIDENCE 与两个生成器脚本（q4_covering.py /
  q4_covering_verify.py）**现盘已全部不存在**，EVIDENCE 目录仅剩 5 个、共 5 个文件，
  含文本 disasm 行的文件 0 个 ⇒ 192,341 与 961 这两个数**当前不可重算**。

## 二 · 请你用一条命令完成全部取证

只允许读。可用 python3（capstone、pefile 已装）、rg、sha256sum、wc。
**严禁**对整段 .text 用 md.disasm(detail=True)；用 disasm_lite。
**严禁**递归跟随符号链接（目录里有自指符号链接环，跟随会跑飞）。
**严禁**起超过 200MB 内存的进程。

请把下面这些问题的答案一次输出：

1. a2_sites.json 的 bounds 条数、最小/最大 VA、是否严格升序、是否零重复。
2. .text 的 VirtualAddress / VirtualSize / SizeOfRawData / PointerToRawData，以及 ImageBase。
3. 用 capstone skipdata=True 对 .text 做一次 disasm_lite，得到起点总数 N2；
   用 skipdata 关（plain，单次不重对齐）得到 N1。N1、N2 各是多少？
4. bounds 是否 ⊆ skipdata 起点集？差集两边各多少条？
5. skipdata 起点集中「地址 >= 0x7E038D」的有多少条、范围是多少？
6. 「bounds 条数 + 上述尾段条数」是否等于 N2？
7. grep R95 REPORT.md 里这几串是否逐字存在：
   192,341 / 1,392,592 = 13.81% ；961 份 ；1,200,251 条（86.19%）只以地址形式存在
8. 现在盘上名为 EVIDENCE 的目录有几个（去重后的 realpath）、其中文件共几个；
   这些文件里有几个含「8 位 hex 地址 + hex 字节 + 小写助记符」形态的行？
9. R17_R95_T1_A2SITES 目录现在还剩哪些条目？q4_covering.py 是否存在？
10. _r131/_audit_deepseek/a2_callsites.py 里是否出现 skipdata 字样？它扫的 TARGETS 是哪两个地址？

## 三 · 输出格式

请按 1..10 逐条给「值 + 你用的命令/代码要点」，最后一段写：
- 你对结论甲、结论乙各判 成立 / 不成立 / 表述需改，并说明判据。
- 你发现的任何与上面两条结论冲突的实测事实（这一项最重要，请务必单列）。

不要写任何文件。不要在回答里使用反引号包裹长代码块以外的内容。
