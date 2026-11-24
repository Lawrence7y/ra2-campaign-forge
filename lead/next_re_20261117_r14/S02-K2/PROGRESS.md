# S02-K2 · PROGRESS（CRT / SBH / 异常链 · 纯静态，D-35 按 A 不打补丁）

> 卡号 S02-K2｜根 `D:\Project\ra2-campaign-forge`｜目标 `ra2youli\gamemd.exe` SHA-256 `73201CC0…F67476` 全值实测一致｜只写本卡目录 + `_ghidra\S02-K2\`；未改 `ra2youli\`、未注入、未写进程内存、未 git commit。

## T1 靶子清单
- `TARGETS.tsv` = `coverage.tsv(subsystem=S02)` ∩ `function_atlas.tsv` = **327 行**；R14-R14 S 口径 named **37/327=11.31%**（`Class::sub_` 占位 0 条，L=S）；`[已证]` **31/327=9.48%**（盘值/ PANEL）；50% 门槛 = ceil(327/2)=**164**，差 **133** 个 proved。
- 纪律 9 分歧：卡面/HANDOFF 写 proved=30(9.17%)，PANEL+盘上=31(9.48%)；采盘值，见 `DISAGREE.md` D1。

## T2 CRT 定名（真依据，基线已测）
- 依据源：`YRpp\CRT.h`（外部符号表 `JMP_STD(0x…)`，非形态匹配）+ 字节体双通道；基线 `EVIDENCE/BASELINE.txt`：随机 31 个 sub_ 命中 YRpp 标记均值 0.128（真实 31）⇒ 地址特异。
- **靶内新增 1 名**：`0x7C9442`→`CRT::_nh_malloc` `[静态推断]`（被 `CRT::malloc@0x7C9430` + `CRT::_new@0x7C8E17` 两具名锚点调用；字节 `cmp [esp+4],-0x20`+重试环）。
- **跨子系统归位 3 条** `[已证]`：`0x7C8B48 qsort` / `0x7C8E25 bsearch`（原 S19 弱邻居票）/ `0x7C5F00 _ftol`（原 S06，台账§4 1974 调用者）—— YRpp 显式地址 + 字节体。
- **不可定 289 条**：YRpp 31 个 CRT 名在靶内已全部具名；0x77–0x7B 段 168 个无符号；0x7C/0x7D 段 25 个仅知 CRT 内部辅助、无标准名 ⇒ 保持 sub_，见 `CRT_NAMES.md` E / `UNKNOWNS.md` U1。
- `vfprintf@0x7CB302`（YRpp 具名）不在 atlas/coverage，按"不在 atlas 区间≠是函数"不新增行，记 U2。

## T3 SBH / 内存池
- 确认 MSVC 小内存块堆：`HeapCreate@0x7CF6C2`→句柄 `[0xB78B9C]`；`HeapAlloc(0x140)@0x7CF78C`→描述符基 `[0xB78B98]`；`[0xB78B84]=0x10`（16B 粒度）；region 1MB/提交 16KB（`0x7CF70F/714` VirtualAlloc）；表项 stride 0x14；region stride 0x204；位图 `+0x44` 32 档。
- `[0xB782C4]`（malloc 句柄）全 `.text` 0 写点 ⇒ 语义仅 `[静态推断]`（U3）。字段表 6 行 + 尺寸双向核对见 `LAYOUT.md` §1。
- §981 槽契约：SBH 为 C 结构无 vtable，不假定槽 12。

## T4 异常 / 崩溃守卫链
- 安装点 `0x6BE07F push 0x6BB990` → `0x6BE084 call [0x7E1144]=SetUnhandledExceptionFilter`。handler `0x6BB990` 为尾跳桩 `…jmp 0x4C8FE0`（atlas gap，四项入口证据满足）。
- **except.txt 写入点找到**：`0x4C8FE0` 内 `0x4C901C push 0x8221F8("except.txt")` → `0x4C9021 call [0x7E11BC]=CreateFileA` → `0x4C9047 call [0x7E11A0]=WriteFile` → `0x4C904E CloseHandle`；前置 `0x4C9005 call 0x4C85E0`（imagehlp: SymInitialize/SymLoad/GetSymFromAddr，格式化 "Exception occurred at %08X"/"Exception code is %d"/"Access address:%08X"）。
- 链见 `LAYOUT.md` §2.3。IAT 全经 pefile 核实。`except.txt` 26,272 B / 2026-11-13 06:29:17 未变。

## 交付 / 分级 / 合规
- 交付：`PROGRESS.md`/`TARGETS.tsv`/`LAYOUT.md`/`CRT_NAMES.md`/`UNKNOWNS.md`/`DISAGREE.md`/`coverage_delta.tsv`/`EVIDENCE\`/`work\`。
- 三级分级：YRpp+字节体双证=`[已证]`；call-graph 收敛/单源 C 结构=`[静态推断]`；无依据保持 sub_=`[未证]`。
- 双通道：命名=YRpp 外部符号（不依赖 atlas）+ 字节体；异常链=pefile IAT + capstone skipdata 全 `.text`（1,394,186 指令）。站点归属用函数区间包含，未用 `entry_at_or_before`；capstone `skipdata=True`；RTTI 未用于类名（无类名判定）。
- 停机核验：SHA/全指令数/coverage 18,431/except.txt 均未变，见 `LAYOUT.md` §3。②-a 30/26、63B 洞、3,944 initterm 只引用未重做。
- 复跑：`python -X utf8 work\t1_counts.py` / `t2_yrpp_harvest.py` / `t2_callgraph.py` / `baseline.py` / `t4_xrefs.py` / `t4_chain.py` / `t3_heap.py` / `t3_sbh.py`。

## 结论一句话
CRT 具名符号在靶内已被 YRpp 用尽，新增 1 靶内名 + 3 归位候选；except.txt 写入点定位到 `0x4C901C/0x4C9021`。
