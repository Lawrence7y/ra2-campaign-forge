import bisect,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
def num(t):
    t=t.strip()
    if t and t[0] in '0123456789':
        try: return int(t,0)
        except ValueError: pass
    return None
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
REGS=('eax','ebx','ecx','edx','esi','edi','ebp')
def analyze(i):
    """i = index of push riid. Returns (ppv_slot, obj_reg, calls) where calls are
       (addr, base_desc, offset) virtual calls reachable on the QI result."""
    a,m,o=ins[i]
    # caller shape: [push ppv][push riid][push this][mov ecx,[this]][call [ecx]]
    ppv=None; objexpr=None
    for b in range(1,5):
        p=ins[i-b]
        if p[1]=='lea' and '[esp + ' in p[2]:
            ppv=('esp',num(p[2].split('[esp + ')[1].rstrip(']'))); break
        if p[1]=='push':
            ppv=('reg',p[2]); break
    # find the call and its target slot
    call=None
    for j in range(i+1,i+6):
        if ins[j][1]=='call': call=j; break
    if call is None: return None
    # track: after the call eax = result. Then follow simple copies.
    held=set(['eax'])          # regs holding result pointer
    slots=set()                # stack slots holding result
    vt={}                      # reg -> base reg of its vtable
    calls=[]; ole=[]
    j=call+1
    while j<min(len(ins),call+90):
        a2,m2,o2=ins[j]
        if m2=='ret': break
        if m2=='mov' and ',' in o2:
            d,src=[x.strip() for x in o2.split(',',1)]
            if d in REGS:
                if src in held: held.add(d)
                elif src.startswith('dword ptr [esp + '):
                    k=num(src.split('[esp + ')[1].rstrip(']'))
                    if k in slots: held.add(d)
                elif src.startswith('dword ptr [') and src.endswith(']'):
                    base=src[len('dword ptr ['):-1].split(' + ')[0]
                    if base in held: vt[d]=base
                else:
                    held.discard(d); vt.pop(d,None)
            elif d.startswith('dword ptr [esp + '):
                k=num(d.split('[esp + ')[1].rstrip(']'))
                if src in held: slots.add(k)
        elif m2=='call':
            if o2.startswith('dword ptr ['):
                inner=o2[len('dword ptr ['):-1]
                base=inner.split(' + ')[0]
                off=num(inner.split(' + ')[1]) if ' + ' in inner else 0
                if base in vt and off is not None:
                    calls.append((hex(a2),base,off,vt[base]))
                elif base.startswith('0x'):
                    ole.append((hex(a2),base,off))
            elif num(o2) is not None:
                pass
        j+=1
    return {'ppv':ppv,'calls':calls,'ole_direct':ole}
for i,(a,m,o) in enumerate(ins):
    if m=='push' and num(o) in G:
        r=analyze(i)
        if r is None: print(G[num(o)],hex(a),'NO-CALL'); continue
        print('%-7s %x ppv=%s slotcalls=%s oledirect=%s'%(G[num(o)],a,r['ppv'],
              [(c[0],c[2],c[3]) for c in r['calls']],r['ole_direct']))
