"""Supplement: full 0x5683C0 wrapper head; object identity at call site;
writes to byte [reg+0x8C] near BuildingClass; CellClass RTTI/GetSize.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
import capstone
from re_helper import Bin, disasm_range, fmt_insn, md, load_atlas, EVID

b=Bin(); L=[]
L.append("0x5683C0 wrapper (full, atlas size 1068)")
L.append("="*80)
for ins in disasm_range(b,0x5683C0,0x5683C0+1068,skipdata=True): L.append(fmt_insn(ins))
L.append("")
L.append("byte [reg+0x8C] WRITES in .text (all operands)")
L.append("="*80)
m=md(skipdata=True); t=b.sec(".text")
data=b.pe.__data__[t["raw"]:t["raw"]+t["rawsize"]]
rows,_=load_atlas()
def fnof(va):
    for r in rows:
        if r["_va"]<=va<r["_va"]+r["_size"]: return r["_va"]
    return None
w8c=[]
for ins in m.disasm(data,t["va"]):
    if ins.id==0: continue
    for op in ins.operands:
        if op.type==capstone.x86.X86_OP_MEM and op.mem.base!=0 and op.mem.disp==0x8C and op.size==1:
            if op.access in (capstone.CS_AC_WRITE, capstone.CS_AC_READ|capstone.CS_AC_WRITE):
                w8c.append((ins.address,ins.mnemonic,ins.op_str,fnof(ins.address)))
L.append("count=%d"%len(w8c))
for a,mn,os_,fn in w8c[:80]: L.append("  %08X %-8s %-46s fn=%s"%(a,mn,os_,("%08X"%fn) if fn else "?"))

L.append("")
L.append("CellClass RTTI + GetSize")
L.append("="*80)
# find TD name .?AVCellClass@@
rdata=b.sec(".rdata"); buf=b.pe.__data__[rdata["raw"]:rdata["raw"]+rdata["rawsize"]]
pat=b".?AVCellClass@@"; off=0; hits=[]
while True:
    i=buf.find(pat,off)
    if i<0: break
    nameva=rdata["va"]+i
    td=nameva-8
    # find COLs with TD at +0xC
    tp=td.to_bytes(4,"little"); off2=0
    while True:
        j=buf.find(tp,off2)
        if j<0: break
        col=rdata["va"]+j-0xC
        # find vtables with COL at vt-4
        cp=col.to_bytes(4,"little"); off3=0
        while True:
            k=buf.find(cp,off3)
            if k<0: break
            vt=rdata["va"]+k+4
            if vt%4==0:
                try:
                    gs=b.u32(vt+0x30)
                    code=b.read(gs,8)
                    sz=int.from_bytes(code[1:5],"little") if code[0]==0xB8 and code[5]==0xC3 else None
                    L.append("  td=%08X col=%08X vt=%08X slot73=%08X GetSize=%08X size=%s bytes=%s"%(
                        td,col,vt,b.u32(vt+0x124),gs,("%08X"%sz) if sz is not None else "?",code.hex()))
                except Exception as e: L.append("  err %s"%e)
            off3=k+1
        off2=j+1
    off=i+1

out=os.path.join(EVID,"t2_wrapper_and_8c_cellclass.txt")
with open(out,"w",encoding="utf-8") as f: f.write("\n".join(L)+"\n")
print("wrote",out,"lines",len(L),"w8c",len(w8c))
