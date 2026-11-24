# UNKNOWNS.md — 本卡遗留 `[未证]`

1. **逐项精确语义（3,944 项）**：本卡只裁"是入口 + 类别"；每项具体初始化了哪个全局/属于哪个类，属 P1 工作，未定名（派卡明确要求不逐一定名）。`coverage_delta.tsv` 全部 grade=`[未证]` 即反映此。
2. **为什么恰好 2 条在 atlas**：已证机制（0/3,944 是 E8/E9 直接目标、唯一调用是 `call eax` 寄存器间接、FuncAtlas.java 只收 Ghidra `fm.getFunctions`），但 Ghidra 为何对 `00412870`/`006A4DC0` 建了函数而对其余 3,942 个没建，需跑 Ghidra 才能确认具体启发式（本卡未用 Ghidra）。两条在 coverage 中本来就是 `[未证]` 兜底条目（S05 猜测 / S22 无信号）。
3. **另外 3 张 `_initterm` 小表的 8 个非空 FUNC**：已枚举（EVIDENCE/t1_tables.txt），未并入 delta（越界）；是否需要收编待 Lead 决定。
4. **口径 A/B 的最终选取**：本卡只给依据与数字，Lead/用户定（CALIBER.md）。在定案前任何"全镜像 X%"不应重算。
5. **前驱指令级 TERM 精确值**：字节级 3,928、指令级≈3,943、审计 3,941，差 2 来自首字节跳转 thunk 的前驱口径；不影响 FUNC 结论（DISAGREE D2）。
6. **未使用 Ghidra**：本卡全程 Python+capstone(skipdata=True)+pefile 独立复算，未复制/运行 Ghidra 副本（无需要）。
