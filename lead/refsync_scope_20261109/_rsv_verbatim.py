"""_rsv_verbatim.py — independent char-level verbatim comparison of the claimed lines.
Run: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/refsync_scope_20261109/_rsv_verbatim.py"
"""
import hashlib, os
ROOT = r"D:/Project/ra2-campaign-forge"

def line(rel, n):
    p = os.path.join(ROOT, rel)
    txt = open(p, "r", encoding="utf-8", newline="").read()
    L = txt.split("\n")
    return L[n-1]

A = ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123)
B = ("lead/ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25)
C = ("lead/ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215)
D = ("lead/ledger_appendix_20261108/_lad_tpl.md", 151)
E = ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196)
F = ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129)

def cmp(name, x, y):
    s, t = line(*x), line(*y)
    equal = (s == t)
    print(f"--- {name}: {x[0]}:{x[1]}  vs  {y[0]}:{y[1]} ---")
    print(f"  EQUAL = {equal}")
    print(f"  len(left)={len(s)} chars / {len(s.encode('utf-8'))} bytes ; len(right)={len(t)} chars / {len(t.encode('utf-8'))} bytes")
    print(f"  sha256(left)  = {hashlib.sha256(s.encode('utf-8')).hexdigest()}")
    print(f"  sha256(right) = {hashlib.sha256(t.encode('utf-8')).hexdigest()}")
    if equal:
        print("  DIFF_COUNT = 0 ; DIFF_POSITIONS = [] ; no differing codepoints")
    else:
        diffs = []
        for i in range(max(len(s), len(t))):
            a = s[i] if i < len(s) else "<EOS>"
            b = t[i] if i < len(t) else "<EOS>"
            if a != b:
                ca = f"U+{ord(a):04X}" if a != "<EOS>" else "EOS"
                cb = f"U+{ord(b):04X}" if b != "<EOS>" else "EOS"
                diffs.append((i, a, ca, b, cb))
                if len(diffs) <= 8:
                    print(f"    first-diff pos={i}: left={a!r} ({ca})  right={b!r} ({cb})")
        print(f"  DIFF_COUNT = {len(diffs)} ; first diff pos = {diffs[0][0] if diffs else 'N/A'}")
    return equal

print("=== GROUP 1 (claimed verbatim EQUAL) ===")
g1 = cmp("group1", A, B)
print()
print("=== GROUP 1 across 6 claimed identical carriers ===")
pairs = [("A",A),("B",B),("E",E),("F",F)]
s0 = line(*A)
for k, x in pairs:
    s = line(*x)
    print(f"  {k} {x[0]}:{x[1]} len={len(s)} sha={hashlib.sha256(s.encode('utf-8')).hexdigest()} EQUAL_TO_A={s==s0}")
print()
print("=== GROUP 2 (claimed verbatim EQUAL) ===")
g2 = cmp("group2", C, D)
print()
print("=== GROUP 1 vs GROUP 2 (claimed NOT the same sentence) ===")
g12 = cmp("group1-vs-group2", A, C)
print()
print(f"SUMMARY: group1_EQUAL={g1} group2_EQUAL={g2} group1_vs_group2_EQUAL={g12}")
