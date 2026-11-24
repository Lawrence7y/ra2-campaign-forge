# S22-CENSUS PROGRESS

- 口径：coverage.tsv subsystem==S22 ∩ function_atlas.tsv entry；entry 统一大小写；atlas size 列按十进制读。
- 总体：S22 全量 10170 行；S22∩atlas **4851** 行（盘上复算一致）；coverage 全表 18431 行；atlas 12916 行。
- 二进制：gamemd.exe 4825360 B，SHA-256 `73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476`；ImageBase 0x400000；只读打开。

实际扫过的通道（A4 不是假否定）：
1. A1：`.rdata` 对齐 dword 找 COL 前缀，COL=sig0, +0xC->TD, +0x10 CHD；从 vt=pos+4 逐槽走到非 `.text`/下一 COL 边界；得 1214 表 / 14044 槽；再用槽值集合查 entry。未用 atlas entry+size 反推虚表。
2. A1 防坑：TD 名取 `TD+8` 内联 `.?AV/.?AU ... @@`；从不把 `TD+8` 当指针；`COL+8` 只作 CD 偏移，不用于取名。
3. A2：对每条 S22∩atlas 行按 atlas size 取体，capstone skipdata=True 逐指令判 `mov [base/index],imm` 且 imm∈1214 个 vtable 起点。
4. A3：同一指令流逐操作数查 IMM∈1214 COL ∪ 988 TD；另查 MEM.disp 与体内 raw dword 作等价形留痕。
5. 双通道：A1 完全不依赖 atlas entry+size；A2/A3 依赖 entry+size 但由反汇编证据逐条留痕。
6. 区间空洞 / 边界：未用 atlas 边界推 A1；A2仅按 entry+size 体判定；006B6EA0 的 vptr 写在 0x6B6F5F（距入口 0x70 < size 241）体内命中，006B6C90 按字面 A1/A2/A3 未命中记 A4。
7. 不存在判定：A4 = A1/A2/A3 全不命中，且等价形（寄存器中介 VT 写、disp COL/TD、raw dword）计数写入证据。
8. 结果：A1=1744，A2=260，A3=1，A4=2846；ANCHORED=2005 (41.33%)，UNANCHORED=2846 (58.67%)。
9. 写域：仅 `S22_CENSUS/`；未写 coverage / PANEL / 其它卡目录；未 git commit。
