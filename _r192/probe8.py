import sys,struct,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VF=0x7F9594
TD={}
for sn in ('.data','.rdata'):
    base,w,n=wv(sn)
    for i in range(n-2):
        if w[i]!=VF: continue
        va=base+4*i; nm=P.cstr(va+8,160)
        if nm and nm.startswith(b'.?A') and nm.endswith(b'@@'): TD[va]=nm.decode('latin1')
def bcds(c):
    nb=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12)
    return [P.dw(arr+4*j) for j in range(nb)]
stat=collections.Counter(); virt=0; examples=[]
for va,c in COL.items():
    cand=[b for b in bcds(c) if b is not None and P.dw(b)==c['ptd']]
    if len(cand)==0: stat['noTDmatch']+=1; continue
    # pick by mdisp equality first
    eq=[b for b in cand if P.dw(b+8)==c['mdisp']]
    if len(eq)==1 and len(cand)==1: stat['exact']+=1
    elif len(eq)==1: stat['exact_multi']+=1
    elif len(eq)>1: stat['ambiguous']+=1
    else:
        # virtual base: PMD.mdisp == -1
        vm=[b for b in cand if P.dw(b+8)==0xFFFFFFFF]
        if len(vm)>=1:
            stat['virt']+=1; virt+=1
            if len(examples)<6: examples.append((c['name'],c['mdisp'],len(cand),[(hex(b),P.dw(b+8),P.dw(b+12),P.dw(b+16)) for b in cand[:4]]))
        else: stat['other']+=1
print(dict(stat))
print('virt examples:')
for e in examples: print('  ',e)
# distribution of vdisp for virt
vd=collections.Counter(); md=collections.Counter()
for va,c in COL.items():
    cand=[b for b in bcds(c) if b is not None and P.dw(b)==c['ptd']]
    vm=[b for b in cand if P.dw(b+8)==0xFFFFFFFF]
    if vm: vd[P.dw(vm[0]+12)]+=1; md[c['mdisp']]+=1
print('virt vdisp dist',dict(sorted(vd.items())[:10]),'count',sum(vd.values()))
print('virt COL.mdisp dist',dict(sorted(md.items())))
