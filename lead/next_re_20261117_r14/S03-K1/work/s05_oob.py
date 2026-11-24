"""S03-K1 step5: new-size statistics (channel B byte/capstone) + out-of-bounds write scan.
CCFileClass ctor=0x4739F0 size expected 0x6C; MixFileClass ctor=0x5B3C20 size expected 0x28.
"""
import sys, os, re
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *
import capstone

b=Bin(); E=os.path.join(os.path.dirname(__file__),'..','EVIDENCE'); out=[]
calls,jmps,meta=scan_calls(b)

def new_size_before(site, lookback=0x50):
    """Walk backward from call site: find nearest 'push imm8; call 0x7C8E17' (operator new)."""
    start=site-lookback
    insns=disasm_range(b,start,site,skipdata=True)
    best=None
    for ins in insns:
        if ins.id==0: continue
        if ins.mnemonic=='call' and ins.op_str=='0x7c8e17':
            # previous insn should be push imm
            idx=insns.index(ins)
            for j in range(idx-1,max(-1,idx-3),-1):
                pi=insns[j]
                if pi.mnemonic=='push' and pi.op_str.startswith('0x'):
                    best=int(pi.op_str,16); break
            if best is not None: break
    return best

for name,ctor,expect in (('CCFileClass',0x4739F0,0x6C),('MixFileClass',0x5B3C20,0x28)):
    sites=calls.get(ctor,[])
    out.append(f"\n===== {name} ctor {ctor:08X}: {len(sites)} call sites; expected size {expect:#x} =====")
    sizes={}
    for s in sites:
        sz=new_size_before(s)
        sizes[sz]=sizes.get(sz,0)+1
    out.append("  new-size distribution: "+" ".join(f"{k if k is None else hex(k)}:{v}" for k,v in sorted(sizes.items(),key=lambda x:(x[0] is None,x[0] or 0))))

# ---- out-of-bounds write scan inside ctors ----
# Find all 'mov [reg+disp], ...' writes where reg is the this pointer.
# Mix ctor: this=esi (mov esi,ecx at +8). CC ctor: this=esi too.
def scan_writes(start,end,thisreg,size,label):
    insns=disasm_range(b,start,end,skipdata=True)
    writes=[]
    for ins in insns:
        if ins.id==0: continue
        mnem=ins.mnemonic
        if not mnem.startswith('mov'): continue
        try:
            ops=ins.operands
        except Exception:
            continue
        if len(ops)>=2 and ops[0].type==capstone.x86.X86_OP_MEM:
            mem=ops[0].mem
            basename=ins.reg_name(mem.base) if mem.base else None
            if basename==thisreg and mem.index==0 and mem.disp>=0:
                width=ops[0].size
                writes.append((ins.address,mem.disp,width,ins.mnemonic,ins.op_str))
    # also rep stos / direct disp writes not via thisreg handled separately in report
    oob=[w for w in writes if w[1]+w[2]>size]
    out.append(f"\n===== {label}: this=[{thisreg}], size={size:#x}, {len(writes)} [reg+disp] writes, {len(oob)} OOB =====")
    for w in writes:
        out.append(f"  {w[0]:08X}  +0x{w[1]:02X} w{w[2]}  {w[3]} {w[4]}")
    if oob:
        out.append("  !! OOB:")
        for w in oob: out.append("    "+" ".join(hex(x) if isinstance(x,int) else x for x in w))
    return writes,oob

w_mix,o_mix=scan_writes(0x5B3C20,0x5B3E89,'esi',0x28,'MixFileClass ctor')
w_cc,o_cc=scan_writes(0x4739F0,0x473AE0,'esi',0x6C,'CCFileClass ctor')

open(os.path.join(E,'E06_newsize_oob.txt'),'w',encoding='utf-8').write("\n".join(out))
print("\n".join(out))
