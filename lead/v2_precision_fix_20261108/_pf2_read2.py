# -*- coding: utf-8 -*-
# _pf2_read2.py —— 补充证据：V2 :125-141 / :158-175、R3:28-50、N-4 定位、台账复查、difflib 交叉验证。只读。
import hashlib, os, re, difflib

BASE = r"D:\Project\ra2-campaign-forge"
P = {
    "v2":     BASE + r"\lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md",
    "r3":     BASE + r"\lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md",
    "mother": BASE + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py",
    "cand":   BASE + r"\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py",
    "ledger_pd": BASE + r"\lead\PENDING_DECISIONS.md",
    "ledger_gt": BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md",
}

def rd(p):
    with open(p, "rb") as f:
        return f.read().decode("utf-8", errors="replace")

def dump(name, p, a, b):
    l = rd(p).splitlines()
    print("---- %s :%d-%d (total=%d) ----" % (name, a, b, len(l)))
    for i in range(a - 1, min(b, len(l))):
        print("%d: %s" % (i + 1, l[i]))
    print("")

b = open(P["r3"], "rb").read()
print("[FP] r3 bytes=%d SHA256 = %s" % (len(b), hashlib.sha256(b).hexdigest()))
b = open(P["mother"], "rb").read()
print("[FP] mother bytes=%d SHA256 = %s" % (len(b), hashlib.sha256(b).hexdigest()))
print("")

dump("V2", P["v2"], 125, 141)
dump("V2", P["v2"], 155, 175)
dump("R3", P["r3"], 28, 50)

# N-4 原文定位（「删除也须解释」）
print("==== 全 lead 树找「删除也须解释」（深度<=3）====")
root = BASE + r"\lead"
n = 0
for dirpath, dirnames, filenames in os.walk(root):
    depth = dirpath[len(root):].count(os.sep)
    if depth >= 3:
        dirnames[:] = []
        continue
    for fn in filenames:
        if not fn.lower().endswith((".md", ".txt", ".py", ".json")):
            continue
        fp = os.path.join(dirpath, fn)
        try:
            t = rd(fp)
        except Exception:
            continue
        for i, ln in enumerate(t.splitlines()):
            if "删除也须解释" in ln:
                print("%s:%d: %s" % (os.path.relpath(fp, BASE), i + 1, ln[:160]))
                n += 1
                if n >= 8:
                    break
        if n >= 8:
            break
    if n >= 8:
        break
print("(hits=%d)" % n)
print("")

# 台账复查（第二轮词）
for k in ("ledger_pd", "ledger_gt"):
    l = rd(P[k]).splitlines()
    hits = [(i + 1, t) for i, t in enumerate(l)
            if any(s in t for s in ("R3:47", "4643", "4648", "JSON:2", "重签"))]
    print("==== %s（total=%d）第二轮 hits=%d ====" % (k, len(l), len(hits)))
    for nn, t in hits[:10]:
        print("%d: %s" % (nn, t[:180]))
    print("")

# difflib 独立交叉验证：母本 vs 候选
a_lines = rd(P["mother"]).splitlines()
c_lines = rd(P["cand"]).splitlines()
print("[XL] mother lines=%d candidate lines=%d net=%d" % (len(a_lines), len(c_lines), len(c_lines) - len(a_lines)))
sm = difflib.SequenceMatcher(None, a_lines, c_lines, autojunk=True)
dele = ins = 0
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == "delete":
        dele += i2 - i1
    elif tag == "insert":
        ins += j2 - j1
    elif tag == "replace":
        dele += i2 - i1
        ins += j2 - j1
print("[XL] difflib totals: deletions=%d insertions=%d (对照 CANDIDATE_LF.diff 实测 +255/-13)" % (dele, ins))
