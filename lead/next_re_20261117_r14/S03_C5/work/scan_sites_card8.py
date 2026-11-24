"""Correct-extent ④ direct-site scan for the 8 CARD candidates (skeleton list, kept for honesty).
Dual channel: capstone linear sweep (A) + raw-byte E8 then boundary verify (B).
Body extent = CFG ext_lo/ext_hi from classification.tsv (self-written CFG, not atlas entry+size).
"""
import os, sys, json, struct, csv
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CARD8 = ["0055C7C0","0065CF00","00431F10","0065CB50","00473B10","00473AE0","0047AF10","0065CCE0"]
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
ext={}
for r in csv.DictReader(open(CLS,encoding="utf-8"),delimiter="\t"):
    if r["entry"] in CARD8: ext[r["entry"]]=(int(r["ext_lo"],16),int(r["ext_hi"],16))

s=C.text_section(); TVA=C.IMAGE_BASE+s.VirtualAddress; TVS=s.Misc_VirtualSize
tb=C._data[s.PointerToRawData:s.PointerToRawData+TVS]

callsA=[]; n_insn=0
for insn in C.md().disasm(tb, TVA):
    n_insn+=1
    if insn.mnemonic=="call" and len(insn.bytes)>=5 and insn.bytes[0]==0xE8:
        rel=struct.unpack("<i",insn.bytes[1:5])[0]
        callsA.append((insn.address, insn.address+5+rel))
boundary=set(a for a,_ in callsA)
raw=[]
i=0
while True:
    i=tb.find(b"\xE8",i)
    if i<0: break
    if i+5<=len(tb):
        rel=struct.unpack("<i",tb[i+1:i+5])[0]; site=TVA+i
        raw.append((site,site+5+rel))
    i+=1

out={}
for e in CARD8:
    entry=int(e,16); lo,hi=ext[e]
    sitesA=sorted(site for site,t in callsA if t==entry and not(lo<=site<hi) and site!=entry)
    sitesB=sorted(site for site,t in raw if t==entry and site in boundary and not(lo<=site<hi) and site!=entry)
    out[e]={"entry":e,"extent":["0x%x"%lo,"0x%x"%hi],"kept_A":["0x%x"%x for x in sitesA],
            "kept_B":["0x%x"%x for x in sitesB],"n":len(sitesA),"agree":sitesA==sitesB}
    print("%s n=%2d agree=%s sites=%s"%(e,len(sitesA),sitesA==sitesB,",".join("0x%x"%x for x in sitesA)))

meta={"n_insn":n_insn,"n_e8_A":len(callsA),"n_raw_e8":len(raw),"text_va":"0x%x"%TVA,"text_vsize":TVS}
json.dump({"meta":meta,"targets":out},open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","direct_sites_card8.json"),"w",encoding="utf-8"),indent=2)
print("wrote EVIDENCE/direct_sites_card8.json")
