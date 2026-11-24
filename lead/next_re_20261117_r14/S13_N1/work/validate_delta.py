import os,sys,csv
card=r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1"
p=os.path.join(card,"coverage_delta.tsv")
rows=[x.rstrip("\r\n").split("\t") for x in open(p,encoding="utf-8") if x.strip()]
print("rows",len(rows),"cols",sorted(set(len(r) for r in rows)))
assert len(rows)==2 and all(len(r)==9 for r in rows)
for r in rows:
 print("ROW",r[0],"base_sub=S13","grade",r[4],"name_kind",r[8],"conflict",r[7])
 assert r[1]=="S13" and r[4]=="[已证]" and r[7]=="0" and r[8]=="symbolic"
 assert not r[2].lower().startswith("sub_") and "slot" not in r[2]
 for ep in r[5].split(";"):
  q=os.path.join(r"D:/Project/ra2-campaign-forge",ep.split("#")[0])
  assert os.path.exists(q), q
print("VALIDATE PASS")
