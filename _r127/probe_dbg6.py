import sys,os
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import tracer2 as T
import pefile,capstone
pe=pefile.PE('ra2bench/gamemd.exe'); IB=pe.OPTIONAL_HEADER.ImageBase
S={s.Name.rstrip(b'\x00').decode():s for s in pe.sections}
TX=S['.text']; T_LO=TX.VirtualAddress+IB
raw=pe.get_data(TX.VirtualAddress,TX.Misc_VirtualSize)
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32); md.skipdata=True
ins=[(a,m,o) for a,s,m,o in md.disasm_lite(raw,T_LO)]
idx={a:i for i,(a,m,o) in enumerate(ins)}
i0=idx[0x4af6ab]+1
lo,hi=i0,min(len(ins),i0+150)
work=[(i0,0,{'eax':('Q',)},{12:('Q',)},0)]
seen=set()
steps=0
while work and steps<80:
    pc,dsp,reg0,stk0,nargs0=work.pop()
    reg,stk,nargs=dict(reg0),dict(stk0),nargs0
    while True:
        steps+=1
        if steps>80: break
        if pc<lo or pc>=hi: print('  exit window'); break
        a,m,o=ins[pc]
        mark=''.join(k for k,v in reg.items() if v==('Q',))
        print('  %x: %-7s %-32s dsp=%d nargs=%d Q=%s VT=%s'%(a,m,o,dsp,nargs,mark,
              ''.join(k for k,v in reg.items() if v==('VT',))))
        if m=='ret': break
        if m=='push': dsp-=4; nargs+=1; pc+=1; continue
        if m=='pop':
            dsp+=4; nargs=max(0,nargs-1)
            if o.strip() in T.REGS: reg.pop(o.strip(),None)
            pc+=1; continue
        if m in ('add','sub') and o.strip().startswith('esp, '):
            v=T.num(o.split(',',1)[1]) or 0
            dsp+= v if m=='add' else -v; nargs=0; pc+=1; continue
        if m=='mov' and ',' in o:
            d,src=[x.strip() for x in o.split(',',1)]
            v=T._eval(src,reg,stk,dsp)
            print('        mov %s <- %s => %s'%(d,src,v))
            if d in T.REGS:
                if v is None: reg.pop(d,None)
                else: reg[d]=v
            else:
                b,disp=T.parse_mem(d)
                print('        parse_mem(%s) = %s'%(d,(b,disp)))
                if b=='esp':
                    k=dsp+disp
                    if v is None: stk.pop(k,None)
                    else: stk[k]=v
            pc+=1; continue
        if m=='call':
            print('        CALL')
            reg.pop('eax',None); dsp+=4*nargs; nargs=0; pc+=1; continue
        if m=='jmp':
            t=T.num(o); nxt=T._index_of(ins,t,lo,hi) if t is not None else None
            if nxt is None: print('        jmp out'); break
            pc=nxt; continue
        if m.startswith('j'):
            t=T.num(o)
            if t is not None:
                nxt=T._index_of(ins,t,lo,hi)
                if nxt is not None: work.append((nxt,dsp,reg,stk,0))
            pc+=1; continue
        if ',' in o:
            d=o.split(',',1)[0].strip()
            if d in T.REGS: reg.pop(d,None)
        pc+=1
