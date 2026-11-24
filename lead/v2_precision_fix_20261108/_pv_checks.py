# -*- coding: utf-8 -*-
# _pv_checks.py —— 复核员独立计算。全部只读（rb 读取），不 import 候选，不执行被核代码。
import difflib
import hashlib
import re

BASE = r"D:\Project\ra2-campaign-forge"

def rd(p):
    with open(p, "rb") as f:
        return f.read()

def rdt(p):
    return rd(p).decode("utf-8", errors="replace")

V2 = BASE + r"\lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md"
R3 = BASE + r"\lead\b2b_candidate_review3_20261107\CANDIDATE_SEMANTIC_REVIEW_R3.md"
DIF = BASE + r"\lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff"
CAND = BASE + r"\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"
MOT = BASE + r"\out\re_work\work_chain\CONTINUE_20261003\lead\qc151_u0400_trip\qc151_trip.py"
B2B = BASE + r"\lead\b2b_design_20261106\B2B_DESIGN.md"
LPD = BASE + r"\lead\PENDING_DECISIONS.md"
LGT = BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md"
RESIGN = BASE + r"\lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md"

# ---- A) V2 / R3 / 重签件 行数与关键行复读 ----
v2l = rdt(V2).splitlines()
r3l = rdt(R3).splitlines()
rl = rdt(RESIGN).splitlines()
print("[A] V2 lines=%d  R3 lines=%d  resign lines=%d" % (len(v2l), len(r3l), len(rl)))
print("[A] V2:91 = %s" % v2l[90])
print("[A] V2:100 = %s" % v2l[99])
print("[A] resign:34 = %s" % rl[33])

# ---- B) CANDIDATE_LF.diff 解析 ----
dl = rdt(DIF).splitlines()
V2_HDRS = [
    ("H01", "-212,6 +212,21"), ("H02", "-4458,6 +4473,10"),
    ("H03", "-4558,8 +4577,131"), ("H04", "-4572,20 +4714,105"),
    ("H05", "-5906,7 +6133,8"), ("H06", "-5936,7 +6164,8"),
    ("H07", "-6294,6 +6523,9"), ("H08", "-6386,6 +6618,15"),
    ("H09", "-7122,7 +7363,8"),
]
hunks = []
cur = None
for t in dl:
    if t.startswith("@@"):
        cur = {"h": t, "m": 0, "p": 0}
        hunks.append(cur)
    elif cur is not None:
        if t.startswith("-"):
            cur["m"] += 1
        elif t.startswith("+"):
            cur["p"] += 1
print("[B] hunks=%d total_minus=%d total_plus=%d" % (
    len(hunks), sum(x["m"] for x in hunks), sum(x["p"] for x in hunks)))
E_OLD = set(range(5984, 5991))
for i, h in enumerate(hunks):
    m = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?", h["h"])
    o0 = int(m.group(1)); oc = int(m.group(2)) if m.group(2) else 1
    o1 = o0 + oc - 1
    exp_h, exp_rng = V2_HDRS[i]
    rng_txt = "-%d,%d +%d,%s" % (o0, oc, int(m.group(3)), m.group(4) or "1")
    ok = (rng_txt.split(" ")[0] + " " + rng_txt.split(" ")[1]) == exp_rng
    hit = sorted(E_OLD & set(range(o0, o1 + 1)))
    print("[B] %s  del=%-2d add=%-3d old=%d-%d  hdr=%s  V2表头=%s  匹配=%s  E块命中=%s"
          % (exp_h, h["m"], h["p"], o0, o1, rng_txt, exp_rng, ok, hit if hit else "无"))

# ---- C) difflib 全量重算（autojunk=False 与 True 各一次）----
a = rdt(MOT).splitlines()
c = rdt(CAND).splitlines()
print("[C] mother lines=%d candidate lines=%d net=%d" % (len(a), len(c), len(c) - len(a)))
for aj in (False, True):
    sm = difflib.SequenceMatcher(None, a, c, autojunk=aj)
    dele = ins = blocks = 0
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag in ("delete", "replace"):
            dele += i2 - i1
        if tag in ("insert", "replace"):
            ins += j2 - j1
        if tag in ("delete", "insert", "replace"):
            blocks += 1
    print("[C] autojunk=%s: changed_blocks=%d deletions=%d insertions=%d" % (aj, blocks, dele, ins))

# ---- D) 台账 8 词检索（带行号）----
TERMS = ["删除行数", "措辞过宽", "精度事项", "R3:47", "4643", "4648", "JSON:2", "重签"]
for name, p in (("ledger_pd", LPD), ("ledger_gt", LGT)):
    ll = rdt(p).splitlines()
    print("[D] %s lines=%d" % (name, len(ll)))
    tot = 0
    for term in TERMS:
        hits = [(i + 1, t) for i, t in enumerate(ll) if term in t]
        tot += len(hits)
        if hits:
            for n, t in hits[:6]:
                print("[D]   %r -> %d: %s" % (term, n, t[:150]))
        else:
            print("[D]   %r -> 0" % term)
    print("[D]   subtotal hits=%d" % tot)

# ---- E) B2B_DESIGN.md 措辞 grep ----
bl = rdt(B2B).splitlines()
for term in ("任意文件状态", "跑后任意"):
    hits = [i + 1 for i, t in enumerate(bl) if term in t]
    print("[E] B2B_DESIGN.md %r hits=%s" % (term, hits))
print("[E] B2B:148 = %s" % bl[147])
print("[E] B2B:151 = %s" % bl[150])
print("[E] B2B:310 = %s" % bl[309])
print("[E] B2B:311 = %s" % bl[310])

# ---- F) 矩阵 :2/:5 行逐字 + R3:31/:43/:44/:47 关键词自证 ----
mx = rdt(BASE + r"\lead\b2b_design_20261106\STATE_MATRIX.json").splitlines()
print("[F] JSON:2 = %s" % mx[1])
print("[F] JSON:5 = %s" % mx[4])
for n in (31, 43, 44, 47):
    print("[F] R3:%d = %s" % (n, r3l[n - 1][:200]))

# ---- G) 候选关键行逐字自证 ----
cl = rdt(CAND).splitlines()
for n in (4634, 4642, 4643, 4644, 4648, 4649, 4786):
    print("[G] cand:%d = %s" % (n, cl[n - 1][:150]))
