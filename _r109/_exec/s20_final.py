import sys,struct,json,collections,array,bisect,time
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r109/_exec')
from pe import *
from pe import _img
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
TL,TH=0x401000,0x7e1000; SPAN=TH-TL
md=Cs(CS_ARCH_X86,CS_MODE_32)
W='/home/t628/projects/ra2-campaign-forge/_r109/_exec/'
raw=open(W+'_insn.bin','rb').read(); n=len(raw)//5
STARTS=array.array('I'); STARTS.frombytes(raw[:4*n])
SIZES=array.array('B'); SIZES.frombytes(raw[4*n:])
size_by=dict(zip(STARTS,SIZES)); ISS=bytearray(SPAN)
for a in STARTS: ISS[a-TL]=1
seg=_img[foff(TL):foff(TL)+SPAN]
t0=time.time()

# ---------- entry evidence ----------
callt=set(); jmpt=set()
for a in STARTS:
    k=a-TL; b=seg[k]; s=size_by[a]
    if b==0xE8 and s==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: callt.add(t)
    elif b==0xE9 and s==5:
        t=(a+5+struct.unpack('<i',seg[k+1:k+5])[0])&0xffffffff
        if TL<=t<TH: jmpt.add(t)
R=json.load(open(W+'_vt_raw.json'))
VT={int(k,16):v for k,v in R['vtables'].items()}
vtsl=set()
for k,v in VT.items():
    for j in range(v['slots']):
        e=u32(k+4*j)
        if e and TL<=e<TH and ISS[e-TL]: vtsl.add(e)
prol=set(); i=0
while True:
    i=seg.find(b'\x55\x8b\xec',i)
    if i<0: break
    if ISS[i]: prol.add(TL+i)
    i+=1
padexact={a for a in STARTS if a-TL>=1 and seg[a-TL-1] in (0xc3,0xcc) and ISS[a-TL-1]}
ENTRY=sorted(callt|jmpt|vtsl|prol|padexact)
ES=set(ENTRY)
print('entries',len(ENTRY),'%.0fs'%(time.time()-t0))

# ---------- recursive descent extents ----------
FUNC=array.array('i',bytes(4*SPAN))
ext={}; fid=0
for e in ENTRY:
    if FUNC[e-TL]!=0: continue
    fid+=1; lo=hi=e; st=[e]
    while st:
        a=st.pop()
        while TL<=a<TH and ISS[a-TL] and FUNC[a-TL]==0:
            FUNC[a-TL]=fid
            o=foff(a); ins=None
            if o is None: break
            for x in md.disasm_lite(_img[o:o+16],a): ins=x; break
            if ins is None: break
            _,sz,mn,op=ins
            if a<lo: lo=a
            if a+sz>hi: hi=a+sz
            nxt=a+sz
            if mn.startswith('ret') or mn.startswith('iret'): break
            if mn=='jmp':
                if op.startswith('0x'):
                    t=int(op,16)
                    if TL<=t<TH and ISS[t-TL]:
                        if t in ES: break
                        st.append(t); break
                break
            if mn.startswith('j') or mn.startswith('loop'):
                if op.startswith('0x'):
                    t=int(op,16)
                    if TL<=t<TH: st.append(t)
            a=nxt
    ext[fid]=(e,lo,hi)
print('funcs',fid,'%.0fs'%(time.time()-t0))
ents=sorted((v[0],k) for k,v in ext.items()); es=[x[0] for x in ents]
def owner_of(a):
    j=bisect.bisect_right(es,a)-1; best=None
    while j>=0:
        e,f=ents[j]; lo,hi=ext[f][1],ext[f][2]
        if lo<=a<hi: best=e; break
        j-=1
    if best is not None: return best,'contain'
    j=bisect.bisect_right(ENTRY,a)-1
    return (ENTRY[j],'nearest') if j>=0 else (None,'none')

D=json.load(open(W+'_dispatch.json'))
own=collections.Counter(); how=collections.Counter(); owner_map={}
for d in D:
    o,h=owner_of(d['va']); own[o]+=1; how[h]+=1; owner_map[d['va']]=o
OWNERS=[o for o in own if o is not None]
print('owners_total',len(OWNERS),dict(how),'%.0fs'%(time.time()-t0))

# ---------- A1: vtable slot index with thunk following ----------
def dec(a,n=8):
    o=foff(a)
    if o is None: return []
    return list(md.disasm_lite(_img[o:o+48],a))[:n]
