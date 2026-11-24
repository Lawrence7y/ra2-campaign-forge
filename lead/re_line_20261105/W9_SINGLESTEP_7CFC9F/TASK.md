# W9 任务书 · 目标② 主崩溃：`EXCEPTION_SINGLE_STEP @ 0x7CFC9F` 的静态定谳

> **为什么是这一题**：目标②（修主崩溃）在线性推进上**长期停滞**。
> 台账 §555 的退场普查得到「37 个 archive 目录零趟游戏崩溃」，
> 但那条结论的**必要前提**（107 份 `except_post_*.txt` 单一哈希）只是旁证，
> **「0 趟崩溃」这条从未被独立验证过**（§555 诚实账第 3 条自陈）。
>
> 唯一有真实异常上下文的一件证据是：
> `out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt`（26,405 B）
> —— `EXCEPTION_SINGLE_STEP`、`Eip=007CFC9F`、`EFlags=00000286`、`Esi=7FFFFFFF`、`Edi=00000001`。
>
> **本任务纯静态：零真机、零采样代码、零活进程读取。** 只允许 `ra2tool.Engine` 反汇编 + 磁盘文件读。

## 0. 目标镜像（必须先自证）

| 项 | 值 |
|---|---|
| 路径 | `D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe` |
| SHA256 | `73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476` |
| 字节数 | `4,825,360` |
| ImageBase | `0x400000` |

读法：`sys.path.insert(0, r'D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104')` → `from ra2tool import Engine`。

★ **Engine 的 `disasm` 会吞异常**：`by()` 不在流里的地址，`disasm` 可能返回空列表。
查「某地址是不是指令起始」必须用 `va in e.by()`；查原始字节用 `e.rd(va, n)`（**`e.raw` 是 bytes 不是函数**）。

## 1. 先读（按序，只读不改）

1. `out/re_work/work_chain/CONTINUE_20261003/lead/boot_hang_triage_20261018/EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt` —— **主证据**，全文
2. 同目录 `SINGLESTEP_0x7CFC9F_ANALYSIS.md`（17,473 B）—— 2026-10-19 的旧分析，**默认怀疑它**
3. `lead/ROUND_SUBAGENT_LOG_TRIGOAL_20261017.md:1898` 与 `:1962-1969` —— 当时的现场记录
4. `lead/GOAL_THREE_TARGETS_20261018.md` §555 —— 「零趟游戏崩溃」普查与其诚实账

## 2. 五项必须回答（每项都要给字节依据或明确写「未验」）

### Q1 · `0x7CFC9F` 处的代码到底是什么

- `Engine().rd(0x7CFC9F, 32)` 拿原始字节，逐条反汇编到 0x30 字节。
- 证据件里已给 `Bytes at CS:EIP (007CFC9F): 8B 0A 2B 4D F0 8B F1 89 4D F8 C1 FE 04 4E 83 FE 3F 7E 03 6A 3F 5E 3B F7 0F 84 0D 01 00 00 8B 4A`
  —— **必须自己重读一遍这些字节，逐字节比对是否一致**，不一致要写出来。
- 逐条写出前 8 条指令的助记符与操作数。
- `0x7CFC9F` 是否在重同步流里（`va in e.by()`）？若**不在**，说明它是 `call`/`jmp` 的落点还是数据区，给依据。

### Q2 · 它属于哪个函数

- 向上回溯到最近的函数序言（`push ebp; mov ebp,esp` 或 `sub esp,imm` 且前方是 `ret`/`int3` 对齐）。
- 给函数起止 VA、长度、函数内 `ret` 的数量（`e.func_rets`）。
- 该函数**是否在既有的 crashspec 工作范围里被分析过**？搜 `lead/` 与 `docs/re/` 下的文件里是否出现过这个 VA。
  **不许只搜一次就断言「没有」** —— 至少用两种口径（VA 写法 `7CFC9F`、`0x7CFC9F`、`7cfc9f`）。

### Q3 · `EXCEPTION_SINGLE_STEP` 但 `EFlags` 无 TF 位 —— 机制上怎么解释

- `EFlags = 0x286` 的位分解：逐位标注 TF(bit8)、IF(bit9)、RF(bit16)、VM(bit17) 等。
- **若 TF=0，硬件单步陷阱不可能触发** ⇒ 那么这次 `EXCEPTION_SINGLE_STEP` 只能来自：
  ① 有人调了 `SetThreadContext` 置 TF 后又清掉；② 调试寄存器（DR0–DR3 执行断点）命中；
  ③ `RaiseException(EXCEPTION_SINGLE_STEP, ...)` 手工抛出；④ 其它。
