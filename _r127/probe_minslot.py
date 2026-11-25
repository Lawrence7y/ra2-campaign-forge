import bisect,collections
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
T=S['.text']; T_LO=T.VirtualAddress+IB
raw=pe.get_data(T.VirtualAddress,T.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
A=[a for a,m,o in ins]; idx={a:i for i,(a,m,o) in enumerate(ins)}
def num(t):
    t=t.strip()
    if t and t[0] in '0123456789':
        try: return int(t,0)
        except ValueError: pass
    return None
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
def reg_of(ops):
    return ops.split(',')[0].strip()
def mem_of(ops):
    return ops.split(',',1)[1].strip()
def slots_after(i,ppv_slot,limit=70):
    """ppv_slot: stack offset (int) holding the QI result, or None.
    Track aliases: regs holding the object pointer, and regs holding [obj] (vtable)."""
    obj_regs=set(); vt_regs=set(); slots=[]; ev=[]
    # after the call (i+2 is call), result in eax
    j=i+3
    while j<min(len(ins),i+limit):
        a,m,o=ins[j]
        if m=='ret' : break
        if m=='mov':
            d,src=reg_of(o),mem_of(o)
            tgt=src
            if d in ('eax','ebx','ecx','edx','esi','edi','ebp'):
                if tgt=='eax' and d in obj_regs: pass
                if tgt=='eax': obj_regs.add(d)
                elif tgt in obj_regs: obj_regs.add(d)
                elif tgt=='[%s]'%d or tgt.startswith('dword ptr ['):
                    pass
            # mov reg,[objreg]
            if tgt.startswith('dword ptr ['):
                base=tgt[len('dword ptr ['):].rstrip(']').split(' + ')[0].split(' - ')[0]
                if base in obj_regs and d in ('eax','ebx','ecx','edx','esi','edi'):
                    vt_regs.add(d)
            # mov reg,[esp+K]
            if tgt.startswith('dword ptr [esp + '):
                pass
        if m=='call' and o.startswith('dword ptr ['):
            inner=o[len('dword ptr ['):].rstrip(']')
            base=inner.split(' + ')[0]
            k=num(inner.split(' + ')[1]) if ' + ' in inner else 0
            if base in vt_regs and k is not None:
                slots.append((hex(a),k)); ev.append('%s: %s %s'%(hex(a),m,o))
            elif base in obj_regs:
                slots.append((hex(a),0))
        j+=1
    return slots
for i,(a,m,o) in enumerate(ins):
    if m=='push' and num(o) in G:
        g=G[num(o)]
        # ppv from instruction i-1 (lea reg,[esp+K]) or i-2
        ppv=None
        for b in (1,2):
            p=ins[i-b]
            if p[1]=='lea' and '[esp + ' in p[2]:
                ppv=num(p[2].split('[esp + ')[1].rstrip(']')); break
        print('%-7s site %x ppv=%s slots=%s'%(g,a,ppv,slots_after(i,ppv)[:6]))
