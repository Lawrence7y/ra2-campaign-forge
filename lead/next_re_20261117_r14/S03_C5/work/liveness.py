"""Liveness sanity (discipline 10 / 错源23): check each main vt has a non-atexit constructor write.
Since ALL 8 rows' 4-ring ④ is direct-call (not livevt), livevt全条款 is N/A; this is consistency sanity only.
"""
import os,sys,json,struct
sys.path.insert(0,os.path.dirname(__file__))
import common as C
CARD8=["0055C7C0","0065CF00","00431F10","0065CB50","00473B10","00473AE0","0047AF10","0065CCE0"]
VT={"0055C7C0":0x7ed394,"0065CF00":0x7f0904,"00431F10":0x7e1668,"0065CB50":0x7f0904,
    "00473B10":0x7e16b0,"00473AE0":0x7e16b0,"0047AF10":0x7e1668,"0065CCE0":0x7f0904}
pe=C.get_pe(); data=C._data
def off2va(i):
    for s in pe.sections:
        if s.PointerToRawData<=i<s.PointerToRawData+s.SizeOfRawData:
            return C.IMAGE_BASE+s.VirtualAddress+(i-s.PointerToRawData)
    return None
def find_vt_writes(vt):
    """mov dword ptr [abs],imm32 = C7 05 <glob4> <imm4>"""
    out=[]; i=0
    while True:
        i=data.find(b"\xC7\x05",i)
        if i<0:break
        if i+10<=len(data):
            imm=struct.unpack("<I",data[i+6:i+10])[0]
            if imm==vt:
                glob=struct.unpack("<I",data[i+2:i+6])[0]
                va=off2va(i)
                out.append({"insn_va":("0x%x"%va) if va else None,"glob":"0x%x"%glob})
        i+=1
    return out
s=C.text_section()
atexit_sites=[]
for insn in C.md().disasm(data[s.PointerToRawData:s.PointerToRawData+s.Misc_VirtualSize],C.IMAGE_BASE+s.VirtualAddress):
    if insn.mnemonic=='call' and len(insn.bytes)>=5 and insn.bytes[0]==0xE8:
        t=insn.address+5+struct.unpack("<i",insn.bytes[1:5])[0]
        if t==0x7C978A: atexit_sites.append(insn.address)
out={}
for e in CARD8:
    vt=VT[e]; writes=find_vt_writes(vt)
    atexit_vas=set()
    for a in atexit_sites:
        atexit_vas.add(a)
    near=[w for w in writes if w["insn_va"] and any(abs(int(w["insn_va"],16)-a)<0x40 for a in atexit_vas)]
    out[e]={"vt":"0x%x"%vt,"c705_writes":writes,"n_writes":len(writes),"writes_near_atexit":near}
    print("%s vt=0x%x writes=%d near_atexit=%d %s"%(e,vt,len(writes),len(near),[w["insn_va"] for w in writes[:8]]))
json.dump({"targets":out,"n_atexit_sites":len(atexit_sites)},open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","liveness.json"),"w",encoding="utf-8"),indent=2)
print("atexit sites total",len(atexit_sites))
