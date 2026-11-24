# -*- coding: utf-8 -*-
"""_writer_table.py — 生成 §3 完整表（4 件 × A/B/C × 8 项 = 96 行）
证据源 = _ak_runs.jsonl（本会话重跑后 108 行）逐行 fail_items。
逐格标出 BASE/WA/WB/SENT 的该判定；OR 项说明 AND_k 塌缩点。
"""
import json
import sys
from pathlib import Path

W = Path(r"D:\Project\ra2-campaign-forge\lead\andk_rerun_20261109")
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

runs = [json.loads(l) for l in (W / "_ak_runs.jsonl").read_text(
    encoding="utf-8").splitlines() if l.strip()]

OR_ITEM = {"d27": 6, "d28": 4, "d29": 4, "d30": 4}
ITEMS = {
    "d27": {1: "两文件存在/非空/UTF-8", 2: "^main:(A|B|C)$ 声明行",
            3: "7 个必需二级标题", 4: "新证据是否成立⊇循环论证",
            5: "授权边界⊇本次不授权", 6: "未背书⊇外推 OR 卡顿不存在（OR 项）",
            7: "裁决书引用≥8 处", 8: "FACTCHECK⊇selfBias"},
    "d28": {1: "两文件存在/非空/UTF-8", 2: "q1/q2 恰一行合法声明",
            3: "7 个必需小节", 4: "D 链处置⊇历史数字 OR 1681（OR 项）",
            5: "授权边界⊇本次不授权", 6: "未背书 AND 词表(外推,口径 B)",
            7: "裁决书引用≥8 处", 8: "FACTCHECK⊇selfBias"},
    "d29": {1: "两文件存在/非空/UTF-8", 2: "q1 恰一行合法声明",
            3: "7 个必需小节", 4: "冲突是否成立⊇互斥 OR 前提（OR 项）",
            5: "授权边界⊇本次不授权", 6: "未背书 AND 词表(口径 B,外推,191)",
            7: "裁决书引用≥8 处", 8: "FACTCHECK⊇selfBias"},
    "d30": {1: "两文件存在/非空/UTF-8", 2: "q1 恰一行合法声明",
            3: "7 个必需小节", 4: "三档权衡的实质⊇93.98 OR 误报率（OR 项）",
            5: "授权边界⊇本次不授权", 6: "未背书 AND 词表(外推,栈采样)",
            7: "裁决书引用≥8 处", 8: "FACTCHECK⊇selfBias"},
}
NEEDLE = {"d27": ("外推", "卡顿不存在"), "d28": ("历史数字", "1681"),
          "d29": ("互斥", "前提"), "d30": ("93.98", "误报率")}
INJ_MUT = {1: "I1", 2: "I2", 3: "I3", 4: "I4LIT", 5: "I5",
           6: "I6AND", 7: "I7", 8: "I8"}
# d27[4] uses I4LIT; d27[6] OR; others [4] OR, [6] I6AND
INJ_OF = {}
for g in OR_ITEM:
    for n in range(1, 9):
        if n == OR_ITEM[g]:
            INJ_OF[(g, n)] = "OR_BOTH（两词全删）"
        elif g == "d27" and n == 4:
            INJ_OF[(g, n)] = "I4LIT（删『循环论证』）"
        elif g != "d27" and n == 6:
            INJ_OF[(g, n)] = "I6AND（删『外推』）"
        else:
            INJ_OF[(g, n)] = INJ_MUT[n]


def rec(gate, label, variant):
    for r in runs:
        if r["gate"] == gate and r["exp"] == "abc_%s" % label + (
                "" if variant == "BASE" else "_" + variant) and r["tag"].startswith("ABC_"):
            if variant == "BASE" and r["tag"] == "ABC_ORIGINAL":
                return r
            if variant != "BASE" and r["tag"] == {"WA": "ABC_WORDA",
                                                  "WB": "ABC_WORDB",
                                                  "SENT": "ABC_SENTINEL"}[variant]:
                return r
    return None


def status(r, item):
    return "FAIL" if item in r["fail_items"] else "PASS"


lines = []
lines.append("| gate | 输入 | 项 | 检查内容 | BASE(原件) | WA(只查第一词) | WB(只查第二词) | SENT(零命中哨兵) | 该格依据 |")
lines.append("|---|---|---|---|---|---|---|---|---|")
for g in ("d27", "d28", "d29", "d30"):
    for label in ("A", "B", "C"):
        b = rec(g, label, "BASE")
        wa = rec(g, label, "WA")
        wb = rec(g, label, "WB")
        se = rec(g, label, "SENT")
        for n in range(1, 9):
            cells = [status(b, n), status(wa, n), status(wb, n), status(se, n)]
            ev = ("EXIT=%d fail_items=%r" % (b["exit"], b["fail_items"]))
            if n == OR_ITEM[g]:
                ev += ("；WA/WB/SENT EXIT=%d/%d/%d，P_WA=%s P_WB=%s" %
                       (wa["exit"], wb["exit"], se["exit"],
                        status(wa, n) == "PASS", status(wb, n) == "PASS"))
            lines.append("| %s | %s | [%d] | %s | %s | %s | %s | %s | `%s` |" %
                         (g, label, n, ITEMS[g][n], cells[0], cells[1],
                          cells[2], cells[3], ev))
(W / "_writer_96_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

# 汇总：每 gate × input 的 8 项通过计数 + AND_k
sm = []
sm.append("| gate | 输入 | BASE 8 项 PASS 数 | WA | WB | SENT | AGGREGATE=AND_k | BAD_NEEDLE_CAUGHT | DISTINGUISHABLE_PASS |")
sm.append("|---|---|---|---|---|---|---|---|---|")
s = json.loads((W / "_ak_summary.json").read_text(encoding="utf-8"))
for g in ("d27", "d28", "d29", "d30"):
    for label in ("A", "B", "C"):
        b, wa, wb, se = (rec(g, label, v) for v in ("BASE", "WA", "WB", "SENT"))
        cnt = lambda r: sum(1 for n in range(1, 9) if status(r, n) == "PASS")
        row = next(x for x in s["abc"] if x["gate"] == g and x["input"] == label)
        sm.append("| %s | %s | %d/8 | %d/8 | %d/8 | %d/8 | **%s** | %s | **%s** |" %
                  (g, label, cnt(b), cnt(wa), cnt(wb), cnt(se),
                   row["and_k"], row["bad_needle_caught"],
                   row["distinguishable_pass"]))
(W / "_writer_96_summary.md").write_text("\n".join(sm) + "\n", encoding="utf-8")
print("WROTE _writer_96_table.md rows=%d ; _writer_96_summary.md rows=%d" %
      (len(lines) - 2, len(sm) - 2))
