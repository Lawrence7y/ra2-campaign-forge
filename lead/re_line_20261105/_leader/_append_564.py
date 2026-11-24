# -*- coding: utf-8 -*-
"""Append §564: D-17/D-18 rulings receipted (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7564"

head = subprocess.run(["git", "show", "HEAD:lead/GOAL_THREE_TARGETS_20261018.md"],
                      cwd=REPO, capture_output=True).stdout
wt = open(LEDGER, "rb").read()
if TAG.encode("utf-8") in wt:
    print("REFUSE: %s already present" % TAG)
    sys.exit(1)
if not wt.replace(b"\r\n", b"\n").startswith(head.replace(b"\r\n", b"\n")):
    print("REFUSE: not a prefix extension of HEAD")
    sys.exit(1)
if b"\r" in wt:
    print("REFUSE: bare CR in worktree")
    sys.exit(1)
print("guards OK; head=%d wt=%d" % (len(head), len(wt)))

SECTION = u"""
## §564 · D-17 / D-18 定谳落账：两条都选 **B（限定版）**，且**都没有授权任何执行**（2026-11-05）

> **本节的地位**：回收 `dwfrun-9b224a40`（`magpie/codex/gpt-6.1-sol$medium`，19m，
> **2.0M tokens**，五阶段跑完，门槛 `exit=0`，**独立审校 APPROVED / issues=[]**）。
> 裁决书：`lead/re_line_20261105/D17D18_RULING/RULING_D17_D18.md`（29.7 KB）
> + 核证件 `FACTBASE_D17.md` / `FACTBASE_D18.md`。
> `PENDING_DECISIONS.md` 两条已按仓规从待裁段删除、移入「已裁决记录（最近在上）」。

### 一、D-17 = **B（限定版：只选「申请受限帧内观测」路线，不授执行权）**

**裁决员明确否掉的关键点**（这几条是我原来条目里埋的坑，被逐一挖出）：

1. **原条目第 165 行「裁 B 只授权采样」不得解释为执行令。**
2. **普通 RPM 不在「E3 暂停范围之外」**：D-16 的禁令列举了
   「E3 / MiniDump / SuspendThread / StackWalk / **真机发射** / **活进程采集**」，
   并规定「**也不得编写相应采样候选代码**」「边界不因裁决放宽」
   ⇒ **只读采样仍落入该列举范围**。低扰动分级**不能替代用户授权**。
3. **原 B 所依据的两个地址是错的**（`0x887308/0x88730C` 是 `DSurface` 指针）；
   **索敌计数尚未定位**；**`GenerationStamp` 有回绕/口径限制**
   ⇒ **申请路线有研究价值，但尚无可直接实施的完整规格**。
4. **1 Hz 只是申请起点**，不保证捕获帧内峰值，**更不能承诺解开全部三条红线**。
5. 不选 A：原文的「永久放弃」**过强**（不可判只限于「现有产物」）。
   不选 C：**候选采样代码本身也在当前暂停范围**。

**执行（全部为待办，本轮未执行）**：
- 归属线先**静态补证**：生成戳写点/初始化/回绕/入口覆盖；真实视口坐标；索敌计时器与实际执行计数。
  每项列 VA、类型、生命周期、访问证据、计数口径；**未知项写「未定位」，不编造**。
- 形成**待用户审定的观测卡**（字段、频率、读权限、记录格式、时间对齐、读失败记 null、
  重置/回绕处理、停止与清理条件）。
- 申请**至少分两闸**：① 是否允许候选代码 + 离线验证；② 是否另行批准指定批次真机/活进程采集。
- **未获对应闸的用户明示授权前继续暂停。E3 始终另裁。**

### 二、D-18 = **B（移交 RE-ATLAS 按写域办理追加勘误）**

1. **依 D-07，不授来源线 `docs/re/` 写权**；「追加」不形成权限例外。
2. 技术要求：**同时撤回两处** —— `:48` 的「硬编码 2000 节点」与 `:74` 的「`+0x3C`=MaxNodeBudget」。
   正确表述：`SearchCore` 单次的**节点处理/展开轮数上限**，负预算缺省 65527，**非负保留**；
   **不是**实际展开量 / 不同格子数 / 整次 FindPath 总量 / 耗时。
3. **来源线义务**：在自身写域追加 W2 传播纠偏，并**不得按 32.76 倍线性推算帧时**。
4. 不选 A（越写域）、不选 C（已知错误继续误导，W2 已有传播实例）。
5. **验收**：须取得 RE-ATLAS 与 W2 两份**可定位回执**；未取得前记「**路线已裁、落实未闭合**」。

### 三、本轮已执行的落实动作

| 动作 | 产物 | 状态 |
|---|---|---|
| 两条移入「已裁决记录」 | `PENDING_DECISIONS.md`（待裁段现只剩 D-13/D-14/D-15） | ✅ |
| D-18 的**来源线义务**：W2 传播纠偏 | `lead/re_line_20261105/W2_FRAMETIME_ATTRIB/ERRATA_D18_20261105.md` | ✅（原文一字未改） |
| D-18 的**移交包** | `lead/re_line_20261105/D18_HANDOFF_TO_REATLAS.md` | ✅ 已备，**尚未送达** |
| D-17 的静态补证 / 观测卡 | — | ⏸ **未做**（需归属线先补字段语义，且属「观测」准备，本轮不越权） |

### 四、这对目标①意味着什么（诚实表述）

**没有变快，只是把「不知道」变成了「知道不知道什么、以及要什么才能知道」。**

- 「四个成本中心 + 三条红线」的结论**保持不变**；
- **C1 的定量排序不可得**：上限虽从 2000 变 65527，但**实际用量取决于提前终止**，
  无观测通道 ⇒ **不能按 32.76 倍推算**；
- **C2 的理由须改写**（地址定性错了），但**结论不变**（仍不可判）；
- ⇒ **目标①的机制未闭合状态不变**；三目标句态不变（①未复现/②RC-4 不收口/③保持态）。

### 五、诚实账

1. **我亲验**：裁决书的五节结构与两份「★ 定谳」块全文；审校 `APPROVED`/`issues=[]`；
   `PENDING_DECISIONS.md` 改动后待裁段只剩 3 条（D-13/D-14/D-15）。
2. **我未验**：裁决书引用的全部字节（**采信核证员与审校员**；审校员自陈「本次实跑独立 PE 静态反汇编，
   `SEARCHCORE_DECODE 2509 2509`、`FINDPATH_DECODE 976 976`」，我未复跑该命令）。
3. **我未验**：`E3_SAMPLING_PLAN_REVIEWABLE.md` —— **裁决员报告该文件不存在**
   （`rg --files` 只找到三件 E3 文件）。这是 D-13 条目里引用的一份路径，**可能已失效**，值得下一轮核实。
4. **我未做**：D-17 的静态补证与观测卡 —— 本轮按「不做越权准备」处理，非遗忘。
5. **移交未送达**：我无 RE-ATLAS 会话通道，只能把移交包置于仓内其可见路径。
   若长期不办理，依 D-18 第 6 步回退用户，**不自行改走 A**。
6. 本轮**零真机**、**未改 `docs/re/` 一字**、**未 commit**。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
