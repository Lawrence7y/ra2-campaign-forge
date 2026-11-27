# R168-EXEC-1 · 独立复算：.text 线性起点数 / 65 个重对齐点 / 引用型跳转表覆盖数

只读任务。工作目录 /home/t628/projects/ra2-campaign-forge 。目标文件 ra2bench/gamemd.exe（4,825,360 B，sha256 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476）。

## 必须遵守
1. 严禁对整段 .text（约 4 MB）开 detail=True 一次性 disasm。只用 capstone 的 disasm_lite，按 64 KB 分块流式迭代，并在解不出指令时只前进 1 字节。
2. 每条命令必须一次输出全部证据，禁止把一个事实拆成多次单点命令。
3. 所有数字必须实测，禁止引用任何现成 JSON 里的数字；禁止读取 _r167 与 _r168 目录下的任何文件。
4. 把脚本与结果 JSON 写到 _r168_exec/ 目录，脚本自带正控与负控断言。

## 要复算的四件事
第一件：.text 的 VirtualAddress=0x1000、VirtualSize=0x3df38d、ImageBase 从 PE 读。用 disasm_lite 从 .text 起点线性扫描到 VirtualSize 末尾，统计「指令起始地址」的个数，同时统计「解不出指令、只能前进 1 字节」的位置个数。给出两个数。

第二件：把扫描上界改成 SizeOfRawData 再跑一次，给出起点数，并回答两个数之差是否全部落在 VirtualSize 之后。

第三件：用代码驱动法找跳转表。扫三种形态的字节模式，都要求命中点在 .text 内：
  a) ff 24 <modrm 为 0x8d/0x85/0x95/0x9d/0xa5/0xb5/0xbd 之一> 后跟 4 字节小端 disp32 —— 即 jmp dword ptr [reg*4+disp32]
  b) ff 14 <同上 modrm> 后跟 4 字节 disp32 —— 即 call 同形
  c) 8b <modrm 为 0x04/0x0c/0x14/0x1c/0x24/0x2c/0x34/0x3c 之一> 8d 后跟 4 字节 disp32 —— 即 mov reg,[reg*4+disp32]
对每个 disp32，从该地址起按 4 字节步进延展，只要读到的 dword 仍是 .text 内地址就继续。延展到 2 条及以上就记作一张表。给出：站点总数、表张数（按 disp32 去重）、以及第一件里得到的「前进 1 字节」位置中有多少落在这类表的字节区间内。

第四件：把第三件里所有表的所有槽值取出来，统计其中有多少个恰好等于第一件得到的「指令起始地址」集合的成员。给出比例。

## 正控与负控（必须都跑，都要打印 PASS 或 FAIL）
正控一：把 ff 24 8d 形态扫到的站点里，找一个 disp32 等于 0x71f9e0 的站点，打印它的地址，并确认从 0x71f9e0 延展出 2 条槽值。
正控二：找一个 disp32 等于 0x79342c 的站点并打印。
负控一：随机取 500 个 .text 内地址当表首做同样延展，统计「延展到 2 条及以上」的比例，应低于 5%。
负控二：把每张表的表首加 1 字节再延展，前 300 张里仍能延展到 2 条及以上的个数应不超过 5。
负控三：扫 ff 15（call dword ptr [disp32]）的 disp32，统计这些目标所在的节名分布，用来说明「连续函数指针成串」不是跳转表的证据。

## 交付格式
最后用一条命令打印一个 JSON，字段为 starts_vsz、starts_raw、resync_count、site_total、tables_ge2、holes_in_tables、slot_total、slot_is_start、断言列表、fail 计数。并在正文里用中文逐条写出你实测到的数字，与 PASS 或 FAIL 结论。
