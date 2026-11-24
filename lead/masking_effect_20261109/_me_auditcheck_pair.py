# -*- coding: utf-8 -*-
"""_me_auditcheck_pair.py — find a genuine TRUE-PASS needle pair for the
verification matrix. NEW file in sole write domain; read-only elsewhere."""
import os, io, sys, subprocess, itertools

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SC = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")

CONTROLS = [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215),
]
WANTS = ["ASSERTION"] * 4 + ["REFUTING_QUOTE", "ASSERTION"]

def corpus():
    for dp, dn, fn in os.walk(LEAD):
        d = os.path.relpath(dp, LEAD).replace("\\", "/")
        depth = 0 if d == "." else d.count("/") + 1
        if depth > 2:
            dn[:] = []
            continue
        for f in sorted(fn):
            if not f.lower().endswith(".md"):
                continue
            p = os.path.join(dp, f)
            try:
                b = io.open(p, "rb").read()
            except OSError:
                continue
            if b"\x00" in b:
                continue
            rel = os.path.relpath(p, LEAD).replace("\\", "/")
            yield rel, b.decode("utf-8", "replace").splitlines()

lines = list(corpus())
cands = ["不能定位当年", "不能定位", "当年错误步骤", "错误步骤",
         "定位当年错误步骤", "不能定位当年错误步骤", "只能判", "不可复现",
         "不能定位当年错误", "当年错误", "步骤", "判", "错误",
         "复算数字", "订正清单", "不受影响", "边界句"]
ok = []
for n in cands:
    cmd = [sys.executable, "-I", "-X", "utf8", SC, "--needle", n,
           "--include-refuting", "--max-depth", "2", "--ext", ".md"]
    cp = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    ls = cp.stdout.splitlines()
    st = next((l.split("=", 1)[1].strip() for l in ls if l.startswith("SELF_TEST")), "?")
    got = []
    for rel, no in CONTROLS:
        key = "%s:%d want=" % (rel, no)
        L = next((l for l in ls if key in l), "")
        got.append(L.split("got=")[-1].strip() if "got=" in L else "<missing>")
    ctl_ok = all(g == w for g, w in zip(got, WANTS))
    S = set((rel, i) for rel, txt in lines for i, L in enumerate(txt, 1) if n in L)
    print("%-24r EXIT=%d SELF_TEST=%-4s ctrl6=%s |U|=%d" % (n, cp.returncode, st, ctl_ok, len(S)))
    if cp.returncode == 0 and st == "PASS" and ctl_ok:
        ok.append((n, S))

print()
print("=== PAIRS that both pass 6/6 and both have >0 exclusive corpus lines ===")
for (a, A), (b, B) in itertools.combinations(ok, 2):
    ea, eb = len(A - B), len(B - A)
    if ea > 0 and eb > 0:
        # does the pair have >=1 exclusive NEGATIVE CONTROL each?
        ea_c = sum(1 for key in CONTROLS if (a in dict(lines).get(key[0], [""] * key[1])[key[1]-1] if False else False))
        print("PAIR %r / %r : exclusive=[%d,%d] both=%d" % (a, b, ea, eb, len(A & B)))
