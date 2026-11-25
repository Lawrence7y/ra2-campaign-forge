import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR, bisect
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
SAVE=0x7e15f4
def feeds(ic,dbg=False):
    held={'eax'}; slots=set(); last=None
    for j in range(ic+1,min(len(ins),ic+90)):
        a,m,o=ins[j]
        if dbg: print('  %x %-7s %-34s held=%s slots=%s last=%s'%(a,m,o,sorted(held),sorted(slots),last))
        if m=='ret': return False
        if m=='mov' and ',' in o:
            d,src=[x.strip() for x in o.split(',',1)]
            if d in TR.REGS:
                if src in held: held.add(d)
                elif src.startswith('dword ptr [esp + '):
                    k=TR.num(src.split('[esp + ')[1].rstrip(']'))
                    if k in slots: held.add(d)
                    else: held.discard(d)
                else: held.discard(d)
            elif d.startswith('dword ptr [esp + '):
                k=TR.num(d.split('[esp + ')[1].rstrip(']'))
                if k is None: continue
                if src in held: slots.add(k)
                else: slots.discard(k)
        if m=='push':
            last = o.strip() if o.strip() in held else None
        if m=='call' and o=='dword ptr [0x%x]'%SAVE:
            return last is not None
    return False
i=idx[0x4af856]+2
print('ic=%x'%ins[i][0], ins[i])
print('feeds=',feeds(i,dbg=True))
