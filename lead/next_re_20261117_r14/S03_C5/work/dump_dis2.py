"""Dump function bodies using the CFG extents (ext_lo/ext_hi) from SURVEY_RING24 classification.tsv.
These extents are self-written CFG (not function_atlas.tsv entry+size), satisfying dual-channel discipline.
Entries re-dumped with entry-relative offsets. Also emits ③b signal metrics.
"""
import os, sys, json, csv
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
SELECT = ["0055C7C0","0065CF00","00431F10","0065CB50","00473B10","00473AE0","0047AF10","0065CCE0"]
# also dump all 24 for triage
ALL24 = ["00431F10","00431F70","00432050","004322A0","004325C0","00473AE0","00473B10",
 "00473C00","00473CE0","00473FC0","0047AAB0","0047AE10","0047AF10","0055C7C0","00631D30",
 "0065CB50","0065CCA0","0065CCE0","0065CDD0","0065CF00","0065D0D0","0065D190","0065D1F0","0065D240"]

ext = {}
for r in csv.DictReader(open(CLS,encoding="utf-8"),delimiter="\t"):
    if r["entry"] in ALL24:
        ext[r["entry"]] = (int(r["ext_lo"],16), int(r["ext_hi"],16), r["name"])

os.makedirs(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","dis2"),exist_ok=True)
meta={}
for e in ALL24:
    lo,hi,name = ext[e]
    size = hi-lo
    off = C.va2off(lo)
    code = C._data[off:off+size]
    lines=[]
    jcc=jmp=calls=rets=0
    switch_pts=[]
    for insn in C.md().disasm(code, lo):
        o=insn.address-lo
        m=insn.mnemonic
        if m.startswith("j") and m!="jmp": jcc+=1
        if m=="jmp":
            jmp+=1
            # switch table indicator: jmp dword ptr [reg*4+...] or jmp [..*4..]
            if "dword ptr" in insn.op_str and "*" in insn.op_str:
                switch_pts.append((o,m,insn.op_str))
        if m=="call": calls+=1
        if m.startswith("ret"): rets+=1
        lines.append("+%04X  %08X  %-9s %-38s ; %s"%(o,insn.address,m,insn.op_str,insn.bytes.hex()))
    with open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","dis2",e+".txt"),"w",encoding="utf-8") as f:
        f.write("; entry %s name=%s extent=%08X..%08X size=0x%X insn=%d jcc=%d jmp=%d call=%d ret=%d\n"%(
            e,name,lo,hi,size,len(lines),jcc,jmp,calls,rets))
        f.write("\n".join(lines)+"\n")
    meta[e]={"name":name,"extent":["0x%x"%lo,"0x%x"%hi],"size":size,"insn":len(lines),
             "jcc":jcc,"jmp":jmp,"call":calls,"ret":rets,"switch_pts":switch_pts}
with open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","dis2","_meta.json"),"w",encoding="utf-8") as f:
    json.dump(meta,f,indent=2)
print("entry   name                     size  insn jcc jmp cal ret switch")
for e in ALL24:
    m=meta[e]
    print("%s %-24s 0x%-4X %4d %3d %3d %3d %3d %s"%(e,m["name"],m["size"],m["insn"],m["jcc"],m["jmp"],m["call"],m["ret"],len(m["switch_pts"])))
