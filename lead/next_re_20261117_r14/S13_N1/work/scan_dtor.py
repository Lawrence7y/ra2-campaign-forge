import os,sys,csv,re
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
OPDEL=0x7C8B3D
print('known 4393D0 vt',vt_slots_for_entry(0x4393D0))
rows=[]
for k,c,a in residual_rows():
    ins=dis(k,768)
    hits=[]
    for i,x in enumerate(ins):
        norm=x.op_str.replace(" ","").lower()
        if x.mnemonic=="test" and re.match(r"byteptr\[esp\+(0x)?[0-9a-f]+\],(0x)?1$",norm):
            window=ins[i+1:i+10]
            callidx=[j for j,y in enumerate(window) if y.mnemonic=="call" and y.op_str.lower().endswith("0x7c8b3d")]
            retidx=[j for j,y in enumerate(window) if y.mnemonic.startswith("ret")]
            hits.append((x.address,bool(callidx),bool(retidx),[fmt(y) for y in window]))
    vh=vt_slots_for_entry(k)
    cls=vh[0]["class"] if vh else ""; slot=vh[0]["slot"] if vh else ""
    if not hits: rows.append([f"{k:08X}","","","",cls,slot,""])
    for ta,hc,hr,win in hits: rows.append([f"{k:08X}",f"{ta:08X}",str(hc),str(hr),cls,slot," | ".join(win)])
with open(os.path.join(EVID,"dtor_scan.tsv"),"w",encoding="utf-8",newline="") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["entry","test_addr","has_opdelete","has_ret","vt_class","vt_slot","window"]);w.writerows(rows)
for r in rows:
 print("\t".join(r[:6]))
