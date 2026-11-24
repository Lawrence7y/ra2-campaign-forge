
# --- 方案乙：为每根 needle 的「只被它命中」行建负控 --------------------------
# 核心：从语料自动算 exclusive(k) = U_k \ union(others)；每根至少 1 条负控。
# 把 needle k 换成坏串后，exclusive(k) 负控必然 FAIL => 加参数掩盖不了坏针。
import os, io, sys
LEAD = r"D:/Project/ra2-campaign-forge/lead"
NEEDLES = ["只能判「不可复现」"]

def iter_lines():
    for dp, dn, fn in os.walk(LEAD):
        rel_d = os.path.relpath(dp, LEAD).replace("\\", "/")
        if (0 if rel_d == "." else rel_d.count("/") + 1) > 2:
            dn[:] = []; continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"): continue
            p = os.path.join(dp, f)
            try: b = open(p, "rb").read()
            except OSError: continue
            if b"\x00" in b: continue
            rel = os.path.relpath(p, LEAD).replace("\\", "/")
            for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
                yield rel, i, L

U = {n: set() for n in NEEDLES}
for rel, i, L in iter_lines():
    for n in NEEDLES:
        if n in L: U[n].add((rel, i))

for k in NEEDLES:
    others = set().union(*[U[n] for n in NEEDLES if n != k])
    excl = U[k] - others
    print("NEEDLE %r : |U|=%d  |exclusive|=%d  examples=%s" %
          (k, len(U[k]), len(excl), sorted(excl)[:3]))
    if not excl:
        print("  !! FATAL: no exclusive control -> needle is NOT independently testable")
# 断言：每根 needle 必须有 >=1 条 exclusive 负控，否则整体判 FAIL（覆盖度门禁）
ok = all(U[k] - set().union(*[U[n] for n in NEEDLES if n != k]) for k in NEEDLES)
print("COVERAGE_GATE = %s" % ("PASS" if ok else "FAIL"))
import sys
sys.exit(0 if ok else 1)   # gate MUST control exit status, not just print
