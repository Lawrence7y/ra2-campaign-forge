import os,sys,struct,csv
sys.path.insert(0,r"D:/Project/ra2-campaign-forge/lead/next_re_20261117_r14/S13_N1/work")
from re_lib import *
res=residual_rows()
with open(os.path.join(EVID,"residual_xrefs.tsv"),"w",encoding="utf-8",newline="") as xf, open(os.path.join(EVID,"residual_strings.tsv"),"w",encoding="utf-8",newline="") as sf:
 wx=csv.writer(xf,delimiter="\t",lineterminator="\n");ws=csv.writer(sf,delimiter="\t",lineterminator="\n")
 wx.writerow(["entry","kind","site_or_addr","detail"])
 ws.writerow(["entry","site","imm","cstr"])
 for k,c,a in res:
  for h in vt_slots_for_entry(k):
   wx.writerow([f"{k:08X}","vt",f"{h['vt']:08X}",f"slot={h['slot']} class={h['class']} value_site={h['addr']:08X}"])
  for site in direct_xrefs(k):
   wx.writerow([f"{k:08X}","xref",f"{site:08X}","E8/E9 direct 32-bit relative"])
  for site,mnem,imm,s in find_imm_refs(k,512):
   ws.writerow([f"{k:08X}",f"{site:08X}",f"{imm:08X}",s])
  print(f"{k:08X} vt={len(vt_slots_for_entry(k))} xref={len(direct_xrefs(k))} str={len(find_imm_refs(k,512))}")
