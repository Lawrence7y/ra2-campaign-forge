# -*- coding: utf-8 -*-
"""_mev_mech.py — INDEPENDENT mechanism verification (asks 3 and 4).

Runs the UNMODIFIED scanner with several needle configs and records the raw
verdicts. Then independently recomputes the six negative controls' hit sets.
No shell; subprocess arg lists with shell=False only. Outputs _mev_ prefixed.
"""
import os, io, sys, subprocess, hashlib, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
N3 = "登记效力说明"
N3B = "与既有草案"
BROKEN = "TOTALLY_BROKEN_NEEDLE_SENTINEL_XYZ"
PY = sys.executable

CONTROLS = [
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 123, "ASSERTION"),
    ("ledger_appendix_20261108/_la_draft3_s604_gapdiff.md", 25, "ASSERTION"),
    ("ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 196, "ASSERTION"),
    ("ledger_bound_20261109/_lb_BOUND_VOLUME.md", 129, "ASSERTION"),
    ("s604_verdict_entry_20261109/_ve_DRAFT_S609.md", 22, "REFUTING_QUOTE"),
    ("ledger_appendix_20261108/LEDGER_APPENDIX_DRAFT.md", 215, "ASSERTION"),
]

TAIL = ["--include-refuting", "--max-depth", "2", "--ext", ".md"]

def run(tag, needles):
    args = ["-I", "-X", "utf8", SCANNER]
    for n in needles:
        args += ["--needle", n]
    args += TAIL
    out = os.path.join(HERE, "_mev_mech_%s_out.txt" % tag)
    with io.open(out, "w", encoding="utf-8") as fh:
        cp = subprocess.run([PY] + args, cwd=ROOT, stdout=fh,
                            stderr=subprocess.STDOUT, shell=False)
    lines = io.open(out, encoding="utf-8", errors="replace").read().splitlines()
    g = lambda k, d="<missing>": next((l for l in lines if l.startswith(k)), d)
    v22 = next((l for l in lines if "DRAFT_S609.md:22 want=" in l), "<missing>")
    epass = [l.strip() for l in lines if l.startswith("  PASS ") or l.startswith("  FAIL ")]
    return {"exit": cp.returncode, "scanned": g("scanned files"),
            "selftest": g("SELF_TEST"), "v22": v22.strip(),
            "control_lines": epass, "file": os.path.basename(out)}

def corpus_lines():
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
            rel = os.path.relpath(p, LEAD).replace("\\", "/")
            for i, L in enumerate(b.decode("utf-8", "replace").splitlines(), 1):
                yield rel, i, L

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    P("=== ASK 3/4: independent mechanism runs on UNMODIFIED scanner ===")
    P("scanner sha256 = %s" % hashlib.sha256(open(SCANNER, "rb").read()).hexdigest())
    P("")
    configs = [
        ("n1only", [N1]),
        ("n2only", [N2]),
        ("double", [N1, N2]),
        ("n2_broken", [N2, BROKEN]),
        ("n1_broken", [BROKEN, N2]),
        ("triple", [N1, N2, N3]),
        ("triple_b", [N1, N2, N3B]),
    ]
    for tag, nd in configs:
        r = run(tag, nd)
        P("--- %s : needles=%r" % (tag, nd))
        P("  EXIT=%d  %s  %s" % (r["exit"], r["scanned"], r["selftest"]))
        P("  %s" % r["v22"])
        P("  negative-control lines (%d): %s" % (len(r["control_lines"]),
          " | ".join(x.split("want=")[0].strip() for x in r["control_lines"])))
        P("")
    P("=== ASK 3: independent negative-control hit sets (whole corpus) ===")
    idx = {(rel, n): L for rel, n, L in corpus_lines()}
    P("controls located in corpus = %d / %d" %
      (sum(1 for c in CONTROLS if (c[0], c[1]) in idx), len(CONTROLS)))
    exN1 = exN2 = both = 0
    for rel, n, want in CONTROLS:
        L = idx.get((rel, n))
        if L is None:
            P("  %s:%d  MISSING" % (rel, n)); continue
        h1, h2 = N1 in L, N2 in L
        tag = "{N1,N2}" if (h1 and h2) else ("{N1}" if h1 else ("{N2}" if h2 else "{}"))
        P("  %s:%-4d want=%-16s hit_set=%s" % (rel, n, want, tag))
        if h1 and not h2: exN1 += 1
        if h2 and not h1: exN2 += 1
        if h1 and h2: both += 1
    P("  => N1-exclusive controls = %d ; N2-exclusive controls = %d ; both = %d"
      % (exN1, exN2, both))
    P("  => by report §3(a) criterion #2 (>=1 exclusive NEGATIVE CONTROL per needle),")
    P("     N1 has ZERO => should be UNPROVEN / overall FAIL")
    P("")
    io.open(os.path.join(HERE, "_mev_mech_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

if __name__ == "__main__":
    main()
