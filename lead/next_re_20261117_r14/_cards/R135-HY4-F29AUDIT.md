# R135-HY4 · 跨家族审计：deepseek 的 F29 字节复算是否可信（只读）

## 背景
同轮 deepseek（work/cn:deepseek-v4.1-flash）做了一份 F29 数字的独立字节复算，报告在
/home/t628/projects/ra2-campaign-forge/_r135/sub_deepseek/REPORT.md（连同同目录 .py 与 .log）。
F29 原文在
/home/t628/projects/ra2-campaign-forge/lead/next_re_20261117_r14/R17_R104_FACTINDEX_V532/FACT_INDEX.tsv
第 2 行（表头 5 列：fact_id / statement / grade / evidence_paths / limitations）。
二进制 = /home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe。
你的任务是**审计它**，不是重做一遍。审计的意思：找出它的数字或口径里任何一处站不住的地方。

## 审计项（逐项给「同意 / 不同意 / 无法判定」+ 依据）
A1 它说 TClassFactory 名字串命中 77、不同 X 77、每个 X 只出现 1 次、全在 .data。
   你自己用一条不同的正则独立数一遍（不要用它那条），比较三组数。
A2 它说 8 字节桩序列 B8 01 00 00 00 C2 04 00 全文件出现 40 次、全在 .text、0 次在数据节。
   **这条要小心**：序列里有 0x00 字节，跨节边界与「子串重叠」都可能让计数变形。
   你独立数一遍，并明确写出你如何处理「同一段字节既算 .text 又跨到下一节」这件事。
A3 它说 0x6C2AC0 与 0x6C51C0 两处 17 字节逐字节相同，序列
   8B44240483C00450FF15C8117E00C20400。你独立定位这两个 VA、独立读 17 字节、独立比较。
   注意 VA 到文件偏移的换算：ImageBase 0x400000，且 .text 的 raw 与 RVA 相等这一事实
   只对 .text/.rdata/.data 成立，对 .rsrc/.detour 不成立（你若踩到这个坑要写出来）。
A4 它说 0x7E11C8 是 KERNEL32.dll 的 InterlockedIncrement，Hint=432、FirstThunk idx=62。
   它同时承认 idx=62 这个「62」的计数起点需要限定口径。你独立手工遍历导入描述符
   （IMAGE_IMPORT_DESCRIPTOR / ILT / IAT / IMAGE_IMPORT_BY_NAME），核实：该槽属于哪个 DLL、
   指向哪个名字、Hint 多少、以及这个「62」按什么起点数才成立；若按另一种常见起点数会是多少。
A5 它说导入共 372 = 按名 339 + 按序数 33；ILT 372 条全在 .detour；IAT 371 条在 .rdata、
   1 条在 .detour（xyr.dll）。你独立复算，并对「节边界归属」写出你用的判据。
A6 它的报告第 6 节自己列了 3 条「措辞需收紧」。判断这 3 条是否成立，以及是否有它**没列出来**
   的口径问题（尤其：它把 40 次桩的出现与 63/77 的关系怎么说的，F29 原文又是怎么说的，
   两者是否等价）。

## 硬约束
- 绝对只读。禁止修改/创建/删除 lead/ 与 _r135/ 下任何文件；临时文件写 /tmp/r135hy4b/。
- **禁止 reuse 它的脚本**：A1..A5 你都要自己写。可以在报告里对照它的输出，但计算过程独立。
- 每条结论必须附你实跑的输出原文。跑不了写「未跑，原因」。
- 交付：/tmp/r135hy4b/REPORT.md，并在最后一次回复里用不超过 1200 字给出 A1..A6 的判决摘要，
  每项一行「项 / 判决 / 一句话依据」。
