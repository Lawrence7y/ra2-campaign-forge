# -*- coding: utf-8 -*-
"""_me_reverse_assertion.py — Step 2(d) stronger construction.

Finds REAL corpus lines (ext=.md, max-depth=2) that are ASSERTION under
[N1,N2] but become non-ASSERTION when a third needle is added that hits
EARLIER in the line and OUTSIDE any quote span. This flips needs_fix from
True to False, i.e. a true carrier silently disappears from the fix list.

Read-only outside the write domain; imports the unmodified scanner.
"""
import os, io, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")
spec = importlib.util.spec_from_file_location("up", SCANNER)
up = importlib.util.module_from_spec(spec)
spec.loader.exec_module(up)

N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
EXTRA = ["核对", "复核", "本会话", "登记", "实跑", "grep", "逐字", "订正", "清单"]

def corpus():
    for dp, dn, fn in os.walk(LEAD):
        rel_d = os.path.relpath(dp, LEAD).replace("\\", "/")
        if (0 if rel_d == "." else rel_d.count("/") + 1) > 2:
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
            yield (os.path.relpath(p, LEAD).replace("\\", "/"),
                   b.decode("utf-8", "replace"))

def main():
    found = []
    assertions = 0
    for rel, txt in corpus():
        for i, L in enumerate(txt.splitlines(), 1):
            c = up.classify_line(L, [N1, N2], "")
            if not c or c["role"] != "ASSERTION":
                continue
            assertions += 1
            pos = min((L.find(n) for n in [N1, N2] if n in L), default=-1)
            negs = [k for k in up.NEG_LEX if k in L]
            for tok in EXTRA:
                q = L.find(tok)
                if not (0 <= q < pos):
                    continue
                if up.quoted_containing(L, q) is not None:
                    continue
                c2 = up.classify_line(L, [N1, N2, tok], "")
                if c2 and c2["role"] != "ASSERTION":
                    found.append((rel, i, tok, q, pos, c["role"], c2["role"],
                                  bool(negs), L[:110]))
                    break
    print("ASSERTION lines under [N1,N2] = %d" % assertions)
    print("=== ASSERTION -> non-ASSERTION flips caused by adding ONE needle ===")
    for x in found[:12]:
        print("  %s:%d extra=%r pos=%d orig_pos=%d %s -> %s negs=%s" %
              (x[0], x[1], x[2], x[3], x[4], x[5], x[6], x[7]))
        print("      text: %s" % x[8])
    print("flip count = %d" % len(found))

if __name__ == "__main__":
    main()
