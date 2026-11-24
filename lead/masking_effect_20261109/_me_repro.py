# -*- coding: utf-8 -*-
"""_me_repro.py — Step 1(a) independent reproduction of the masking pair.

Runs the UNMODIFIED upstream scanner twice (single needle vs two needles),
with the exact parameter set that reproduces the orchestrator's five numbers:
  --ext .md --max-depth 2 --include-refuting

Outputs are written to THIS write domain with _me_ prefix. This script does
NOT modify _rs_carrier_scan.py or any existing script. Read-only on all
absolute-read-only paths. python -I -X utf8, hashlib for fingerprints.
"""
import os, sys, io, subprocess, hashlib

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SCANNER = os.path.join(ROOT, "lead", "refsync_scope_20261109", "_rs_carrier_scan.py")
OUTDIR = os.path.dirname(os.path.abspath(__file__))
N1 = "只能判「不可复现」"
N2 = "不能定位当年错误步骤"

def run(tag, needles):
    cmd = [sys.executable, "-I", "-X", "utf8", SCANNER]
    for n in needles:
        cmd += ["--needle", n]
    cmd += ["--include-refuting", "--max-depth", "2", "--ext", ".md"]
    out = os.path.join(OUTDIR, "_me_repro_%s_out.txt" % tag)
    cp = subprocess.run(cmd, cwd=ROOT, stdout=io.open(out, "w", encoding="utf-8"),
                        stderr=subprocess.STDOUT)
    txt = io.open(out, encoding="utf-8", errors="replace").read()
    lines = txt.splitlines()
    scanned = next((l for l in lines if l.startswith("scanned files")), "<none>")
    st = next((l for l in lines if l.startswith("SELF_TEST")), "<none>")
    v22 = next((l for l in lines if "DRAFT_S609.md:22 want=" in l), "<none>")
    return {"cmd": " ".join(cmd), "out": out, "exit": cp.returncode,
            "scanned": scanned, "self_test": st, "v22": v22.strip(),
            "out_sha256": hashlib.sha256(io.open(out, "rb").read()).hexdigest()}

def main():
    print("SCANNER = %s" % SCANNER)
    print("SCANNER_SHA256 = %s" % hashlib.sha256(io.open(SCANNER, "rb").read()).hexdigest())
    print("SCANNER_BYTES = %d" % os.path.getsize(SCANNER))
    print("")
    for tag, needles in [("single", [N1]), ("double", [N1, N2])]:
        r = run(tag, needles)
        print("=== %s ===" % tag)
        print("CMD = %s" % r["cmd"])
        print("OUT = %s (sha256=%s)" % (r["out"], r["out_sha256"]))
        print("EXIT = %d" % r["exit"])
        print(r["scanned"])
        print(r["self_test"])
        print(r["v22"])
        print("")

if __name__ == "__main__":
    main()
