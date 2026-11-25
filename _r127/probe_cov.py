import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as TR
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
GSET={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
QS=[]
for i,(a,m,o) in enumerate(ins):
    if m!='push': continue
    t=TR.num(o)
    if t not in GSET: continue
    ic=None
    for d in (2,3):
        if i+d<len(ins) and ins[i+d][1]=='call' and ins[i+d][2].startswith('dword ptr [e'):
            ic=i+d; break
    if ic is None: continue
    QS.append((a,GSET[t],ic))
def feeds(ic):
    held={'eax'}; last=None
    pk=TR.qi_ppv_key(ins,ic)
    slots=set() if pk is None else {pk}
    for j in range(ic+1,min(len(ins),ic+90)):
        a,m,o=ins[j]
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
        if m=='push': last=o.strip() if o.strip() in held else None
        if m=='call' and o=='dword ptr [0x7e15f4]': return last is not None
    return False
for a,lab,ic in QS:
    if lab!='0109.d': continue
    print(lab,hex(a),hex(ic),'fed=',feeds(ic))
