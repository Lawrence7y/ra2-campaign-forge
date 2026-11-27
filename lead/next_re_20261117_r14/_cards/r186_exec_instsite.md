# 卡 R186-EXEC：独立复算「vtable 装点位移 == COL.mdisp」六个数字

角色：执行员（只读，不改任何四件套）。工作目录 /home/t628/projects/ra2-campaign-forge。

## 背景（一句话）
gamemd.exe 里每个类的多张 vtable 在构造器中被装到对象的不同偏移上，偏移量等于该 vtable 的
COL（CompleteObjectLocator）里的 mdisp 字段。主会话已用一个脚本得出数字，你要用你自己的脚本复现。

## 必须一次命令跑完，输出六个数（禁止预估，全部由字节算出）

1) 全镜像 vtable 数 N1
   枚举法：在 .rdata 与 .data 里，位置 V 满足 dword[V] 落在 .text 文件区间（0x401000..0x7E1000）
   且 dword[V-4] 是一个合法 COL 起点。COL 起点定义：该地址起 5 个 dword 满足
   d0 in (0,1) 且 d2 == 0 且 d3 指向 .data 且 where(d3+8) 的串形如 .?AV...@@ 或 .?AU...@@ 且 d4 指向 .rdata。
   （.text 上界取**文件上界** 0x7E1000，不是 vsize 的 0x7E038D；上界取错会少算。）

2) 全镜像 COL 数 N2（同上枚举法，去重后计数）

3) .text 中含「某个 vtable 绝对地址作为 imm32」的指令条数 N3
   做法：用 capstone 32 位线性反汇编 .text 全段，**必须用 md.disasm_lite() 或 <=64KB 分块**，
   禁止对 4MB 整段开 detail=True 一次性 disasm（会 OOM）。对每条指令在其字节范围内
   按 4 字节对齐滑动窗口取 dword，命中 vtable 集合即记 1 条。

4) 上述指令中属于 store 形态（mov dword ptr [基址+位移], imm32）的条数 N4
   以及对其中「基址寄存器不是 esp、并且不是 ebp、并且没有索引寄存器」的子集 N5，
   在 N5 上统计「位移 == 该 vtable 的 COL.mdisp」的条数 N6。

## 输出格式（一条命令输出全部）
打印以下六行，每行形如 名字 = 数字：
N1 = ...
N2 = ...
N3 = ...
N4 = ...
N5 = ...
N6 = ...
并额外打印一行 N6/N5 的百分比，以及一行「位移 != mdisp 的那批里，位移取值 top10」。
再打印一行：这些不等条目按 vtable 的类名（TD 名的 .?A 前缀后缀去掉）分组的 top10 与条数。

## 硬要求
- 脚本落 /home/t628/projects/ra2-campaign-forge/_r186/exec_<你的编号>_census.py，输出 JSON 同目录。
- 必须带一条反控：把位移换成 位移+1 再判一次，N6 必须变成 0（证明判据真的读了位移字节）。
- 数字必须实测；与你预期不符就如实打印，不要调整判据去凑数。
- 不许写任何带反引号的字符串进卡面或输出（本卡无）。
- 报告里逐项写出：六个数字、反控结果、top10 位移、top10 类名分组。
