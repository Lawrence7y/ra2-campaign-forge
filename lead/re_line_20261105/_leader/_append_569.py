# -*- coding: utf-8 -*-
"""Append §569: D-20=B execution + B conclusion + W3 C2 erratum (guarded)."""
import subprocess
import sys

LEDGER = r"D:/Project/ra2-campaign-forge/lead/GOAL_THREE_TARGETS_20261018.md"
REPO = r"D:/Project/ra2-campaign-forge"
TAG = "## \u00a7569"

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
## §569 · D-20 裁 B 并已执行：**「可见单位数」不存在现成计数 VA**（2026-11-05）

> **本节的地位**：用户 2026-11-05 下令「**所有行动都授权、所有裁决交 gpt-6.1-sol**」
> 并要求「**裁决流程快起来**」。本节记录：① 全开授权的落账；② 裁决流程简化；
> ③ **D-20 快裁（分钟级）的结论**；④ **B 步的执行结果**。

### 一、用户全开授权（已落 `PENDING_DECISIONS.md:144`）

原话：「**第一项授权。第二项真机活进行采集也授权，所有的行动都授权，所有的裁决都交给 gpt 6.1 sol 执行。**」
- D-17 的两级闸（候选代码 / 真机采集）**全部放开**；
- 「所有行动」放开（含写候选件、真机、活进程只读采集、commit/push、跨线写域）；
- 「所有裁决交 gpt-6.1-sol」：本线**不再自行裁决**。
- **保留安全下限**（非权限下限）：不 `taskkill` 生产进程、不改用户存档、结论须可追溯、不伪造。

### 二、裁决流程简化（用户令，已入锚点 §二之三）

**废止**五阶段流水线（独立核证→裁决→独立审校→文书→门槛，实测 22–29 分钟 / 2–2.5M tokens）。
**新基准**：`立 D-xx → gpt-6.1-sol 单轮裁决 → 文书 → 执行`，**不设独立核证/审校**。
**D-20 实测**：`dwfrun-abf90739` 用新流程，**几分钟内出结论**。

### 三、D-20 = **B**（执行顺序 B → A → C，B 设明确出口）

裁决原文要点：
> 「先核清可视性判定与可读取驱动量，**可避免把脏矩形 Count 误当可见单位数**。
> B 若证明不存在现成计数或静态证据不足，**应明确记录缺口并转 A，不能无限阻塞最小采样**。
> C 的慢窗匹配和采样扰动问题仍待解决，排在通道验证之后。」

### 四、★ B 步执行结果：**不存在现成「可见单位数」计数 VA**

**我实跑的三组证据**（`_b_visibility_probe.py` / `_b_counter_hunt.py` / `_b_callers_probe.py`）：

| 证据 | 结果 |
|---|---|
| `0x5F4B10` 全函数 | **无第二参数输出、不写任何全局**；返回值只是 `al` 布尔 |
| `call 0x5F4B10` 全镜像 | **仅 3 处**：`0x422C8E`、`0x73B132`、`0x749B5B` —— **全是 3–5 指令的透传包装**，无计数 |
| `0x6D8DB0..0x6DA1FB`（1603 条）内 `call 0x5F4B10` | **0 处** |
| 同范围「`mov [abs],reg` 写全局 dword」 | **0 处** |
| 同范围 4 字节 `inc/dec` | 19 处，**全为寄存器**（`inc eax` / `dec eax`），**无一落内存** |
| `call 0x6D2140`（IsVisible） | **139 处**，均为 `test al,al` 取布尔，**无一处跟 `inc [全局]`** |

⇒ **判定为第 (ii) 类「需遍历推导」，而非 (i)「现成计数」。**
按 D-20 出口条件：**记录缺口、F6 仍标未定位、不强行认定任何 VA、转 A**。

**遍历推导为何也不可行**：即使拿到对象表，也要在外部**复现 `0x6D2140` 的等轴测投影 + 视口裕量比对**
（其头部已读：`0x6D2140` 内做 3D→屏幕投影后比视口矩形），
**等价于在外部实现一遍渲染判定**，成本与风险远超读一个计数器。

### 五、连带勘误：W3 `Q1_C2_RENDER.md` 有一处与实测不符

W3 称「`0x6D8DB0` 外层遍历 5 个 Layer，**内层逐单位调 `DrawIfVisible`**」。
**实测该簇内 `call 0x5F4B10` = 0**。
⇒ 该表述**须勘误**（本轮只登记，**未改 W3 原文**）。

**但 C2 的结论方向不变**：裁剪失败跳过整条绘制链（`0x5F4B7F: xor al,al; ret 0xC`）**已亲验成立**；
只是「谁在调它」的遍历位置**说错了**。

### 六、对目标①的诚实表述

**C2 这条线，在不实现外部判定复现的前提下，无法用单一计数器代理。**
这**强化**了 D-19「四 VA 不足以完全解耦」的判断，也**削弱**了「用一个 VA 代表屏内可见单位数」的想法。
**但 C2 并未被排除**——它仍是强解释源，只是**不可被只读计数器观测**，
除非接受 `0x00B0CE88`（脏矩形 Count）作**语义受限的间接代理**（D-19 已采纳）。

### 七、诚实账

1. **我亲验**：§四表格全部六行；`0x422C8E`/`0x73B132` 两个调用点的上下文（均为透传包装）。
2. **我未验**：`0x749B5B` 调用点上下文（第三个）——**不影响结论**（形态与前两个同构）。
3. **我未验**：`0x6D2140` 的完整投影算法（只读头部 `0x80` 字节）。
4. **我未验**：`0x00B0CE88` 与可见单位数的定量关系（D-19 已判「未校准」）。
5. 本轮**零真机**、**未改 W3 原文**、**未 commit**。
6. **下一步（A）**：按 D-19 帧沿规格，用**现有四 VA + 帧号**做候选件与离线单测；
   **alpha 未校准与采样充分性未证**这两个标记**必须保留在候选件里**。
"""

with open(LEDGER, "ab") as f:
    f.write(SECTION.encode("utf-8"))
print("appended %d bytes" % len(SECTION))
