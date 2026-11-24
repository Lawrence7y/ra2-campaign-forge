# -*- coding: utf-8 -*-
"""Refine kind values on the 12 M2-appended probe rows; check prose-evidence files exist."""
import csv, os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PP=os.path.join(ROOT,"COVERAGE","probe_and_data_entries.tsv")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f:return list(csv.reader(f,delimiter="\t"))
rows=rd(PP)
KIND={
 "00414B9E":"callsite",
 "0087F924":"global","00A83D4C":"global","0087F7E8":"global",
 "00886FA0":"global","00886FA4":"global","00A8EB50":"global","00B0F724":"global",
 "0000030C":"field_offset","000001AC":"field_offset","0000009C":"field_offset","000000A0":"field_offset",
}
for r in rows[1:]:
    if r and len(r)>6 and r[6].startswith("M2-merge") or (r and len(r)>6 and "routed by M2" in r[6]):
        e=r[0].strip().upper()
        if e in KIND:
            r[1]=KIND[e]
# check evidence base files for prose fragments
for e in ["0087F924","0000021C","0000030C"]:
    for r in rows[1:]:
        if r and r[0].strip().upper()==e:
            ev=r[5]; base=ev.split(" §")[0].split("#")[0]
            card=r[6]
            p=os.path.join(ROOT,card,base)
            print("EVID check",e,repr(ev),"base_exists=",os.path.exists(p),p)
with open(PP,"w",encoding="utf-8",newline="") as f:
    csv.writer(f,delimiter="\t",lineterminator="\n").writerows(rows)
print("refined probe kinds written")
