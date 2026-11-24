# -*- coding: utf-8 -*-
"""_mev_step2.py — INDEPENDENT single/double needle reproduction (ask 2).

Runs the UNMODIFIED upstream scanner myself (not via the author's _me_repro.py),
with the exact kou jing --include-refuting --max-depth 2 --ext .md, and records:
EXIT / SELF_TEST / scanned files / carrier occurrences / :22 verdict.
Also re-implements iter_files() from _rs_carrier_scan.py:150-162 independently
to count the corpus and to check the documented 637->638 drift file.
Read-only outside this write domain. All outputs prefixed _mev_.
No shell, no dynamically assembled command strings: subprocess arg lists only.
"""
import os, io, sys, subprocess, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
LEAD = os.path.join(ROOT, "lead")
SCANNER = os.path.join(LEAD, "refsync_scope_20261109", "_rs_carrier_scan.py")
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"
DRIFT = "chain_vs_single_20261109/_cs_BASELINE_ALIGNMENT_20261109.md"

PY = sys.executable

def my_iter_files(root, exts, maxdepth):
    """Independent reimplementation of _rs_carrier_scan.py:150-162."""
    for dp, dn, fn in os.walk(root):
        rel = os.path.relpath(dp, root).replace("\\", "/")
        depth = 0 if rel == "." else rel.count("/") + 1
        if maxdepth is not None and depth > maxdepth:
            dn[:] = []
            continue
        for f in sorted(fn):
            if exts and not any(f.lower().endswith(e) for e in exts):
                continue
            p = os.path.join(dp, f)
            if os.path.isfile(p):
                yield p, os.path.relpath(p, root).replace("\\", "/")

def build_args(n1, n2, is_double):
    """Return a fixed argument LIST (never a shell string)."""
    base = ["-I", "-X", "utf8", SCANNER,
            "--needle", n1]
    if is_double:
        base = base + ["--needle", n2]
    tail = ["--include-refuting", "--max-depth", "2", "--ext", ".md"]
    return base + tail

def run(tag, n1, n2, is_double):
    args = build_args(n1, n2, is_double)
    out = os.path.join(HERE, "_mev_scanner_%s_out.txt" % tag)
    with io.open(out, "w", encoding="utf-8") as fh:
        cp = subprocess.run([PY] + args, cwd=ROOT, stdout=fh,
                            stderr=subprocess.STDOUT, shell=False)
    lines = io.open(out, encoding="utf-8", errors="replace").read().splitlines()
    def g(key, default="<missing>"):
        return next((l for l in lines if l.startswith(key)), default)
    f22 = next((l for l in lines if "DRAFT_S609.md:22 want=" in l), "<missing>")
    return {"args": args, "out": out, "exit": cp.returncode,
            "scanned": g("scanned files"), "self_test": g("SELF_TEST"),
            "v22": f22}

def main():
    o = []
    def P(s=""):
        o.append(s); print(s)
    P("=== ASK 2: independent single/double needle reproduction ===")
    P("SCANNER = %s" % SCANNER)
    P("SCANNER sha256 = %s ; bytes = %d" %
      (hashlib.sha256(open(SCANNER, "rb").read()).hexdigest(), os.path.getsize(SCANNER)))
    P("")
    for tag, is_double in [("single", False), ("double", True)]:
        r = run(tag, N1, N2, is_double)
        P("--- %s ---" % tag)
        P("ARGS = %r" % (r["args"],))
        P("OUT = %s" % os.path.basename(r["out"]))
        P("EXIT = %d" % r["exit"])
        P(r["scanned"])
        P(r["self_test"])
        P(r["v22"].strip())
        P("")
    P("=== independent corpus enumeration (mirrors scanner iter_files, ext=.md max-depth=2) ===")
    paths = list(my_iter_files(LEAD, [".md"], 2))
    scannable = []
    for p, rel in paths:
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        if b"\x00" in b:
            continue
        scannable.append((p, rel, b))
    P("candidate .md paths = %d ; scannable (opened, non-NUL) = %d" % (len(paths), len(scannable)))
    drift = [x for x in scannable if x[1].replace("\\", "/") == DRIFT]
    P("drift file present = %s" % bool(drift))
    if drift:
        t = drift[0][2].decode("utf-8", "replace")
        P("drift file bytes = %d ; contains N1 = %s ; contains N2 = %s" %
          (len(drift[0][2]), N1 in t, N2 in t))
        P("count WITHOUT drift file = %d  (explains author 637 at repro time)" % (len(scannable) - 1))
    P("")
    io.open(os.path.join(HERE, "_mev_step2_out.txt"), "w", encoding="utf-8").write("\n".join(o) + "\n")

if __name__ == "__main__":
    main()
