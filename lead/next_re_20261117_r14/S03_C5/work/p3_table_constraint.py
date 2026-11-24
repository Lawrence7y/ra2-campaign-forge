"""P3: "next table's COL as self-table slot" error — block it explicitly.
For each entry (4-byte VA) occurrence in the image, hypothesize (vt,slot) with vt=X-slot*4 and
COL at vt-4, TD at COL+0xC, TD+8 inline .?A name. WITHOUT table-length constraint this yields
many pseudo pairs (a slot can fall into the NEXT vtable whose COL is at vt-4 of that next table).
WITH constraint: require slot < table_length(vt), where table_length = number of consecutive
dwords from vt that are valid .text function pointers before a non-.text dword (table terminator).
Report without vs with counts.
"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(__file__))
import common as C

CARD8 = ["0055C7C0","0065CF00","00431F10","0065CB50","00473B10","00473AE0","0047AF10","0065CCE0"]
pe=C.get_pe(); data=C._data
TEXT_VA=C.IMAGE_BASE+C.text_section().VirtualAddress
TEXT_END=TEXT_VA+C.text_section().Misc_VirtualSize

def off2va(i):
    for s in pe.sections:
        if s.PointerToRawData<=i<s.PointerToRawData+s.SizeOfRawData:
            return C.IMAGE_BASE+s.VirtualAddress+(i-s.PointerToRawData)
    return None

def find_va_occurrences(va):
    pat=struct.pack("<I",va); out=[]; start=0
    while True:
        i=data.find(pat,start)
        if i<0: break
        v=off2va(i)
        if v is not None: out.append(v)
        start=i+1
    return out

def valid_col(vt):
    col=C.u32(vt-4)
    if col is None: return None
    td=C.u32(col+0xC)
    if td is None: return None
    name=C.cstr(td+8)
    if name and name.startswith(".?A"):
        return (col,td,name)
    return None

def table_len(vt, maxn=600):
    """# consecutive dwords from vt that are valid .text pointers."""
    n=0
    for k in range(maxn):
        v=C.u32(vt+4*k)
        if v is None: break
        if TEXT_VA<=v<TEXT_END:
            n+=1
        else:
            break
    return n

out={}
for e in CARD8:
    entry=int(e,16)
    occ=find_va_occurrences(entry)
    pseudo=[]  # (vt,slot,col,name) without constraint
    for X in occ:
        for slot in range(0,400):
            vt=X-4*slot
            if vt<0x400000: break
            vc=valid_col(vt)
            if vc:
                pseudo.append({"vt":"0x%x"%vt,"slot":slot,"col":"0x%x"%vc[0],"name":vc[2]})
    constrained=[]
    for p in pseudo:
        vt=int(p["vt"],16); slot=p["slot"]
        tl=table_len(vt)
        if slot<tl:
            p2=dict(p); p2["table_len"]=tl; constrained.append(p2)
    out[e]={"entry":e,"n_occurrences":len(occ),"n_pseudo_without":len(pseudo),
            "n_with_constraint":len(constrained),
            "constrained":constrained[:40]}
    print("%s occ=%d  pseudo_without=%d  with_constraint=%d  kept=%s"%(e,len(occ),len(pseudo),len(constrained),
          [(p["vt"],p["slot"],p["name"]) for p in constrained[:6]]))

json.dump(out,open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","p3_table_constraint.json"),"w",encoding="utf-8"),indent=2,ensure_ascii=False)
print("wrote EVIDENCE/p3_table_constraint.json")
