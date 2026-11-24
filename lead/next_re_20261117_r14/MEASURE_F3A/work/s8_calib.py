# -*- coding: utf-8 -*-
"""MEASURE-F3A step 4b: recalibrate the ③b detector on the controls, then run the
full 274-row census. Controls must come out as the documented truth before any
census number is trusted.
"""
import csv, json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.stdout.reconfigure(encoding="utf-8")
from pelib import PE
from thirdb import conds, thirdb, which

ROOT = r"D:\Project\ra2-campaign-forge"
ATLAS = os.path.join(ROOT, r"lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv")
EXE = os.path.join(ROOT, r"ra2youli\gamemd.exe")
pe = PE(EXE)
atlas = {}
with open(ATLAS, encoding="utf-8-sig", newline="") as f:
    for r in csv.DictReader(f, delimiter="\t"):
        atlas[r["entry"].upper()] = int(r["size"])

CTRL = [
    # entry, expected ③b, why
    ("004A9840", True,  "text names ③b② anchors: +0x26 call 0x6DA230 / +0x2D cmp eax,-1 / +0x30 setne dl"),
    ("006F3330", True,  "text names ③b② anchors (+0x0BD cmp [eax+0xd50],-1 ...)"),
    ("0065CDD0", True,  "text names ③b② anchors (+0x52 call [7E11A0] / +0xAB cmp eax,-1)"),
    ("00700600", True,  "text names ③b②+③b④ anchors (+0x01EA cmp eax,-1 ... 有界循环)"),
    ("004AC660", False, "MapClass::SetSellMode - text is name+category only (乙 template)"),
    ("004A80D0", False, "CD::GetCDNumber - 2 instructions, nothing to close"),
    ("0045A640", False, "card control: pure compare loop, 0 writes 0 calls -> ③b must fail"),
    ("004E2690", True,  "real implementation (AUDIT-MARGIN: semantics since SEMFIXed)"),
]
print("%-9s %-5s %-5s %-4s %-5s %-5s  %s" % ("entry", "want", "got", "③b", "instr", "back", "note"))
bad = []
for e, want, note in CTRL:
    sz = atlas.get(e)
    c = conds(pe, int(e, 16), sz)
    got = thirdb(c)
    ok = (got == want)
    if not ok:
        bad.append((e, want, got))
    print("%-9s %-5s %-5s %-4s %-5d %-5d  %s  %s" % (
        e, want, got, which(c), c["n_instr"], c["n_backedge"],
        note[:58], "" if ok else "<== MISMATCH"))
print("\ncontrols matching documented truth: %d/%d" % (len(CTRL) - len(bad), len(CTRL)))
if bad:
    print("MISMATCH:", bad)
    sys.exit(1)
print("ALL CONTROLS PASS - detector accepted")
