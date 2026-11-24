
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
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True
def fn(host,maxlen=0x400):
    ins=[]
    for i in md.disasm(rd(host,maxlen),host):
        ins.append(i)
        if i.mnemonic in ('ret','retn'): break
    return ins
lines=[]
for a in (0x7C8E17,0x7C8B3D):
    lines.append("== %#x =="%a)
    for i in fn(a,0x120):
        lines.append("%#x %-20s %s %s"%(i.address,i.bytes.hex(),i.mnemonic,i.op_str))
# also: epilogue checks - search whole 3 hosts for 'test' of a flag after a vtable/imm store, and for [esp+..],1 patterns
def scan(host,end):
    out=[]
    ins=list(md.disasm(rd(host,end-host),host))
    for i in ins:
        s=i.mnemonic+" "+i.op_str
        if (i.mnemonic=='test' ) or (', 1' in s and i.mnemonic in ('mov','push')) or (i.mnemonic=='or' and 'ptr [esp' in s):
            out.append("  %#x %s %s"%(i.address,i.mnemonic,i.op_str))
    return out
for host,end in [(0x43B680,0x43B740),(0x43B740,0x43BCDE),(0x43BCF0,0x43C0D0)]:
    lines.append("== delete/test signature scan %#x..%#x =="%(host,end))
    lines += scan(host,end) or ["  (none)"]
# check whether slot fn ptrs are vtables (i.e., whether 0x7E3Exx is pointed to by any vftable) 
lines.append("== slot content addresses mean anything? call targets from constructors ==")
open(os.path.join(OUT,'stage4.txt'),'w',encoding='utf8').write("\n".join(lines))
print("\n".join(lines))
