# W107 PROGRESS（CellClass 字段布局，硬时限 40min）

- 20:46 开卡。读 R10_FACTS.md ✅（自建库、禁 Hy4、禁改 ra2youli、表达纪律已确认）
- 20:47 建目录 `_ghidra` / `ghidra_scripts` / `EVIDENCE`；验证 gamemd.exe 与 analyzeHeadless.bat 存在
- 20:47 后台启动自建库导入分析（job pwsh-a81edf430abd4122）
- 20:48 写 CellFields.java（反汇编扫描 + 反编译溯源 + 合并表三通道）
- 20:52 库就绪（241s 分析成功）；run1：扫描 169 个 +0xE4 函数，但合并表空 → 独立复现器定位两 bug（参数种子 + OBJ 标签被链步进覆盖）
- 21:05 修复（签名行解析种子 + var[idx]/(*var+d) 访问形态）；run2 成功：20 偏移入表，maxEnd=0x144，C 组排除 50 函数
- 21:18 Lead RTTI 补充：CellClass vtable=0x7E4EC0/C8/D0/EEC；字节搜索得 4 个 VT 写入点（VA 修正后 0x47B38C/47BB92/47BD8C/483A4B），±160B 无 push 0x148
- 21:20 pass1only 补 VA 级例句（access_dump.tsv，137 stride 站点）
- 21:26 交付 CELL_STRUCT.md / UNKNOWNS.md / DISAGREE.md / EVIDENCE\*（DebugSig.java 按一卡一脚本规矩删除）

