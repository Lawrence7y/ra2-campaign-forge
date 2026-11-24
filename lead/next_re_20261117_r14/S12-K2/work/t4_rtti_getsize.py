"""T4: RTTI class-name recovery from vtable->COL->TD (chain: [vt-4]=COL,
TD=[COL+0xC], name=TD+8). Fail-closed. GetSize = vtable slot 12 @ +0x30,
verify B8 <imm32> C3. Then find constructor 'push <size>' allocation sites.
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from re_helper import Bin, disasm_range, fmt_insn, md, EVID

b=Bin(); L=[]
def u32(va): return b.u32(va)
def col_td_name(vt):
    try:
        col=u32(vt-4)
        if not (0x400000<=col<0x900000): return (col,None,None,"COL out of range")
        td=u32(col+0xC)
        if not (0x400000<=td<0x900000): return (col,td,None,"TD out of range")
        # name at TD+8, null-terminated
        raw=b.read(td+8,80)
        end=raw.find(b"\x00")
        if end<0: return (col,td,None,"no NUL")
        name=raw[:end].decode("ascii",errors="replace")
        if not name or name=="?": return (col,td,name,"empty/?")
        return (col,td,name,"ok")
    except Exception as e:
        return (None,None,None,str(e))

# find vtables by slot73 value: scan .rdata for value at [addr+0x124]
L.append("RTTI recovery for vtables whose slot73 (offset +0x124) is a known function")
L.append("chain: [vt-4]=COL ; TD=[COL+0xC] ; name=TD+8  (fail-closed)")
L.append("="*88)
rdata_sec=b.sec(".rdata")
buf=b.pe.__data__[rdata_sec["raw"]:rdata_sec["raw"]+rdata_sec["rawsize"]]
vbase=rdata_sec["va"]
slot73_targets={0x43F180:"Building slot73",0x4D3780:"Unit/Inf/Air slot73",
                0x6F4A70:"Techno base slot73",0x4151E0:"? slot73",0x71BFB0:"? slot73"}
for tgt,label in slot73_targets.items():
    pat=tgt.to_bytes(4,"little"); off=0; hits=[]
    while True:
        i=buf.find(pat,off)
        if i<0: break
        loc=vbase+i          # this is vt+0x124
        vt=loc-0x124
        if vt%4==0:
            col,td,name,why=col_td_name(vt)
            hits.append((vt,col,td,name,why))
        off=i+1
    L.append("slot73=%08X (%s): %d candidate vtable locs"%(tgt,label,len(hits)))
    seen=set()
    for vt,col,td,name,why in hits:
        if vt in seen: continue
        seen.add(vt)
        L.append("   vt=%08X col=%s td=%s name=%r why=%s"%(vt,("%08X"%col) if col else "?",("%08X"%td) if td else "?",name,why))

# BuildingClass vtable given by R14: 0x7E3EBC. Verify + GetSize.
L.append(""); L.append("="*88); L.append("BuildingClass vtable 0x7E3EBC per R14_COMMON §2: RTTI chain + GetSize"); L.append("="*88)
vt=0x7E3EBC
col,td,name,why=col_td_name(vt)
L.append("vt=%08X col=%s td=%s name=%r why=%s"%(vt,("%08X"%col) if col else "?",("%08X"%td) if td else "?",name,why))
# verify slot73
L.append("slot73 [vt+0x124]=%08X"%u32(vt+0x124))
getsize=u32(vt+0x30)
L.append("GetSize slot12 [vt+0x30]=%08X"%getsize)
try:
    code=b.read(getsize,8)
    L.append("bytes: %s"%code.hex())
    if code[0]==0xB8 and code[5]==0xC3:
        sz=struct.unpack("<I",code[1:5])[0]
        L.append("GetSize=0x%X (%d) via B8 imm32 C3"% (sz,sz))
    else:
        sz=None
        for ins in disasm_range(b,getsize,getsize+16,skipdata=True): L.append(fmt_insn(ins))
except Exception as e: L.append("GetSize read fail %s"%e); sz=None

# find push <size> allocation sites in .text
if sz is not None:
    L.append(""); L.append("'push 0x%X' allocation sites in .text (68 imm32):"%sz)
    pat=b"\x68"+sz.to_bytes(4,"little")
    t=b.sec(".text"); tb=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
    off=0; hits=[]
    while True:
        i=tb.find(pat,off)
        if i<0: break
        va=t["va"]+i; hits.append(va); off=i+1
    L.append("count=%d: %s"%(len(hits)," ".join(hex(x) for x in hits[:60])))
    for h in hits[:20]:
        L.append("  ctx %08X:"%h)
        for ins in disasm_range(b,h-4,h+12,skipdata=True): L.append("    "+fmt_insn(ins))

# also known BuildingClass GetSize alternative: dump slot12 for all candidate vtables found
L.append(""); L.append("="*88); L.append("GetSize(slot12) for all named candidate vtables"); L.append("="*88)
for vt in sorted(set(h[0] for hh in slot73_targets for h in [])): pass

out=os.path.join(EVID,"t4_rtti_getsize.txt")
with open(out,"w",encoding="utf-8") as f: f.write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L))