def dj(i): return i[2]=='jmp' and i[3].startswith('0x')
def follow(a,limit=8):
    cur=a; ch=0
    while ch<limit:
        ins=dec(cur,8)
        if not ins: return cur,'nocode'
        m0=ins[0]
        if dj(m0): cur=int(m0[3],16); ch+=1; continue
        if m0[2]=='mov' and m0[3].startswith('eax, dword ptr [esp + 4'):
            k=1
            if len(ins)>1 and ins[1][2] in ('add','sub') and ins[1][3].startswith('eax,'): k=2
            if len(ins)>k and dj(ins[k]): cur=int(ins[k][3],16); ch+=1; continue
            return cur,'adjustor'
        if m0[2] in ('sub','add') and m0[3].startswith('ecx,') and len(ins)>1 and dj(ins[1]):
            cur=int(ins[1][3],16); ch+=1; continue
        return cur,'body'
    return cur,'limit'

slot_raw={}   # func -> list of (cls, slot, vtable)
slot_thunk={}
nchg=0; kinds=collections.Counter()
for vt_va,v in sorted(VT.items()):
    for j in range(v['slots']):
        e=u32(vt_va+4*j)
        if not e: continue
        slot_raw.setdefault(e,[]).append((v['cls'],j,vt_va))
        f,kind=follow(e); kinds[kind]+=1
        if f!=e: nchg+=1
        slot_thunk.setdefault(f,[]).append((v['cls'],j,vt_va,e,kind))
print('A1 slot values',len(slot_raw),'distinct values',len({e for e in slot_raw}),
      'thunk-resolved funcs',len(slot_thunk),'chains changed',nchg,dict(kinds))

# ---------- A2: vtable assembler sites ----------
seg2=seg
sites=[]
i=0
while True:
    i=seg2.find(b'\xc7',i)
    if i<0: break
    if i+6>SPAN: break
    modrm=seg2[i+1]
    if ((modrm>>3)&7)!=0: i+=1; continue
    mod=(modrm>>6)&3; rm=modrm&7
    length=None; disp=None; based=None
    if mod==0 and rm==5:
        length=10; disp=struct.unpack('<I',seg2[i+2:i+6])[0]
    elif mod==0 and rm==4:
        if i+11>SPAN: i+=1; continue
        sib=seg2[i+2]; b=sib&7
        if b==5: length=11; disp=struct.unpack('<I',seg2[i+3:i+7])[0]
        else: length=10; disp=0; based=b
    elif mod==0:
        length=6; disp=0; based=rm
    elif mod==1:
        length=7 if rm!=4 else 8; disp=struct.unpack('<b',seg2[i+2:i+3])[0]
        if rm!=4: based=rm
        else: based=seg2[i+2]&7
    elif mod==2:
        length=10 if rm!=4 else 11; disp=struct.unpack('<I',seg2[i+2:i+6])[0]
        if rm!=4: based=rm
        else: based=seg2[i+2]&7
    if length is None or i+length>SPAN: i+=1; continue
    va=TL+i
    if not ISS[i]: i+=1; continue
    imm=struct.unpack('<I',seg2[i+length-4:i+length])[0]
    if imm in VT:
        sites.append(dict(va=va,disp=disp,imm=imm,based=based,mod=mod,rm=rm,
                          nbytes=length,bytes=seg2[i:i+length].hex(),
                          cls=VT[imm]['cls'],vt_offset=VT[imm]['offset']))
    i+=1
REG=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
for s in sites: s['basereg']=REG[s['based']] if s['based'] is not None else 'ABS'
print('A2 raw immediate-store sites in vtable set:',len(sites))
print('  base reg hist',collections.Counter(s['basereg'] for s in sites).most_common())
obj=[s for s in sites if s['basereg'] not in ('esp','ABS')]
print('  object stores (base != esp, non-absolute):',len(obj))
json.dump(dict(all_sites=sites,n_all=len(sites),n_obj=len(obj)),
          open(W+'_ctor_sites.json','w'))
json.dump(dict(owners_total=len(OWNERS),how=dict(how),
               owner_of={hex(k):(v if v is None else hex(v)) for k,v in owner_map.items()},
               counts={hex(k):v for k,v in own.items() if k}),
          open(W+'_owner_dispatch.json','w'))
print('done %.0fs'%(time.time()-t0))