- **对每条候选给「能否被这份证据支持/排除」的判据**，不要只列可能性。
- 证据件里 `Esi=7FFFFFFF`、`Edi=00000001` 这两个值是否对某条候选是特征值？给推理链或写「未验」。

### Q4 · 这个地址与「主崩溃」是什么关系

- 台账 §555 说这一类 `except_post` 是**历史基线残件**（107 份同哈希 `6694b75e…`）。
- **本任务要核**：`EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt`（26,405 B）是否**就是**那 107 份之一？
  自己算它的 SHA256，并与 `except_post_*.txt` 的哈希比对（`find` + `sha256sum` 或 python）。
  ★ **这是本节最关键的一问**：若同哈希 ⇒ 该证据**不是任何一趟的崩溃**，整个「主崩溃」叙事要重新定位；
  若不同哈希 ⇒ 它是一件**独立的**异常证据，价值高得多。
- 给出明确二选一的结论 + 依据。

### Q5 · 目标② 下一步该做什么（只给路线，不执行）

- 基于 Q1–Q4 的结论，给 2–3 条候选路线，每条写：需要什么数据、是否受 D-13 限制、代价。
- **不写任何采样代码**。

## 3. 每份回件强制头部（缺则整份作废）

```
被核对象 = gamemd.exe + EXCEPT_SINGLESTEP_0x7CFC9F_20261019T1352.txt
gamemd.exe SHA256 = <自己实算的 64 位>，字节数 = <自己实算的>
EXCEPT 件 SHA256 = <自己实算的 64 位>，字节数 = <自己实算的>
Engine 自证 = COVERAGE <coverage> / IMAGEBASE 0x400000
回件时刻 = <实际时刻>
```

## 4. 判定档

- **CONFIRMED**：每个结论都有「反汇编地址 + 原始字节」或「文件:行」支撑。
- **PARTIAL**：部分结论有支撑，部分只能给可能性。
- **REFUTED**：发现旧分析 `SINGLESTEP_0x7CFC9F_ANALYSIS.md` 的实质错误（要点名是哪一条、字节依据是什么）。

## 5. 交付物

写到 `lead/re_line_20261105/W9_SINGLESTEP_7CFC9F/`：
- `Q1_CODE.md` / `Q2_FUNCTION.md` / `Q3_MECHANISM.md` / `Q4_RELATION.md` / `Q5_ROUTES.md`
- `reviews/Q*_review.md` —— 每项一道独立复核
- `W9_SINGLESTEP.md` —— 汇总（`## 0 总判` / `## 1 SHA256 绑定` / `## 2 Q1 代码` / `## 3 Q2 函数` / `## 4 Q3 机制` / `## 5 Q4 与主崩溃的关系` / `## 6 Q5 路线` / `## 7 必须改项` / `## 8 诚实账`）
- `_w9_*.py` + `_w9_*_out.txt` —— 只读探针

## 6. 铁律（违反即作废）

- **零真机**：不启动 `gamemd.exe` / `ra2loader` / `YURI.exe`，不 `taskkill`，**不读活进程内存**。
- **零采样代码**：不写 hook / MiniDump / SuspendThread / StackWalk / 探针注入。**E3 维持暂停（D-13）**。
- **只读**：`ra2youli\`、`out\re_work\...`、`lead/GOAL_*`、`lead/PENDING_DECISIONS.md`、
  `lead/ROUND_SUBAGENT_LOG_*`、`W1_*`…`W8_*` 既有件、`D*_RULING\`、`_leader\*` —— **一律不得修改**。
  **唯一写域 = `W9_SINGLESTEP_7CFC9F/`**。
- Python 一律 `python -I -X utf8`，绝对路径。
- **不 commit、不 push**。
- 每个数字追到「实跑命令 + 输出」或「文件:行」；**拿不到就写「未验」，不许补造**。
- ★ **不要把「查不到」当成「不存在」**。
- ★ **否定性/存在性事实先用文件系统命令核**（`find` / `ls` / `wc` / `sha256sum`），
  **不要上全仓 Python 遍历 + Engine**；只有需要字节内容判定才上 Engine，且必须**限定地址窗口**。
- ★ **并行度**：本任务最多同时 2 个子代理（用户 2026-11-06 令）。
