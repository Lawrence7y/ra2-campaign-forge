from base import BUF, IB, u32, s32, TEXT, RDATA, blob
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from collections import Counter, deque
md = Cs(CS_ARCH_X86, CS_MODE_32); md.skipdata=True
tlo,thi=TEXT["va"],TEXT["va"]+TEXT["vsize"]
insns={i.address:(i.size,i.mnemonic,i.op_str) for i in md.disasm(bytes(BUF[tlo-IB:thi-IB]),tlo)}
starts=set()
for a,(sz,mn,op) in insns.items():
    if mn.startswith("ret"):
        n=a+sz
        while n in insns and insns[n][1]=="nop": n+=insns[n][0]
        if n in insns: starts.add(n)
starts.add(tlo); starts=sorted(starts)
import bisect
def owner(a):
    i=bisect.bisect_right(starts,a)-1
    return starts[i] if i>=0 else None

print("=== PlayerClass (the class owning HouseClass) forwarders: find PlayerClass vtables ===")
needle=b".?AVPlayerClass@@"
lo,hi=0x007E1000,0x00811074
hits=[]
for va in range(lo,hi-20):
    if blob(va,16)==needle: hits.append(va)
print("  name at:", ["%08X"%x for x in hits])
for nv in hits:
    td=nv-8
    print("  TD=%08X TD+0x00=%08X" % (td,u32(td)))
    # find COLs pointing to this TD
    for c in range(lo,hi-0x18):
        if u32(c+0xC)==td:
            vts=[v+4 for v in range(lo,hi-4) if u32(v)==c]
            print("    COL=%08X -> vtables %s" % (c,["%08X"%v for v in vts]))
            for vt in vts:
                ents=[]
                a=vt
                while a<hi-4 and tlo<=u32(a)<thi:
                    ents.append(u32(a)); a+=4
                print("      vt=%08X n=%d" % (vt,len(ents)))
                # which entries are 4-byte forwarders jmp [eax+off] to 0x4FC0B0?
                for k,v in enumerate(ents):
                    if v in insns:
                        sz,mn,op=insns[v]
                        raw=blob(v,sz)
                        if mn=="jmp" and op.startswith("dword ptr [e") and raw[:2]==b"\xff\xa0":
                            tgt=u32(v+2)
                            print("        slot %-2d %08X  jmp [eax+0x%X] -> would land %08X" % (k,v,tgt-0x4FC0B0+0x4FC0B0 if False else tgt))
