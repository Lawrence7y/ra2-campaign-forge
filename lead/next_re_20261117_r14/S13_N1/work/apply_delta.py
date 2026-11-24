import os,sys,csv
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
card=os.path.dirname(EVID)
D={}
for x in open(os.path.join(card,"coverage_delta.tsv"),encoding="utf-8"):
 if not x.strip(): continue
 p=x.rstrip("\r\n").split("\t"); D[int(p[0],16)]={"name":p[2],"grade":p[4]}
rows=s13_rows(); n=len(rows); named=0; proved=0
for k,c,a in rows:
 nm=D[k]["name"] if k in D else c.get("name","")
 g=D[k]["grade"] if k in D else c.get("grade","")
 named += 0 if nm.strip().lower().startswith("sub_") else 1
 proved += 1 if g=="[已证]" else 0
print("POST_DELTA S13",n,"named",named,f"{100*named/n:.2f}%","proved",proved,f"{100*proved/n:.2f}%","threshold",-(-n*9//10))
print("named gain",named-214,"delta rows",len(D))
open(os.path.join(EVID,"post_delta_count.txt"),"w",encoding="utf-8").write(f"S13∩atlas={n}\nnamed={named}/{n} ({100*named/n:.2f}%)\nproved={proved}/{n} ({100*proved/n:.2f}%)\nthreshold={-(-n*9//10)}\nnamed_gain={named-214}\n")
