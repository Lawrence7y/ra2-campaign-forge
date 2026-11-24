# -*- coding: utf-8 -*-
"""Fix probe kinds (note is col 7) and apply §966 guard to probe rows with broken evidence."""
import csv, os, sys
sys.stdout.reconfigure(encoding="utf-8")
ROOT=r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
PP=os.path.join(ROOT,"COVERAGE","probe_and_data_entries.tsv")
PEND=os.path.join(ROOT,"COVERAGE","PENDING_CORRECTIONS.tsv")
def rd(p):
    with open(p,"r",encoding="utf-8-sig",newline="") as f:return list(csv.reader(f,delimiter="\t"))
def wr(p,rows):
    with open(p,"w",encoding="utf-8",newline="") as f:csv.writer(f,delimiter="\t",lineterminator="\n").writerows(rows)
rows=rd(PP)
KIND={"00414B9E":"callsite","0087F924":"global","00A83D4C":"global","0087F7E8":"global",
 "00886FA0":"global","00886FA4":"global","00A8EB50":"global","00B0F724":"global",
 "0000030C":"field_offset","000001AC":"field_offset","0000009C":"field_offset","000000A0":"field_offset"}
newpend=[]
for r in rows[1:]:
    if r and len(r)>7 and "routed by M2" in r[7]:
        e=r[0].strip().upper()
        if e in KIND: r[1]=KIND[e]
        # §966 guard: [已证] with non-existent evidence file -> downgrade
        if r[4]=="[已证]":
            ev=r[5].strip(); base=ev.split(" §")[0].split("#")[0].split(";")[0]
            ok=False
            for cand in [os.path.join(ROOT,r[6],base),os.path.join(ROOT,base),os.path.join(r"D:\Project\ra2-campaign-forge",base)]:
                if os.path.exists(cand): ok=True;break
            if not ok:
                newpend.append([r[6],e,"grade","[已证] (delta; evidence file missing)","[未证]","M2-merge",
                                "UNFOUNDED_PROVED (M2 guard): evidence_path=%s"%ev])
                r[4]="[未证]"
                print("DOWNGRADED probe row",e,r[6],ev)
wr(PP,rows)
if newpend:
    pend=rd(PEND); pend.extend(newpend); wr(PEND,pend)
    print("added",len(newpend),"PENDING rows")
print("probe kinds fixed")
