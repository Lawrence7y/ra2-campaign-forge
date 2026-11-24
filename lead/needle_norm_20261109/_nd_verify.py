# -*- coding: utf-8 -*-
"""_nd_verify.py — 本轮独立量化（不改任何既有件）。
口径：lead/ depth<=2 *.md，排除整个 needle_norm_20261109/ 写域。
零真机 / 零采样代码 / 只读语料；输出仅 stdout。"""
import os, re, sys, importlib.util, hashlib

ROOT = r"D:/Project/ra2-campaign-forge/lead"
SCAN = r"D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rs_carrier_scan.py"
CANON = "只能判「不可复现」"
VARIANTS = {
    "angle_corner": "只能判「不可复现」",
    "curly_corner": "只能判『不可复现』",
    "curly_double": "只能判“不可复现”",
    "no_quote":     "只能判不可复现",
    "half_paren":   "只能判(不可复现)",
    "no_punct":     "只能判 不可复现",
}

def files():
    out = []
    for dp, dn, fn in os.walk(ROOT):
        rel = os.path.relpath(dp, ROOT).replace(os.sep, "/")
        d = 0 if rel == "." else rel.count("/") + 1
        if d > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            r = os.path.relpath(p, ROOT).replace(os.sep, "/")
            if r.startswith("needle_norm_20261109/"):
                continue
            out.append((p, r))
    return out

LINES = {}
for p, r in files():
    b = open(p, "rb").read()
    if b"\x00" in b:
        continue
    LINES[r] = b.decode("utf-8", "replace").splitlines()
print("scanned files (excl entire needle_norm_20261109/ write domain) =", len(LINES))

sets = {}
for k, nd in VARIANTS.items():
    s = {(r, i) for r, ls in LINES.items() for i, L in enumerate(ls, 1) if nd in L}
    sets[k] = s
    print("  %-14s files=%2d lines=%2d" % (k, len({r for r, i in s}), len(s)))
U = set().union(*sets.values())
B = sets["angle_corner"]
print("  angle only: files=%d lines=%d" % (len({r for r, i in B}), len(B)))
print("  union(6)  : files=%d lines=%d" % (len({r for r, i in U}), len(U)))
missed_files = {r for r, i in U} - {r for r, i in B}
print("  missed files=%d (%.2f%%) lines=%d (%.2f%%)" % (
    len(missed_files), 100.0 * len(missed_files) / len({r for r, i in U}),
    len(U - B), 100.0 * len(U - B) / len(U)))
print("  missed file list =", sorted(missed_files))
print("  baseline recall lines=%.2f%% files=%.2f%%" % (
    100.0 * len(B) / len(U), 100.0 * len({r for r, i in B}) / len({r for r, i in U})))
print("  variant-line pairs sum=%d ; distinct union lines=%d ; overlap=%d" % (
    sum(len(s) for s in sets.values()), len(U), sum(len(s) for s in sets.values()) - len(U)))
THREE = sets["angle_corner"] | sets["curly_corner"] | sets["curly_double"]
print("  three quote variants: files=%d lines=%d" % (len({r for r, i in THREE}), len(THREE)))
print("  residual U-L1(no_quote etc): lines=%d files=%d" % (len(U - THREE), len({r for r, i in U - THREE})))

# L1: only normalize quote-class characters, 1:1 length preserving
OPEN_Q, CLOSE_Q, SYM_Q = "\x01", "\x02", "\x03"
QO, QC, SYM = "「『“‘", "」』”’", "`\"'"
def norm(s):
    out = []
    for c in s:
        out.append(OPEN_Q if c in QO else CLOSE_Q if c in QC else SYM_Q if c in SYM else c)
    return "".join(out)
QN = norm(CANON)
l1 = set(); mapped = 0; bad = 0
for r, ls in LINES.items():
    for i, L in enumerate(ls, 1):
        n = norm(L)
        pos = 0
        while True:
            k = n.find(QN, pos)
            if k < 0:
                break
            a, b = k, k + len(QN)
            if L[a:b] != n[a:b] and L[a:b] != L[a:b]:  # unreachable; keeps explicit
                bad += 1
            if norm(L[a:b]) != QN:
                bad += 1
            mapped += 1
            l1.add((r, i))
            pos = k + 1
print("  L1 norm key =", repr(QN))
print("  L1: files=%d lines=%d ; L1==three_quote_union? %s ; FP=%d FN=%d" % (
    len({r for r, i in l1}), len(l1), l1 == THREE, len(l1 - THREE), len(THREE - l1)))
