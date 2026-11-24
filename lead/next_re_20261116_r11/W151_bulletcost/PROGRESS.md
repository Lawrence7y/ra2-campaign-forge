# W151 · PROGRESS

时间线（2026-11-16，本卡只读静态分析；零真机）

| 时间 | 做了什么 | 结论 / 下一步 |
|---|---|---|
| 16:50 | 整份读 `R11_COMMON.md`；建卡目录 `work\`/`EVIDENCE\`；确认 Ghidra 副本、空闲内存 4.7 GB | 开工 |
| 16:53 | 从 `W130_atlas\vtables_canonical.json` 取 `.?AVBulletClass@@` 4 张表 | 主表 = **`0x7E46E4`**（col_offset==0），3 张子表 offset 12/8/4 |
| 16:56 | 写 `work\dumppvt.py`，dump `0x7E46E4` 全 125 槽 | 槽 11(+0x2C)=`0x46B550 mov eax,8` ✓；槽 12(+0x30)=`0x46B540 mov eax,0x160`；槽 23(+0x5C)=`0x4666E0`；槽 69(+0x114)=`0x468090`（= 台账 §18103 的 Draw）|
| 17:00 | grep 主台账（`BulletClass`/`0x4664`/`0x4666`/`0x468090`/`CellSpread`/`DamageArea`） | 台账 §575/§623 已有 `+0x98`/`+0x90`/`+0x158` 三处门与 `0x55B960 call [edx+0x5c]` 这一行字节，但**从未把它接到"谁遍历子弹数组"**；`CellSpread` 只有 §14764 的 `[未证]` |
| 17:04 | 写 `work\xref_scan.py`（capstone 全 `.text`，按 atlas 函数分帧）| 12,916 函数 / 44,367 条绝对操作数 / 31,042 条调用边 → `work\absref*.tsv`、`fnloops.tsv`、`edges.tsv` |
| 17:08 | 从 `W131\calledges.raw.log` 抽干净 `edges.tsv`（62,333 条，与 R11_COMMON §3.4 一致）| 校验里程碑产物可用 |
| 17:10 | 第一次查容器 xref → 只有 4 个真遍历者（0x466380 / 0x466560 / 0x534450 / 0x7192F0）+ SYNC 转储 | 发现 `0x466380` 是**构造器**（写 4 个 vptr），`0x466560` 是**析构器**；两者内联了数组 Add/Remove |
| 17:15 | 反汇编 Add/Remove 段，重定容器布局 | **R11_COMMON §3.3 的 `0xA8ED3C` 错了**：基址 `0xA8ED40`、Items `+4`、Capacity `+8`、Count `+0x10`=`0xA8ED50`、Increment `+0x14` |
| 17:20 | 意识到 `mov ecx,0xA8ED40` 是**立即数**不是内存操作数 → 重写 `work\xref_scan2.py` 同时收 IMM | 多出 `0x67D300 @0x67E00C`（`mov edx,0xa8ed40`）——上一轮"7 种数组"漏掉的那条 |
| 17:28 | 查 `0x6802F0`（子弹数组处理器）| 用 `[edi+0x10]`/`[edi+4]` **独立复核**布局；但它调对象**槽 0**（16 字节 key 匹配器），不是槽 0x5C ⇒ 不是 AI 派发 |
| 17:35 | 查 129 处 `call [reg+0x5c]` 的 91 个函数，与 `0x55D360` BFS 求交 | 只有 9 个命中且都不是子弹循环 ⇒ 派发点不在 atlas 覆盖范围内 |
| 17:42 | 写 `work\patscan.py`（原始字节搜 `FF /2` 编码）| 槽 0x5C 实为 **162 处**（atlas 只找到 129）；`0x55B8F0` 区出现 0x27 等距阶梯 |
| 17:48 | dump `0x55B8F0..0x55BAC0` | **命中**：11 条数组阶梯，块 3 = 子弹（`[0xA8ED50]`/`[0xA8ED44]`），`0x55B960 call [edx+0x5C]`；函数 = `0x55B8F0…0x55BA9F`（432 B）|
| 17:52 | 查 `0x55B8F0` 的调用者：`branchscan.py`（rel8/rel32 全扫）+ 原始 dword 全节搜 | **0 处引用**；Ghidra 也说 `getFunctionContaining(0x55b960)=null` ⇒ 该段**未分帧**，这解释了 `0x4666E0` 的"0 callers" |
| 17:58 | 查 `0x7E1918` 邻域 | `0x7E18FC` = **`LogicClass` 主虚表**（11 槽）；槽 7=`0x55BAA0`、槽 10=`0x55B880`，两者都是 AddToArray/RemoveFromArray（操 `+0x98`）|
| 18:05 | 单次 Ghidra 跑 `work\W151Probe.java`（INFO/DISASM/DECOMP/IREF）| 第 1 次编译失败（`MemoryAccessException` 未捕获）→ 修好重跑，exit=0，171 KB |
| 18:12 | 按 `=== DECOMP <addr> ===` 切反编译（第一次切错，已修）| `BulletClass::AI` 6422 B / 763 行 C / **只有 1 个真循环**（数组摘除，上界 `[0xB0F5C8]`，`+0x158` 门控）；AI 的 33 个 callee 全部 `nback=0` |
| 18:20 | 查 `0x67CEF0` 的 `0x67CC5F` 块 + `0x5F6250`（槽 13）| 槽 13 = **逐字段序列化器** ⇒ `0x67CEF0`/`0x67D300` 是**存档/COM 序列化**，推翻 §873 的"每帧对象协调"定性 |
| 18:28 | 用 `globalscan.py` 穷举 `0xB0F730/724`（全场对象数组）的引用 | 14 个函数全是内联 Add/Remove（各 1 处 Items + 3 处 Count）；与槽 0x5C 集合**交集为空** ⇒ 不存在"遍历全场对象并派发" |
| 18:35 | AI 深度 4 闭包（303 函数）与 14/6 个对象数组遍历者求交 | AbstractClass 4/14（全是 Add/Remove）、FootClass **0/6** ⇒ **无 O(b·n)** |
| 18:42 | 收尾：写 `BULLET_COST.md` / `UNKNOWNS.md` / `DISAGREE.md` / 本文件 | 交付 |

**未做完 / 交给下一卡**：U-1（谁进入 `0x55B8F0`）、U-2（`CellSpread` 消费函数）、U-3（绘制侧成本）。
预算用了约 2 小时（16:50–18:45）。
