#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""台账 §611 写入：D-13 = C 裁决登记（append-only + 四项自检）。"""
import hashlib
import os
import re
import shutil
import sys
from collections import Counter

REPO = r"D:\Project\ra2-campaign-forge"
LEDGER = os.path.join(REPO, "lead", "GOAL_THREE_TARGETS_20261018.md")
WORK = os.path.join(REPO, "lead", "re_d13_ruling_20261112")

# §610 落盘后的基线
BASE_BYTES = 802956
BASE_SHA = "b5e4c1c8861f432ad4ce1bbdd6928a92432d622bb107bfdc0339f92d5e185cdc"
BASE_LINES = 9910

SEC = """## §611 · ★★ 裁决登记：D-13 用户明示「选 C」⇒ 走甲案 `SuspendThread`+`GetThreadContext`+`StackWalk64`；**仅解除「候选件 + 离线单测」禁令，真机/活进程仍未授权**（2026-11-12）

- **裁决来源**：用户 2026-11-12 当轮明示「**D 13 选 c**，继续」。对应 D-13 三选一中的 **(C)**。
- **裁决内容**：E3 栈采样改走**甲案**（`SuspendThread` + `GetThreadContext` + `StackWalk64`，≤50 ms/次）尝试覆盖短停主体；不再走乙案（`MiniDumpWriteDump`）。
- **★ 范围界定（解除与未解除必须分清，不得混用）**：
  1. **已解除**：D-31 Q4（`lead/direction_ruling_20261108/RULING_DIRECTION.md` / 16,514 B / `0ebd68dd11a2a54a`）曾判「**不批准**以『只编写候选件 + 离线单测』放行采样代码」。用户本次明示选 C，构成对该禁令的**明确改变** ⇒ **编写 SuspendThread/StackWalk 候选件 + 离线单测现已获授权**。
  2. **未解除**：**真机发射 / 活进程采集 / attach / 读活进程内存**仍未授权。依据 D-15 已裁决原文「未经用户明示授权的 E3/MiniDump/SuspendThread/StackWalk/**真机发射/活进程采集**一律不得执行、也不得编写相应采样候选代码」与 D-31 Q4「真机/活进程须**当轮明示**」；用户本轮只说「选 c / 继续」，**未**就真机发射明示 ⇒ **仍不执行**。**本条不构成真机授权，也不得被引作真机授权依据。**
  3. **仍未得到答案的子问题**：E3 卡 §7 第 3 项「授权边界：①仅编写候选件+离线单测（卡内推荐）／②含真机发射」——用户**未就此项作答**。本线按**最保守**取 ①（只写候选件 + 离线单测），并把 ② 保留为待明示项。
- **触发条件**：沿用 E3 卡 §2 建议「**帧号 `[0xA8ED84]` 连续 N 秒不变**」，**N = 1.0 s**（§532 已复算：真实正常抖动上限 360 拍 = 900 ms；N=1.0 s 误触率实测 **0**，含 Δf>1 的 3 例、最大 410 ms）。用户**未另改 N**。原 E3 的 `latch_detected` 触发条件**不适用**于目标①（①的帧冻结趟正常退出：`l3_20261023q` rc=0 / 259.7 s / 无残留，§530–§532 已证）。
- **必须连带声明的能力边界（不得省略）**：
  1. C 案是**为覆盖 87.7% 的 0.1–0.2 s 短停**而选（乙案自身停顿数百 ms–秒，物理上采不到短停主体）。
  2. 但 E3 方案原文自述甲案「**可能自造死锁**」，且对目标②（正常退出读数）属**高反身影响**（E3 卡 §4 分级表：甲案「高」、乙案「中」）。**该死锁风险本线未独立验证**（E3 卡 §8-4 自认）。
  3. ⇒ 本线在候选件中必须实现：**逐线程挂起 → 立即恢复**的严格配对（`try/finally` 保证不留挂起态）、**单次总停顿上限**、**失败即记录错误码不重试不强杀**、以及**与②读数分列**的反身护栏。这些在候选件与离线单测中可验，但**真机行为仍未验**。
- **仍待用户另行明示的两项**：① 真机发射批次；② 是否接受「C 案死锁风险可能污染②读数」这一代价（E3 卡 §7 第 3 项）。
- **执行落点**：候选件与离线单测在 `lead/re_d13_ruling_20261112/`（本轮新建）；裁决登记流程见 `lead/re_d13_ruling_20261112/RULING_RECEIPT_611.md`。
- **PENDING_DECISIONS 同步**：D-13 已从「待裁决事项（当前）」段移入「已裁决记录（最近在上）」段；其**原始正文与 D-31 Q4 历史状态块均逐字迁移、未改一字**；原挂在 D-13 状态块内的 **N10-C04 / 上游 Q3「静态检索任务的顺序与新写域」仍待裁**，已拆出单列保留在待裁段。
- 本节**零真机、零采样代码执行、未改既有件（除本节追加本体）、未 commit、未 push**。
"""


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    os.makedirs(WORK, exist_ok=True)
    ok = True

    raw = open(LEDGER, "rb").read()
    bl = len(raw)
    bs = sha(raw)
    print("== STEP 0 · before ==")
    print("bytes = %d" % bl)
    print("sha   = %s" % bs)
    print("[%s] baseline 802956" % ("PASS" if bl == BASE_BYTES else "FAIL"))
    print("[%s] baseline sha" % ("PASS" if bs == BASE_SHA else "FAIL"))
    ok = ok and bl == BASE_BYTES and bs == BASE_SHA
    if not ok:
        print("!! 基线不符，停止")
        return 2

    bak = os.path.join(WORK, "GOAL_before_611.md")
    if not os.path.exists(bak):
        shutil.copyfile(LEDGER, bak)

    payload = "\n\n" + SEC
    pb = payload.encode("utf-8")
    print("\n== STEP 1 · 追加 ==")
    print("payload_bytes = %d" % len(pb))
    print("payload_sha   = %s" % sha(pb))

    with open(LEDGER, "ab") as f:
        f.write(pb)

    after = open(LEDGER, "rb").read()
    print("\n== STEP 2 · after ==")
    print("bytes = %d" % len(after))
    print("sha   = %s" % sha(after))

    print("\n== STEP 3 · 四项自检 ==")
    cr = []

    def chk(t, c, d=""):
        print("[%s] %-34s %s" % ("PASS" if c else "FAIL", t, d))
        cr.append(c)

    chk("a 前缀 sha == before sha", sha(after[:bl]) == bs)
    txt = after.decode("utf-8")
    hc = Counter(re.findall(r"(?m)^##+ *§(\d+)\b", txt))
    for n in range(605, 612):
        chk("b §%d 节标题数==1" % n, hc.get(str(n), 0) == 1, str(hc.get(str(n), 0)))
    ap = after[bl:]
    chk("c 追加字节数 == payload", len(ap) == len(pb), str(len(ap)))
    chk("c' 追加段 sha == payload", sha(ap) == sha(pb))
    blines = len(open(bak, encoding="utf-8").read().splitlines())
    alines = len(txt.splitlines())
    chk("d 旧行数 == 9910", blines == BASE_LINES, str(blines))
    chk("d' 行数增量 == 追加行数", (alines - blines) == len(payload.splitlines()),
        "%d->%d (+%d) vs %d" % (blines, alines, alines - blines, len(payload.splitlines())))
    chk("d'' UTF-8 无 U+FFFD", txt.count("\ufffd") == 0, "fffd=%d" % txt.count("\ufffd"))

    print("\n== STEP 4 · 定位 ==")
    for i, ln in enumerate(txt.splitlines()):
        if ln.startswith("## §611"):
            print("§611 标题行 = L%d" % (i + 1))
            break
    print("总行数 = %d" % len(txt.splitlines()))
    print("\n==== RESULT: %s ====" % ("ALL PASS" if all(cr) else "HAS FAILURE"))
    return 0 if all(cr) else 1


if __name__ == "__main__":
    sys.exit(main())