print("  L1 mapped hits=%d ; length-preserving/orig-slice bad=%d" % (mapped, bad))

# widenet
W1 = {(r, i) for r, ls in LINES.items() for i, L in enumerate(ls, 1) if "不可复现" in L}
W2 = {(r, i) for r, ls in LINES.items() for i, L in enumerate(ls, 1) if "只能判" in L}
W3 = W1 & W2
W4 = {(r, i) for r, ls in LINES.items() for i, L in enumerate(ls, 1)
      if re.search(r"只能判.{0,3}不可复现", L)}
SUPP = {(r, i) for r, ls in LINES.items() for i, L in enumerate(ls, 1)
        if re.search(r"只能判[「『“(]?不可复现[」』”)]?", L)}
for nm, s in (("W1", W1), ("W2", W2), ("W3", W3), ("W4", W4), ("SUPP", SUPP), ("L1|SUPP", l1 | SUPP)):
    print("  %-8s lines=%3d files=%2d" % (nm, len(s), len({r for r, i in s})))
print("  U-W3=%d W3-U=%d U-W4=%d W4-U=%d W1-U=%d (contain 只能判=%d)" % (
    len(U - W3), len(W3 - U), len(U - W4), len(W4 - U), len(W1 - U),
    sum(1 for r, i in W1 - U if "只能判" in LINES[r][i - 1])))

# auto-discovery of (pre,post) classes + coverage-matrix difference
disc = {}
for r, ls in LINES.items():
    for i, L in enumerate(ls, 1):
        for m in re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L):
            key = (m.group(1), m.group(2))
            disc.setdefault(key, [0, (r, i)])
            disc[key][0] += 1
print("  discovered (pre,post) classes =", len(disc))
for k in sorted(disc, key=lambda x: (-disc[x][0], x)):
    print("     pre=%-8r post=%-8r count=%-3d anchor=%s:%d" % (k[0], k[1], disc[k][0], *disc[k][1]))
# controls: 6 checks from _rs_carrier_scan.py:332-339 mapped to their (pre,post)
ctrl = set()
for r, n, _ in [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, "ASSERTION"),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25, "ASSERTION"),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196, "ASSERTION"),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129, "ASSERTION"),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22, "REFUTING_QUOTE"),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, "ASSERTION"),
]:
    L = LINES[r][n - 1]
    for m in re.finditer(r"只能判(.{0,4}?)不可复现(.{0,2})", L):
        ctrl.add((m.group(1), m.group(2)))
print("  covered classes by 6 existing controls =", len(ctrl), sorted(ctrl))
print("  GATE discovered=%d covered=%d DIFF=%d -> %s" % (
    len(disc), len(ctrl), len(set(disc) - ctrl), "FAIL" if set(disc) - ctrl else "PASS"))

# L1 mis-merge counterexamples: independent direct import of classify_line/spans_of_quotes
spec = importlib.util.spec_from_file_location("_rs_mod", SCAN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
CASES = [
    ("V4 half-mismatched", "只能判「不可复现」", "只能判『不可复现」"),
    ("V5 single curly",    "只能判「不可复现」", "只能判‘不可复现’"),
    ("V1 core word",       "只能判「不可复现」", "只能判「不可复原」"),
    ("V3 no quote",        "只能判「不可复现」", "只能判不可复现"),
]
print("=== L1 mis-merge / boundary counterexamples (direct import) ===")
for nm, A, Bx in CASES:
    kA, kB = norm(A), norm(Bx)
    hA, hB = QN in kA, QN in kB
    spansA, spansB = mod.spans_of_quotes(A), mod.spans_of_quotes(Bx)
    rA = mod.classify_line(A, [CANON], "") if False else None
    print("  %-20s keyA=%r keyB=%r FULL_KEY_MERGED=%s find_norm(A)=%s find_norm(B)=%s spansA=%s spansB=%s" % (
        nm, kA, kB, kA == kB, hA, hB, spansA, spansB))
# role on original line, with the matched literal as needle
for s in ("只能判『不可复现」", "只能判‘不可复现’", "只能判「不可复现」"):
    c = mod.classify_line(s, [s], "")
    print("  classify_line(%r, needle=itself) -> %s" % (s, c["role"] if c else None))

# sentinel presence (whole corpus, excl write domain)
hits = []
for r, ls in LINES.items():
    p = os.path.join(ROOT, r)
    b = open(p, "rb").read()
    f = [x for x in (b"\x01", b"\x02", b"\x03") if x in b]
    if f:
        hits.append((r, f))
print("=== sentinel presence ===")
print("  files containing sentinel bytes =", len(hits), hits[:5])
