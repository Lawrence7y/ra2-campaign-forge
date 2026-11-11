#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""D-13 = C 裁决登记：更新 PENDING_DECISIONS.md。

纪律依据（PENDING_DECISIONS.md 头部原文）：
  「裁决后由**该条目的来源会话**在下一轮执行删除 + 台账记一行
   `D-xx 已裁决（<日期>）：<结论>；执行：<下一步>`，同一提交完成。」

本脚本做三件事：
  1. 待裁段：把 D-13 的状态块 + 原始正文块移出（原文逐字迁移，不改一字），
     仅留一行指针；**N10-C04 待裁项保留不动**。
  2. 已裁决记录：在标题下插入 D-13 已裁决条目（含用户裁决原文、范围界定、保留原文）。
  3. 自检：行数变化可解释、D-13 原文零丢失（逐字节在迁移后仍存在）、N10-C04 仍在。

写域：本脚本 + stdout 在 lead/re_d13_ruling_20261112/；被改件：lead/PENDING_DECISIONS.md
"""
import hashlib
import os
import shutil
import sys

REPO = r"D:\Project\ra2-campaign-forge"
PD = os.path.join(REPO, "lead", "PENDING_DECISIONS.md")
WORK = os.path.join(REPO, "lead", "re_d13_ruling_20261112")

BASELINE_SHA = "3765eddbe96deeb65eeb1f05dc81e1dc171e7ea3b2c826e2692a1d15e1c8f2d7"
BASELINE_BYTES = 52419


def sha(b):
    return hashlib.sha256(b).hexdigest()


def main():
    os.makedirs(WORK, exist_ok=True)
    raw0 = open(PD, "rb").read()
    print("== STEP 0 · before ==")
    print("bytes = %d" % len(raw0))
    print("sha   = %s" % sha(raw0))
    print("expect bytes %d / sha %s" % (BASELINE_BYTES, BASELINE_SHA))
    ok = (len(raw0) == BASELINE_BYTES and sha(raw0) == BASELINE_SHA)
    print("[%s] baseline match" % ("PASS" if ok else "WARN"))
    if not ok:
        print("!! 基线不符 —— 可能已被他处改动，停止")
        return 2

    bak = os.path.join(WORK, "PENDING_DECISIONS_before.md")
    if not os.path.exists(bak):
        shutil.copyfile(PD, bak)

    lines = raw0.decode("utf-8").splitlines(True)
    print("\n== STEP 1 · 定位 ==")

    def find(pred, start=0):
        for i in range(start, len(lines)):
            if pred(lines[i]):
                return i
        return -1

    i_wait = find(lambda l: l.startswith("## 待裁决事项（当前）"))
    i_done = find(lambda l: l.startswith("## 已裁决记录"))
    i_d13_status = find(lambda l: l.startswith("- **D-13 已同步状态"))
    i_d13_orig = find(lambda l: l.startswith("### D-13 原始正文（保留供追溯，不改）"))
    i_d14 = find(lambda l: l.startswith("- **D-14 已同步状态"))
    print("待裁段标题   L%d" % (i_wait + 1))
    print("已裁决标题   L%d" % (i_done + 1))
    print("D-13 状态块  L%d" % (i_d13_status + 1))
    print("D-13 原始正文 L%d" % (i_d13_orig + 1))
    print("D-14 状态块  L%d" % (i_d14 + 1))
    assert i_wait < i_d13_status < i_d13_orig < i_d14 < i_done

    # --- 保存 D-13 两块的逐字原文 ---
    status_block = lines[i_d13_status:i_d13_orig]          # 状态块（含尾部空行）
    orig_block = lines[i_d13_orig:i_d14]                    # 原始正文块
    status_text = "".join(status_block)
    orig_text = "".join(orig_block)
    print("status_block 行数 = %d" % len(status_block))
    print("orig_block   行数 = %d" % len(orig_block))

    # 抓 N10-C04 那两行（在状态块内，必须保留）
    n10 = [l for l in status_block if "N10-C04" in l]
    print("N10-C04 行数 = %d" % len(n10))
    assert len(n10) >= 1

    # --- 构造替换内容 ---
    pointer = (
        "- **D-13 已裁决（2026-11-12，用户当轮明示「D 13 选 c」）：见「已裁决记录」段。**\n"
        "  **★ 本次裁决只解除「编写候选件 + 离线单测」的禁令**；**真机发射 / 活进程采集仍未授权**，"
        "按 D-15 与 D-31 Q4 须**当轮明示**，不得由本条或既有裁决代授。\n"
        "  原「D-13 已同步状态」块与「D-13 原始正文」块已**逐字迁移**至「已裁决记录」段供追溯（不改一字）。\n"
    )
    # N10-C04 仍待裁 —— 单独成条保留在待裁段
    n10_block = (
        "\n- **N10-C04 / 上游 Q3「静态检索任务的顺序与新写域」仍待裁**（原挂在 D-13 状态块内，"
        "D-13 归档时拆出单列）：不能以「更新缺口状态」冒充已裁任务顺序或写域。\n"
        "  裁决依据出处：`lead/direction_ruling_20261108/RULING_DIRECTION.md`（16,514 B / `0ebd68dd11a2a54a`）Q4。\n"
    )

    new_done_entry = (
        "- **D-13 已裁决（2026-11-12）：用户当轮明示「D 13 选 c」⇒ 选 (C)。**\n"
        "  **结论**：走**甲案 `SuspendThread` + `GetThreadContext` + `StackWalk64`**（≤50 ms/次）尝试覆盖短停主体。\n"
        "  **范围界定（本次裁决解除与未解除的部分，必须分清）**：\n"
        "  1. **已解除**：D-31 Q4 曾判「**不批准**以『只编写候选件 + 离线单测』放行采样代码」——"
        "用户本次明示选择 C，构成对该禁令的**明确改变**，故**编写 SuspendThread/StackWalk 候选件 + 离线单测**现已获授权。\n"
        "  2. **未解除**：**真机发射 / 活进程采集 / attach / 读活进程内存**仍未授权。"
        "依据 D-15 已裁决原文「未经用户明示授权的 E3/MiniDump/SuspendThread/StackWalk/**真机发射/活进程采集**一律不得执行」"
        "与 D-31 Q4「真机/活进程须**当轮明示**」，用户本轮只说「选 c / 继续」，**未**就真机发射明示 ⇒ 仍不执行。\n"
        "  3. **触发条件**：沿用 E3 卡 §2 建议「帧号 `[0xA8ED84]` 连续 N 秒不变」，N = 1.0 s（§532 已复算："
        "真实正常抖动上限 360 拍 = 900 ms，N=1.0 s 误触率实测 0）。**用户未另改 N**。\n"
        "  4. **必须连带声明的能力边界**：C 案是为覆盖 87.7% 的 0.1–0.2 s 短停而选；"
        "但 E3 方案原文自述甲案「**可能自造死锁**」，且对目标②（正常退出读数）属**高反身影响**"
        "（E3 卡 §4 分级表）。该风险**本线未独立验证**（E3 卡 §8-4 自认）。\n"
        "  5. **仍待用户另行明示**：真机发射批次、以及是否接受「C 案死锁风险可能污染②读数」这一代价。\n"
        "  执行：见台账 §611；候选件与离线单测在 `lead/re_d13_ruling_20261112/`。\n"
        "  **原始条目正文（逐字保留，供追溯；自待裁段迁移而来，未改一字）**：\n\n"
    )

    # --- 组装：待裁段（D-13 两块 → 指针 + N10-C04 单列）---
    seg_wait_head = lines[i_wait:i_d13_status]
    seg_wait_tail = lines[i_d14:i_done]
    new_wait = seg_wait_head + [pointer] + [n10_block] + seg_wait_tail

    # --- 组装：已裁决段（标题后插入 D-13 条目 + 迁移来的原文）---
    seg_done = lines[i_done:]
    # seg_done[0] 是 '## 已裁决记录（最近在上）'，[1] 通常空行
    insert_at = 1
    while insert_at < len(seg_done) and seg_done[insert_at].strip() == "":
        insert_at += 1
    indent_orig = []
    for l in orig_block:
        indent_orig.append(("  " + l) if l.strip() else l)
    new_done = (
        seg_done[:insert_at]
        + [new_done_entry]
        + indent_orig
        + ["\n"]
        + seg_done[insert_at:]
    )

    out = lines[:i_wait] + new_wait + new_done
    new_text = "".join(out)
    nb = new_text.encode("utf-8")
    open(PD, "wb").write(nb)

    print("\n== STEP 2 · after ==")
    print("bytes = %d  (delta %+d)" % (len(nb), len(nb) - len(raw0)))
    print("sha   = %s" % sha(nb))

    print("\n== STEP 3 · 自检 ==")
    fin = open(PD, encoding="utf-8").read()
    cr = []

    def chk(t, c, d=""):
        print("[%s] %-40s %s" % ("PASS" if c else "FAIL", t, d))
        cr.append(c)

    chk("草案头未变（前 16 行逐字）",
        "".join(lines[:16]) == "".join(fin.splitlines(True)[:16]))
    chk("D-13 状态块原文零丢失（逐字仍在）",
        status_text.strip() in fin)
    chk("D-13 原始正文块原文零丢失（逐字仍在，缩进容差）",
        all(s.strip() in fin for s in orig_text.splitlines() if s.strip()))
    chk("已裁决记录段含「D-13 已裁决（2026-11-12）」", "D-13 已裁决（2026-11-12）" in fin)
    chk("N10-C04 仍待裁且存在", "N10-C04" in fin)
    chk("真机未授权声明在案", "真机发射 / 活进程采集仍未授权" in fin or "真机/活进程须**当轮明示**" in fin or "真机发射/活进程采集**一律不得执行" in fin)
    chk("UTF-8 无替换字符", fin.count("\ufffd") == 0, "fffd=%d" % fin.count("\ufffd"))
    # D-14 条目仍在
    chk("D-14 条目仍在", "D-14 已同步状态" in fin)

    print("\n==== RESULT: %s ====" % ("ALL PASS" if all(cr) else "HAS FAILURE"))
    return 0 if all(cr) else 1


if __name__ == "__main__":
    sys.exit(main())
