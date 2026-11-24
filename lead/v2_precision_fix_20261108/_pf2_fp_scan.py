# -*- coding: utf-8 -*-
# _pf2_fp_scan.py —— 精度事项复核：指纹 + 定位实读。只读，不写任何被核对象。
import hashlib, re

BASE = r"D:\Project\ra2-campaign-forge"
FILES = [
    ("v2_n4v2",   BASE + r"\lead\n4_yi_final_20261108\_n4v2_B_EXECUTION_SPEC_V2.md"),
    ("v2_yi",     BASE + r"\lead\n4_yi_final_20261108\B_EXECUTION_SPEC_V2_YI.md"),
    ("resign",    BASE + r"\lead\n4_yi_final_20261108\CANDIDATE_RESIGN_YES_V2.md"),
    ("matrix",    BASE + r"\lead\b2b_design_20261106\STATE_MATRIX.json"),
    ("cand",      BASE + r"\lead\b2b_candidate_lf_20261107\qc151_trip.candidate_lf.py"),
    ("diff",      BASE + r"\lead\b2b_candidate_lf_20261107\CANDIDATE_LF.diff"),
    ("ledger_pd", BASE + r"\lead\PENDING_DECISIONS.md"),
    ("ledger_gt", BASE + r"\lead\GOAL_THREE_TARGETS_20261018.md"),
]
D = {}
for k, p in FILES:
    with open(p, "rb") as f:
        b = f.read()
    D[k] = b
    print("[FP] %-9s bytes=%-7d SHA256 = %s" % (k, len(b), hashlib.sha256(b).hexdigest()))
print("")

def L(k):
    return D[k].decode("utf-8", errors="replace").splitlines()

def dump(k, a, b):
    l = L(k)
    print("---- %s :%d-%d ----" % (k, a, b))
    for i in range(a - 1, min(b, len(l))):
        print("%d: %s" % (i + 1, l[i]))

# ---- 0) 定位哪份是「V2」（210 行、:91 = 允许范围句）----
v2key = None
for k in ("v2_n4v2", "v2_yi"):
    ls = L(k)
    mark = ""
    if len(ls) >= 91 and ("允许范围" in ls[90]):
        v2key = k
        mark = "   <== :91 含「允许范围」"
    print("[V2ID] %s totalLines=%d :91=%s%s" % (k, len(ls), (ls[90][:50] if len(ls) > 90 else "<SHORT>"), mark))
if v2key is None:
    for k in ("v2_n4v2", "v2_yi"):
        for i, t in enumerate(L(k)):
            if "删除行数" in t:
                v2key = k
                print("[V2ID-fallback] %s:%d 命中「删除行数」" % (k, i + 1))
                break
        if v2key:
            break
print("[V2ID] chosen = %s" % v2key)
print("")

# ---- 1) V2 关键区段 ----
dump(v2key, 76, 101)
print("")
print("==== %s 全文 grep：删除 / 255 / STATE_MATRIX / 措辞 / 4643 / 4648 ====" % v2key)
for i, t in enumerate(L(v2key)):
    if any(s in t for s in ("删除", "255", "STATE_MATRIX", "措辞", "4643", "4648")):
        print("%d: %s" % (i + 1, t[:240]))
print("")

# ---- 2) 重签件 grep ----
rl = L("resign")
print("==== resign totalLines=%d；grep：删除/精度/过宽/STATE_MATRIX/矩阵/4643/4648/255 ====" % len(rl))
for i, t in enumerate(rl):
    if any(s in t for s in ("删除", "精度", "过宽", "STATE_MATRIX", "矩阵", "4643", "4648", "255")):
        print("%d: %s" % (i + 1, t[:240]))
print("")

# ---- 3) 两件台账 grep（登记处定位，只读）----
for k in ("ledger_pd", "ledger_gt"):
    ls2 = L(k)
    hits = [(i + 1, t) for i, t in enumerate(ls2)
            if any(s in t for s in ("删除行数", "措辞过宽", "精度事项"))]
    print("==== %s（totalLines=%d）hits=%d ====" % (k, len(ls2), len(hits)))
    for n, t in hits[:15]:
        print("%d: %s" % (n, t[:200]))
print("")

# ---- 4) STATE_MATRIX.json 带行号全文 ----
dump("matrix", 1, 40)
print("")

# ---- 5) 候选 :4600-4680 分支顺序 ----
dump("cand", 4600, 4680)
print("")
print("==== cand grep：read_error 行号（前 30）====")
cnt = 0
for i, t in enumerate(L("cand")):
    if "read_error" in t:
        print("%d: %s" % (i + 1, t[:160]))
        cnt += 1
        if cnt >= 30:
            break
print("")

# ---- 6) CANDIDATE_LF.diff 解析：hunk 数 / +行 / -行 / 老侧区间 ----
dl = D["diff"].decode("utf-8", errors="replace").splitlines()
print("==== diff 头 3 行 ====")
for t in dl[:3]:
    print("   %s" % t[:120])
stats = []
cur = None
for t in dl:
    if t.startswith("@@"):
        cur = {"h": t, "m": 0, "p": 0}
        stats.append(cur)
        continue
    if cur is None:
        continue
    if t.startswith("-"):
        cur["m"] += 1
    elif t.startswith("+"):
        cur["p"] += 1
tot_m = sum(s["m"] for s in stats)
tot_p = sum(s["p"] for s in stats)
print("[DIFF] hunks=%d total_plus=%d total_minus=%d" % (len(stats), tot_p, tot_m))
E_OLD = set(range(5984, 5991))
for i, s in enumerate(stats, 1):
    m = re.search(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))?", s["h"])
    if m:
        o0 = int(m.group(1)); o1 = o0 + (int(m.group(2)) if m.group(2) else 1) - 1
        hit = sorted(E_OLD & set(range(o0, o1 + 1)))
        print("[DIFF] hunk%02d  -%d/+%d  old=%d-%d new=%s  E块5984-5990命中=%s"
              % (i, s["m"], s["p"], o0, o1, m.group(3), hit if hit else "无"))
    else:
        print("[DIFF] hunk%02d  -%d/+%d  %s" % (i, s["m"], s["p"], s["h"][:70]))
