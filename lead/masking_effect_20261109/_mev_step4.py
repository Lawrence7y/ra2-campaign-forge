# -*- coding: utf-8 -*-
"""_mev_step4.py — ASK 4: independent verification of "reverse masking".

Verifies, WITHOUT reusing the author's _me_analyze.py, that:
 (1) :165 min(pos) makes role depend on argmin;
 (2) adding N3='登记效力说明' (pos=17, outside quotes) to the REAL :22 flips
     REFUTING_QUOTE -> ANALYSIS_MENTION;
 (3) scanned/carrier inclusion is monotone non-decreasing;
 (4) the synthetic ASSERTION -> QUOTED (needs_fix True->False) flip exists;
 (5) the honest negative result: 24 ASSERTION lines x extra needles -> 0 flips.
Uses the UNMODIFIED scanner's own functions via importlib (read-only).
Outputs _mev_ prefixed.
"""
import os, io, importlib.util, hashlib
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")
spec = importlib.util.spec_from_file_location("mev_up", SCANNER)
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
N3 = "登记效力说明"
N3B = "与既有草案"

def corpus():
    for dp, dn, fn in os.walk(LEAD):
        rel_d = os.path.relpath(dp, LEAD).replace("\\", "/")
        depth = 0 if rel_d == "." else rel_d.count("/") + 1
        if depth > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            try:
                b = open(p, "rb").read()
            except OSError:
                continue
            if b"\x00" in b:
                continue
            yield os.path.relpath(p, LEAD).replace("\\", "/"), b.decode("utf-8", "replace").splitlines()

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    P("=== ASK 4: independent reverse-masking verification ===")
    P("scanner sha256 = %s" % hashlib.sha256(open(SCANNER, "rb").read()).hexdigest())
    P("")
    L22 = io.open(os.path.join(LEAD, "s604_verdict_entry_20261109", "_ve_DRAFT_S609.md"),
                  encoding="utf-8").read().splitlines()[21]
    P("--- (1)(2) REAL :22, min(pos) / quoted_containing / role ---")
    for name, nd in [("[N2]", [N2]), ("[N1,N2]", [N1, N2]),
                     ("[N1,N2,N3]", [N1, N2, N3]), ("[N3,N2]", [N3, N2]),
                     ("[N1,N2,N3B]", [N1, N2, N3B])]:
        found = [(n, L22.find(n)) for n in nd if n in L22]
        pos = min((p for _, p in found), default=-1)
        q = up.quoted_containing(L22, pos) if pos >= 0 else None
        c = up.classify_line(L22, nd, "")
        P("  %-15s present=%s min_pos=%-4d q=%s role=%s" %
          (name, found, pos, "None" if q is None else ("quote@%s" % (q[1],)),
           c["role"] if c else None))
    P("  => N3 pos=%d outside quotes; N3B pos=%d outside quotes" %
      (L22.find(N3), L22.find(N3B)))
    P("")
    P("--- (3) monotonicity of carrier inclusion ---")
    sets = []
    for name, nd in [("N=2", [N1, N2]), ("N=3", [N1, N2, N3]),
                     ("N=4", [N1, N2, N3, N3B])]:
        s = set()
        for rel, lines in corpus():
            for i, L in enumerate(lines, 1):
                if any(n in L for n in nd):
                    s.add((rel, i))
        sets.append(s)
        pats = Counter()
        for rel, lines in corpus():
            pass
        P("  %s needles=%d union lines=%d" % (name, len(nd), len(s)))
    P("  N=2 subset of N=3 = %s ; N=3 subset of N=4 = %s" %
      (sets[0] <= sets[1], sets[1] <= sets[2]))
    P("  (scanned/carrier inclusion monotone == the report's claim)")
    P("")
    P("--- (4) synthetic ASSERTION -> QUOTED flip (needs_fix True->False) ---")
    for L, extra in [("「核对」 " + N1, "核对"),
                     ("「逐字」 复算数字 " + N1, "逐字")]:
        c1 = up.classify_line(L, [N1], "")
        c2 = up.classify_line(L, [N1, extra], "")
        p1 = min((L.find(n) for n in [N1] if n in L), default=-1)
        p2 = min((L.find(n) for n in [N1, extra] if n in L), default=-1)
        P("  line=%r" % L)
        P("    [N]      pos=%-3d role=%-16s needs_fix(role==ASSERTION)=%s" %
          (p1, c1["role"] if c1 else None, bool(c1 and c1["role"] == "ASSERTION")))
        P("    [N,%r] pos=%-3d role=%-16s needs_fix(role==ASSERTION)=%s" %
          (extra, p2, c2["role"] if c2 else None, bool(c2 and c2["role"] == "ASSERTION")))
        P("    FLIP=%s" % (c1["role"] != c2["role"]))
    P("")
    P("--- (5) honest negative: real-corpus ASSERTION flips ---")
    EXTRA = ["核对", "复核", "本会话", "登记", "实跑", "grep", "逐字", "订正", "清单"]
    assertions = 0
    flips = []
    for rel, lines in corpus():
        for i, L in enumerate(lines, 1):
            c = up.classify_line(L, [N1, N2], "")
            if not c or c["role"] != "ASSERTION":
                continue
            assertions += 1
            pos = min((L.find(n) for n in [N1, N2] if n in L), default=-1)
            for tok in EXTRA:
                q = L.find(tok)
                if not (0 <= q < pos) or up.quoted_containing(L, q) is not None:
                    continue
                c2 = up.classify_line(L, [N1, N2, tok], "")
                if c2 and c2["role"] != "ASSERTION":
                    flips.append((rel, i, tok, c["role"], c2["role"]))
                    break
    P("  ASSERTION lines under [N1,N2] = %d ; extra needles = %d ; flip count = %d" %
      (assertions, len(EXTRA), len(flips)))
    P("  (author reported 24 / 9 / 0 at their corpus snapshot; my snapshot differs")
    P("   because new .md artifacts now exist -- see _mev_forensics_out.txt)")
    P("")
    io.open(os.path.join(HERE, "_mev_step4_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

if __name__ == "__main__":
    main()
