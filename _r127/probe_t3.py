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
IAT={0x7e15f4:'OleSaveToStream',0x7e15f8:'OleLoadFromStream'}
G={0x7f7c70:'010C.r',0x818858:'010C.d',0x7f7c80:'0109.r',0x820270:'0109.d'}
def ppv_key(ic):
    for b in range(2,8):
        p=ins[ic-b]
        if p[1]=='lea' and '[esp + ' in p[2]:
            tgt=p[2].split(',',1)[0].strip()
            k=T.num(p[2].rsplit(' + ',1)[1].rstrip(']'))
            if k is None: return None
            pushes=[j for j in range(ic-b+1,ic+1) if ins[j][1]=='push']
            if not any(ins[j][2].strip()==tgt for j in pushes): return None
            return 4*len(pushes)+k
    return None
for i,(a,m,o) in enumerate(ins):
    if m=='push' and T.num(o) in G and ins[i+1][1]=='push' and ins[i+2][1]=='call':
        ic=i+2
        pk=ppv_key(ic)
        # seed: instrument by patching tracer to accept seed stk
        import copy
        orig=T.walk
        def walk_seed(ins, i0, window, seed_objin='eax', _pk=pk):
            lo,hi=i0,min(len(ins),i0+window)
            work=[(i0,0,{seed_objin:('Q',)},{_pk:('Q',)})] if _pk is not None else [(i0,0,{seed_objin:('Q',)},)]
            seen=set(); slots=set(); iatcalls=[]; steps=0; trunc=False
            while work:
                pc,dsp,reg0,stk0=work.pop(); reg,stk=dict(reg0),dict(stk0)
                while True:
                    steps+=1
                    if steps>T.MAXSTEP: trunc=True; break
                    if pc<lo or pc>=hi: break
                    sig=(pc,dsp,tuple(sorted(reg.items())))
                    if sig in seen: break
                    seen.add(sig)
                    a2,m2,o2=ins[pc]
                    if m2=='ret': break
                    if m2=='push': dsp-=4; pc+=1; continue
                    if m2=='pop':
                        dsp+=4
                        if o2.strip() in T.REGS: reg.pop(o2.strip(),None)
                        pc+=1; continue
                    if m2 in ('add','sub') and o2.strip().startswith('esp, '):
                        v=T.num(o2.split(',',1)[1]) or 0
                        dsp+= v if m2=='add' else -v
                        pc+=1; continue
                    if m2=='mov' and ',' in o2:
                        d,src=[x.strip() for x in o2.split(',',1)]
                        v=T._eval(src,reg,stk,dsp)
                        if d in T.REGS:
                            if v is None: reg.pop(d,None)
                            else: reg[d]=v
                        else:
                            b2,disp=T.parse_mem(d)
                            if b2=='esp':
                                k=dsp+disp
                                if v is None: stk.pop(k,None)
                                else: stk[k]=v
                        pc+=1; continue
                    if m2=='xor' and ',' in o2:
                        d,s2=[x.strip() for x in o2.split(',',1)]
                        if d==s2 and d in T.REGS: reg[d]=('IMM',0)
                        pc+=1; continue
                    if m2=='lea' and ',' in o2:
                        d=o2.split(',',1)[0].strip()
                        if d in T.REGS: reg.pop(d,None)
                        pc+=1; continue
                    if m2=='call':
                        tgt=o2.strip()
                        if tgt.startswith('dword ptr ['):
                            inner=tgt[len('dword ptr ['):-1]
                            b2,disp=T.parse_mem('dword ptr [%s]'%inner)
                            if b2 in T.REGS:
                                if reg.get(b2)==('VT',) and disp is not None: slots.add(disp)
                            elif b2 and b2[0]=='abs': iatcalls.append((a2,b2[1]))
                        reg.pop('eax',None)
                        pc+=1; continue
                    if m2=='jmp':
                        t=T.num(o2)
                        nxt=T._index_of(ins,t,lo,hi) if t is not None else None
                        if nxt is None: break
                        pc=nxt; continue
                    if m2.startswith('j'):
                        t=T.num(o2)
                        if t is not None:
                            nxt=T._index_of(ins,t,lo,hi)
                            if nxt is not None: work.append((nxt,dsp,reg,stk))
                        pc+=1; continue
                    if ',' in o2:
                        d=o2.split(',',1)[0].strip()
                        if d in T.REGS: reg.pop(d,None)
                    pc+=1
            return {'slots':slots,'iatcalls':iatcalls,'truncated':trunc,'steps':steps}
        r=walk_seed(ins,ic+1,140)
        print('%-7s %x pk=%s slots=%s iat=%s trust=%s'%(G[T.num(o)],a,pk,
              sorted(hex(x) for x in r['slots']),
              sorted({IAT.get(v,hex(v)) for x,v in r['iatcalls']}), r['truncated']))
