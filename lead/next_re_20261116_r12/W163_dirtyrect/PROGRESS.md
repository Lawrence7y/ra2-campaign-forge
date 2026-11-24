# W163 PROGRESS（每完成一步追加）

- 2026-11-16 19:03｜读 `R11_COMMON.md` 全文 + `R12_FACTS.md` §6–§12；grep 主台账脏矩形相关节（§6643/7090/8143/900-5/900-6/900-7）。确立双通道纪律与 §6.2。
- 19:05｜拷 `w161_lib.py`→`work/w163_lib.py`；建 `work/`、`EVIDENCE/`。确认 Python capstone 5.0.7/pefile 2024.8.26、Ghidra 副本 `_ghidra/W163`、无 java 在跑。
- 19:06｜`w163_explore_container.py`：发现 `0xB0CE88` 在 `.bss`（无磁盘字节），vptr 运行期写 ⇒ 转字节通道扫引用。
- 19:07｜`w163_scan_container_refs.py`：全 `.text` skipdata 扫 `0xB0CE50..0xB0CEC0`，89 命中；实证 DynamicVectorClass 布局 base `0xB0CE78`、Count `0xB0CE88`、Inc `0xB0CE8C=0xA`。
- 19:08｜`w163_vtables.py`：vptr `0x7F429C/0x7F42BC`（各 7 槽）；`w163_keyfuncs.py`：11 个关键函数回边/调用数；定位 `0x6D3D10`(10 回边/58 call)、`0x6D2790`(Add,2 回边)。
- 19:09｜`w163_add_disasm.py` + Ghidra `W163Gather.java`（后台,-noanalysis,exit=0）：**Add 反编译确认 O(k) 扫描 + O(k) 搬移 ⇒ O(k²)**；双通道字段引用数逐项相等。
- 19:10｜收到 Lead 插入的 CPU 复算（④帧等待排除、缺口钉死 0.61 ms/发）；纳入 Q4 权重，追加"子弹转嫁子系统"检查。
- 19:11｜`w163_dual_bfs.py`：深度≤8 双通道 BFS——Ghidra 1062 / 字节 1570 函数，两通道命中**相同 11 个脏矩形簇目标**；`0xA8E9A0` 123 处绝对引用。
- 19:12｜`w163_paths.py` + `w163_path_context.py`：最短路径两通道逐跳一致；子弹 AI→Add 深度3（`0x421EA0→0x5F4EC0→0x6D2790`）；flush 深度7；10 个路径调用点**全部指令边界有效**。
- 19:13｜`w163_q23.py`：Add 调用者 46(A)/47(B)，其中 23/24 在闭包内；识别 G_INGAME 语义（子进程 Init 置 1、模态框清 0 恢复）。
- 19:13｜`w163_q3_detail.py` / `w163_final_checks.py`：`0x5F3B80` 是析构器非热点；`0x6D3D10←0x4F4480←0x55D360` 每帧链闭合；`0x466560`=BulletClass 构造（vt `0x7E46E4`、inc Bullet Count、调 `0x5F4D30` 脏 Add）。
- 19:13｜全镜像扫描：仅 3 函数在循环读 Bullet Count；深度≤3 仅 3 函数"回边+容器Count" ⇒ O(b·n) 基本排除。
- 19:14｜收尾：写 `DIRTYRECT.md`（5 行摘要 + Q1–Q5 + 判决 + LEAD_AUDIT）、`UNKNOWNS.md`、`DISAGREE.md`。

**结论状态**：Q1/Q5 `[已证]`；Q2 路径 `[已证]`、频率 `[静态推断]`/精确数 `[未证]`；Q3 负结果 `[已证·负]` + 嵌套结构 `[已证]`、频率 `[静态推断]`；Q4 判决 ⑤最可能（`[已证]` 结构/`[静态推断]` 主导性）、③必须真机。
