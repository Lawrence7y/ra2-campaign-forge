# R105 AUDIT 卡 · 3 项 —— 只做独立判断，不要写脚本超过 3 个

被测对象 sha256 = 73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476
（/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe）

工具：/home/t628/projects/ra2-campaign-forge/_r104/vendor 下有 iced_x86 1.22.0，只读引用。

## 待核 3 项（每项给 CONFIRMED / REFUTED / UNVERIFIABLE 之一，并写判据）

### A1
命题：「B1 的 31 个去重宿主，在 iced 线性扫描下全部是 is_invalid 单元起点（31/31）。」
B1 清单：/home/t628/projects/ra2-campaign-forge/_r101/_exec/r101_bc.json 里 class=="B1" 的 host 字段。
注意区分两个集合：线性扫描产出的 ip 集合，与「is_invalid == False」的合法起点集合。
请报：31 个宿主里有几个在 ip 集合里、几个合法、几个 invalid。

### A2
命题：「这 19 张 jmp [reg*4+base] 表的 292 个项值，全部 292 个都是合法（非 invalid）单元起点。」
请自己枚举表和项，报你的表数、项值总数、其中合法起点的个数。
若你的表数或项值总数与 19/292 不同，先报你的数，再说差异来自哪一步的口径。

### A3
命题：「292 个项值里，0 个是任何 call 指令的直接目标（call + NEAR_BRANCH32 的 target）。」
并且：这个 0 不是空判据 —— 请另取 292 个 call 目标做反向，命中率应为 100%。

## 交付
只写这三个文件到 /home/t628/projects/ra2-campaign-forge/_r105/_audit/：
audit105.py、audit105.json、AUDIT105.md
不许写其它目录，不许改真树任何文件。
结论若与命题不符，直接写 REFUTED 并给你的数。
