import os,sys,csv
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
with open(os.path.join(EVID,"function_bodies.txt"),"w",encoding="utf-8") as bf:
 for k,c,a in residual_rows():
  size=int(a.get("size","512"))
  bf.write("===== %08X size=%s %s =====\n"%(k,size,c.get("name","")))
  for i in fn_ins(k,size): bf.write(fmt(i)+"\n")
  bf.write("\n")
with open(os.path.join(EVID,"residual_strings.tsv"),"w",encoding="utf-8",newline="") as f:
 w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["entry","site","imm","mnemonic","cstr"])
 for k,c,a in residual_rows():
  for site,mnem,imm,s in printable_imm_refs(k,int(a.get("size","512"))):
   w.writerow([f"{k:08X}",f"{site:08X}",f"{imm:08X}",mnem,s])
for k,c,a in residual_rows():
 refs=printable_imm_refs(k,int(a.get("size","512")))
 print(f"{k:08X}: "+" ; ".join(f"{s}@{imm:08X}" for _,_,imm,s in refs))
