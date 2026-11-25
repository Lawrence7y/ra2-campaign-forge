# R135-DS · F29 数字的独立字节复算（只读）

## 定位
本卡在 t628（Linux x86_64）本机执行。二进制 = /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe
（PE32 x86，ImageBase 0x400000，节表：.text RVA 0x1000 raw 0x1000 / .rdata RVA 0x3E1000 raw 0x3E1000 /
.data RVA 0x412000 raw 0x412000 / .rsrc / .detour RVA 0x793000 raw 0x497000）。

被测主张在 FACT_INDEX 第 F29 行，原文见
/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv
（第 2 行 F29，第 2 列 statement，第 5 列 limitations）。先自己读原文再动手，本卡不复述全部措辞。

## 任务：独立复算下面 5 个数字（自己写代码，不许抄 _r95 或 _r109 下的既有脚本；不许 import 它们）
D1 F29 说「77 张 TClassFactory 表」。独立数一遍：全文件里形如 .?AV?$TClassFactory@V<X>@@ 的
   RTTI 类型名字符串有多少个**不同**的 X。给出总数、是否 77、以及你用的正则原文。
D2 F29 说 8 字节桩序列 B8 01 00 00 00 C2 04 00（mov eax,1 / ret 4）
   「全镜像出现 40 次、全在 .text、0 次在数据节」。独立数一遍：全文件出现次数、按节分布。
D3 F29 说 0x6C2AC0 与 0x6C51C0 处的 slot1 目标**17 字节逐字节相同**，序列为
   8B44240483C00450FF15C8117E00C20400。在文件里定位这两个 VA（注意 VA 到文件偏移的换算），
   逐字节打印两处 17 字节并给出 sha256 或逐字节比较结论。
D4 F29 说 0x7E11C8 是导入表里 KERNEL32.dll 的 InterlockedIncrement，Hint=432、FirstThunk idx=62。
   独立遍历导入描述符（不要用 pefile 的高层 get_import_table，手工读 IMAGE_IMPORT_DESCRIPTOR、
   ILT/IAT、IMAGE_IMPORT_BY_NAME），核实 0x7E11C8 这个槽属于哪个 DLL、指向的名字是什么、
   Hint 是多少、在 IAT 数组里的下标是多少。
D5 F29 limitations 说导入共 372 条 = 按名 339 + 按序数 33；ILT 372 条全在 .detour；
   IAT 数组 371 条在 .rdata、1 条在 .detour（xyr.dll）。独立复算这 6 个数字。

## 硬约束
- **只读**。除下面允许的两个输出文件外，不得创建/修改/删除任何文件。
- 允许写：/home/t628/projects/ra2-campaign-forge/_r135/sub_deepseek/ 下的文件，
  以及该目录里的 REPORT.md。禁止写入 ra2bench/ 与 lead/ 下任何路径。
- 不许对整段 .text 开 capstone detail=True（会 OOM）；本卡不需要反汇编，用字节搜索即可。
- 每个数字必须给出「你跑的命令 + 实际输出」，不许只给结论。跑不了就写「未跑，原因」。

## 交付
在 /home/t628/projects/ra2-campaign-forge/_r135/sub_deepseek/REPORT.md 里逐项写 D1..D5：
  主张值 / 你的实测值 / 一致或不一致 / 命令与输出原文。
最后单列一节「分歧」：凡是你实测与被测主张不一致的，写清差在哪里、你更相信哪一个、为什么。
