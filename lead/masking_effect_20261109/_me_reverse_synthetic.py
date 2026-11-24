# -*- coding: utf-8 -*-
"""_me_reverse_synthetic.py — Step 2(d) minimal synthetic construction.

Shows that adding ONE needle can flip a line's ROLE (and therefore
needs_fix) purely because :165 uses min(pos): the newly added needle hits
earlier, inside a quote span, so quoted_containing() now returns a quote
that it did not return before. This is "reverse masking": more input makes
a previously-detected carrier disappear from the fix list.

Read-only; imports the unmodified scanner.
"""
import os, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
SCANNER = os.path.join(ROOT, "lead", "refsync_scope_20261109", "_rs_carrier_scan.py")
spec = importlib.util.spec_from_file_location("up", SCANNER)
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)

N = "只能判「不可复现」"

def classify(L, needles):
    c = up.classify_line(L, needles, "")
    pos = min((L.find(x) for x in needles if x in L), default=-1)
    return c["role"] if c else None, pos, up.quoted_containing(L, pos)

CASES = [
    ("「核对」 " + N, "核对"),
    ("「逐字」 复算数字 " + N, "逐字"),
]

def main():
    print("=== STEP 2(d) reverse masking: minimal synthetic construction ===")
    print("mechanism: _rs_carrier_scan.py:165 pos = min(...find(n)...)")
    print("           :168 q = quoted_containing(line, pos) ; :173-182 role from q")
    print("")
    for L, extra in CASES:
        r1, p1, q1 = classify(L, [N])
        r2, p2, q2 = classify(L, [N, extra])
        print("line = %r" % L)
        print("  [N]        role=%-16s pos=%-3d q=%s" % (r1, p1, repr(q1)))
        print("  [N, %-6r] role=%-16s pos=%-3d q=%s" % (extra, r2, p2, repr(q2)))
        print("  ROLE_FLIP = %s  (needs_fix: %s -> %s)" %
              (r1 != r2, r1 == "ASSERTION", r2 == "ASSERTION"))
        print("")
    print("=> adding a needle is NOT monotone in the ROLE/fix-list sense:")
    print("   'scanned' is monotone (any/min cannot un-scan a line), but")
    print("   'classified as ASSERTION / needs_fix' is NOT monotone.")
    print("")
    print("REAL-CORPUS check: _me_reverse_assertion_out.txt found 0 such flips")
    print("   among 24 ASSERTION lines with the 9 candidate extra needles tried;")
    print("   so the risk is demonstrated synthetically but NOT observed on")
    print("   this particular corpus. Reported honestly, not overstated.")

if __name__ == "__main__":
    main()
