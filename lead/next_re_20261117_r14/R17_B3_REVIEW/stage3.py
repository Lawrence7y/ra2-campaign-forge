
import json, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32, x86_const
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_B3_REVIEW"
def u16(b,o): return int.from_bytes(b[o:o+2],'little')
def u32(b,o): return int.from_bytes(b[o:o+4],'little')
data=open(EXE,'rb').read()
pe=u32(data,0x3C); opt=pe+24; IMGB=u32(data,opt+28); nsec=u16(data,pe+6); optsz=u16(data,pe+20)
SECS=[]
for i in range(nsec):
    o=opt+optsz+i*40
    SECS.append(dict(name=data[o:o+8].rstrip(b'\0').decode('latin1'),va=IMGB+u32(data,o+12),rsz=u32(data,o+16),raw=u32(data,o+20)))
def rd(va,n):
    for s in SECS:
        if s['raw'] and s['va']<=va<s['va']+s['rsz']:
            off=s['raw']+(va-s['va']); return data[off:off+n]
    return b''
def dword(va):
    b=rd(va,4); return int.from_bytes(b,'little') if len(b)==4 else None
def secname(va):
    for s in SECS:
        if s['va']<=va<s['va']+s['rsz']: return s['name']
    return None
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
HOSTS=[(0x43B680,0x43B740),(0x43B740,0x43BCDE),(0x43BCF0,0x43C0D0)]
PROLOG=[0x6F4300,0x6F2B40]
res={}
for host,end in HOSTS:
    ins=list(md.disasm(rd(host,end-host),host))
    first_call=None; newcall=None
    for i in ins:
        if i.mnemonic=='call' and i.operands and i.operands[0].type==x86_const.X86_OP_IMM:
            tgt=i.operands[0].imm & 0xFFFFFFFF
            if first_call is None:
                first_call=(i.address,tgt)
            if tgt in PROLOG and newcall is None:
                newcall=(i.address,tgt)
    # classify operator new
    def classify(a):
        if a is None: return None
        mnem=None
        # will be resolved below
        return a
    res[host]=dict(fn_end=end, first_call=first_call, newcall=newcall)
# resolve operator new semantics: look at prologue target + its own callees
def peek(a, n=24):
    out=[]
    for i in md.disasm(rd(a,n*8),a):
        out.append("%#x %s %s"%(i.address,i.mnemonic,i.op_str))
        if len(out)>=n: break
    return out
# scan for allocator calls 0x7c8e17 in each host (operator new style)
print(json.dumps({hex(k):v for k,v in res.items()}, indent=1))
for p in PROLOG:
    print("== prologue %#x =="%p); print("\n".join(peek(p,12)))
    # find its own calls
    for i in md.disasm(rd(p,0x180),p):
        if i.mnemonic=='call' and i.operands[0].type==x86_const.X86_OP_IMM:
            t=i.operands[0].imm&0xFFFFFFFF
            if t!=0x6F4300 and t!=0x6F2B40:
                print("   %#x -> %#x  (sec %s)"%(i.address,t,secname(t)))
json.dump({str(k):v for k,v in res.items()}, open(os.path.join(OUT,'stage3_prologue.json'),'w'), indent=1)
