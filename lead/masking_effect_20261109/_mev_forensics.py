# -*- coding: utf-8 -*-
"""_mev_forensics.py — corpus-drift forensics + :22 codepoint check.

Ask 2: my independent re-run gave scanned=643 / 87 / 136, author recorded
637 / 79 / 122. Determine whether the delta is fully explained by .md files
created/modified AFTER the author's repro snapshot (14:15 on 2026-11-09).

Also independently verifies ask-1b claims about _ve_DRAFT_S609.md:22.
Read-only outside this write domain. Outputs _mev_ prefixed.
"""
import os, io, datetime, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"

def ts(t):
    return datetime.datetime.fromtimestamp(t).strftime("%Y-%m-%d %H:%M:%S")

def iter_md():
    for dp, dn, fn in os.walk(LEAD):
        rel = os.path.relpath(dp, LEAD).replace("\\", "/")
        depth = 0 if rel == "." else rel.count("/") + 1
        if depth > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            if not os.path.isfile(p):
                continue
            try:
                b = open(p, "rb").read()
            except OSError:
                continue
            if b"\x00" in b:
                continue
            yield os.path.relpath(p, LEAD).replace("\\", "/"), p, b, os.stat(p).st_mtime

def counts(b):
    t = b.decode("utf-8", "replace")
    lines = t.splitlines()
    n1 = sum(1 for L in lines if N1 in L)
    n2 = sum(1 for L in lines if N2 in L)
    un = sum(1 for L in lines if N1 in L or N2 in L)
    return n1, n2, un

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    P("=== CORPUS DRIFT FORENSICS (ask 2) ===")
    allf = list(iter_md())
    P("current scannable .md (depth<=2) = %d" % len(allf))
    carriers = [(rel, p, b, mt, counts(b)) for rel, p, b, mt in allf if counts(b)[2] > 0]
    P("files containing >=1 needle line = %d" % len(carriers))
    P("current totals: N1-lines=%d N2-lines=%d UNION-lines=%d" % (
        sum(c[4][0] for c in carriers), sum(c[4][1] for c in carriers),
        sum(c[4][2] for c in carriers)))
    P("")
    P("--- carrier files by mtime (N1-lines, N2-lines, UNION-lines) ---")
    for rel, p, b, mt, (n1, n2, un) in sorted(carriers, key=lambda x: x[3]):
        P("  %s  %s  n1=%-4d n2=%-4d un=%-4d  %s" % (
            ts(mt), "OLD" if mt <= CUT else "NEW", n1, n2, un, rel))
    P("")
    # author repro snapshot: 14:15:00 local; design run at 14:25 showed 638
    old = [c for c in carriers if c[3] <= CUT]
    new = [c for c in carriers if c[3] > CUT]
    P("CUT = %s" % ts(CUT))
    P("carrier files OLD(<=cut) = %d ; NEW(>cut) = %d" % (len(old), len(new)))
    P("OLD totals: N1=%d N2=%d UNION=%d" % (
        sum(c[4][0] for c in old), sum(c[4][1] for c in old), sum(c[4][2] for c in old)))
    P("NEW totals: N1=%d N2=%d UNION=%d" % (
        sum(c[4][0] for c in new), sum(c[4][1] for c in new), sum(c[4][2] for c in new)))
    n_old_files = sum(1 for rel, p, b, mt in allf if mt <= CUT)
    P("ALL .md files <= CUT = %d  (author recorded scanned files = 637)" % n_old_files)
    P("")
    P("=== :22 independent verification (ask 1b) ===")
    p22 = os.path.join(LEAD, "s604_verdict_entry_20261109", "_ve_DRAFT_S609.md")
    lines = io.open(p22, encoding="utf-8", errors="replace").read().splitlines()
    L22 = lines[21]
    P("line22 len = %d" % len(L22))
    P("N1 find = %d ; N2 find = %d" % (L22.find(N1), L22.find(N2)))
    P("normalized variant find = %d" % L22.find("只能判『不可复现』"))
    P("CONTAINS_BOTH_VERBATIM = %s" % (N1 in L22 and N2 in L22))
    frag = "「只能判『不可复现』、不能定位当年错误步骤」"
    P("outer fragment found at = %d" % L22.find(frag))
    cps = sorted({hex(ord(ch)) for ch in L22 if ord(ch) > 0x2fff and ord(ch) < 0x3100})
    P("CJK punctuation codepoints present = %s" % ", ".join(cps))
    P("N1 quotes = %s ; variant quotes = %s" % (
        [hex(ord(c)) for c in N1 if ord(c) in (0x300c, 0x300d, 0x300e, 0x300f)],
        [hex(ord(c)) for c in "只能判『不可复现』" if ord(c) in (0x300c, 0x300d, 0x300e, 0x300f)]))
    P("N3 '登记效力说明' find = %d ; '与既有草案' find = %d" %
      (L22.find("登记效力说明"), L22.find("与既有草案")))
    P("")
    io.open(os.path.join(HERE, "_mev_forensics_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

CUT = datetime.datetime(2026, 11, 9, 14, 15, 0).timestamp()

if __name__ == "__main__":
    main()
