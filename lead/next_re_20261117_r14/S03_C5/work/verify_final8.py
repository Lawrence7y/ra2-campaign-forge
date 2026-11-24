"""Verify ④ direct sites + liveness for the FINAL 8 candidates (refined after extent-corrected ③b triage).
Final 8: 0055C7C0 0065CF00 0065CB50 0065CCE0 00473B10 00432050 004322A0 0065CDD0
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import common as C

FINAL = ["0055C7C0","0065CF00","0065CB50","0065CCE0","00473B10","00432050","004322A0","0065CDD0"]
# CFG extents from classification.tsv
import csv
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
ext={}; rtti={}
for r in csv.DictReader(open(CLS,encoding="utf-8"),delimiter="\t"):
    if r["entry"] in FINAL:
        ext[r["entry"]]=(int(r["ext_lo"],16),int(r["ext_hi"],16))
        rtti[r["entry"]]=(r["rtti_vt"],r["rtti_slot"],r["rtti_classes"])

s=C.text_section(); TVA=C.IMAGE_BASE+s.VirtualAddress; TVS=s.Misc_VirtualSize
tb=C._data[s.PointerToRawData:s.PointerToRawData+TVS]

# channel A: capstone sweep of E8 calls
calls=set()
for insn in C.md().disasm(tb, TVA):
    if insn.mnemonic=="call" and len(insn.bytes)>=5 and insn.bytes[0]==0xE8:
        rel=struct.unpack("<i",insn.bytes[1:5])[0]
        calls.add((insn.address, insn.address+5+rel))

out={}
for e in FINAL:
    entry=int(e,16); lo,hi=ext[e]
    sites=sorted(site for site,t in calls if t==entry and not (lo<=site<hi) and site!=entry)
    out[e]={"entry":e,"extent":["0x%x"%lo,"0x%x"%hi],"rtti_vt":rtti[e][0],"rtti_slot":rtti[e][1],
            "rtti_classes":rtti[e][2],"n_sites":len(sites),"sites":["0x%x"%x for x in sites]}
    print("%s %-22s vt=%s slot=%s extent=%s..%s n_sites=%d"%(e,"",rtti[e][0],rtti[e][1],
          out[e]["extent"][0],out[e]["extent"][1],len(sites)))

json.dump({"final8":out},open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","final8_sites.json"),"w",encoding="utf-8"),indent=2)
print("wrote EVIDENCE/final8_sites.json")
