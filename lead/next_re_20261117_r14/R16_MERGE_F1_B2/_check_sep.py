# -*- coding: utf-8 -*-
"""Confirm appended-segment separator and the 3 no-④ rows."""
import os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(ROOT,"COVERAGE","coverage.tsv")
DELTA = os.path.join(ROOT,"R16_F1_B2","delta.tsv")
rows = [ln.split("\t") for ln in open(COV,encoding="utf-8",newline="").read().split("\n")[1:] if ln]
by = {r[0].strip().upper(): r for r in rows}
drows = [ln.split("\t") for ln in open(DELTA,encoding="utf-8",newline="").read().split("\n")[1:] if ln]
SEP = "；④ 活表槽位见证"
for r in drows:
    e=r[0].strip().upper(); old4=by[e][3]; new4=r[3]
    seg=new4[len(old4):]
    ok = seg.startswith(SEP)
    has4 = "④" in old4
    recon = new4.split(SEP,1)[0]
    print(e, "has④=",has4, "seg_start_ok=",ok, "recon==old4=", recon==old4, "seglen=",len(seg))
