import os,sys,csv
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1\work")
from re_lib import *
rows=s13_rows(); residual=residual_rows()
named=sum(1 for k,c,a in rows if not c.get("name","").strip().lower().startswith("sub_"))
proved=sum(1 for k,c,a in rows if c.get("grade","")=="[已证]")
print("sha256",sha())
print("S13∩atlas",len(rows),"named",named,f"{named/len(rows)*100:.2f}%","proved",proved,f"{proved/len(rows)*100:.2f}%","threshold",-(-len(rows)*9//10),"sub_residual",len(residual))
from collections import Counter
print("grades",dict(Counter(c.get("grade","") for k,c,a in rows)))
with open(os.path.join(EVID,"baseline_recompute.tsv"),"w",encoding="utf-8",newline="") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["entry","atlas_size","name","grade","semantics","evidence_path"])
 for k,c,a in rows:
  w.writerow([f"{k:08X}",a.get("size",""),c.get("name",""),c.get("grade",""),c.get("one_line_semantics",""),c.get("evidence_path","")])
with open(os.path.join(EVID,"residual_rows.tsv"),"w",encoding="utf-8",newline="") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["entry","atlas_size","name","grade","semantics","evidence_path"])
 for k,c,a in residual:
  w.writerow([f"{k:08X}",a.get("size",""),c.get("name",""),c.get("grade",""),c.get("one_line_semantics",""),c.get("evidence_path","")])
for k,c,a in residual: print(f"{k:08X} size={a.get('size','')} grade={c.get('grade','')} {c.get('name','')} :: {c.get('one_line_semantics','')}")
