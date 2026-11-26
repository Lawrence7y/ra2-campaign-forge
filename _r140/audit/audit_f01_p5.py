import struct,os,collections
ROOT='/home/t628/projects/ra2-campaign-forge';data=open(os.path.join(ROOT,'ra2bench','gamemd.exe'),'rb').read()
pe=struct.unpack_from('<I',data,0x3c)[0];nsec=struct.unpack_from('<H',data,pe+6)[0]
optsz=struct.unpack_from('<H',data,pe+20)[0];opt=pe+24;IB=struct.unpack_from('<I',data,opt+28)[0]
st=opt+optsz;SECS=[]
for i in range(nsec):
    o=st+40*i;nm=data[o:o+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,rp=struct.unpack_from('<IIII',data,o+8)
    SECS.append(dict(name=nm,rva=va,rs=rs,rp=rp,va_lo=IB+va,va_hi=IB+va+max(vs,rs)))
S={s['name']:s for s in SECS};TEXT=S['.text'];RDATA=S['.rdata'];DATA=S['.data']
def r2v(o):
    for s in SECS:
        if s['rp']<=o<s['rp']+s['rs']: return IB+s['rva']+(o-s['rp'])
def v2r(va):
    for s in SECS:
        if s['va_lo']<=va<s['va_lo']+s['rs']: return s['rp']+(va-s['va_lo'])
def rd(va):
    o=v2r(va)
    return None if o is None or o+4>len(data) else struct.unpack_from('<I',data,o)[0]
def inse(va,s): return s['va_lo']<=va<s['va_hi']
def sec(va):
    for s in SECS:
        if s['va_lo']<=va<s['va_hi']: return s['name']
tds={}
for s in (RDATA,DATA):
    b=data[s['rp']:s['rp']+s['rs']]
    for tag in (b'.?AV',b'.?AU'):
        i=b.find(tag)
        while i!=-1:
            e=i
            while e<len(b) and e-i<256 and 0x20<=b[e]<=0x7e: e+=1
            x=b[i:e].decode('latin1')
            if x.endswith('@@') and len(x)>=8:
                sv=r2v(s['rp']+i);a,c=rd(sv-8),rd(sv-4)
                if a is not None and c==0 and (inse(a,RDATA) or inse(a,DATA)): tds[sv-8]=x
            i=b.find(tag,i+1)
dw={}
for s in SECS:
    for o in range(s['rp'],s['rp']+s['rs']-3,4): dw[o]=struct.unpack_from('<I',data,o)[0]
cols=sorted({r2v(o)-12 for o,v in dw.items() if v in tds and dw.get(v2r(r2v(o)-12))==0 and rd(r2v(o))==v})
cs=set(cols);refs=collections.defaultdict(list)
for o,v in dw.items():
    if v in cs: refs[v].append(r2v(o)+4)
kept=[c for c in cols if rd(c+16)!=0]
def cnt(c,n,kind):
    k=0
    for i in range(n):
        v=rd(c+4*i)
        if v is None: break
        if kind=='text':
            if inse(v,TEXT): k+=1
        elif kind=='any':
            if any(inse(v,s) for s in SECS): k+=1
        elif kind=='ptr':
            if v!=0: k+=1
    return k
print('C5 criterion comparison, base 1216 / first 64 slots')
for kind in ('text','any','ptr'):
    b={c:max([cnt(v,64,kind) for v in refs.get(c,())],default=-1) for c in cols}
    print('  %-5s k2..k12: %s'%(kind,' '.join('%d:%d'%(k,sum(1 for c in cols if b[c]>=k)) for k in range(2,13))))
    print('        exit cliff: %s'%' '.join('%d->%d:%d'%(k,k+1,sum(1 for c in cols if b[c]>=k)-sum(1 for c in cols if b[c]>=k+1)) for k in range(2,12)))
print('\n1201 plateau width under text crit: k values ->',[k for k in range(2,13) if sum(1 for c in cols if max([cnt(v,64,'text') for v in refs.get(c,())],default=-1)>=k)==1201])
# which COLs drop exactly at k=8 (1206->1201) and are they a coherent class family?
b={c:max([cnt(v,64,'text') for v in refs.get(c,())],default=-1) for c in cols}
d7=[c for c in cols if b[c]==7]
print('COLs whose best vtable has exactly 7 .text slots (%d):'%len(d7))
for c in d7[:12]: print('   0x%08x %s'%(c,tds.get(rd(c+12),'?')))
print('max-slot histogram:',dict(sorted(collections.Counter(b.values()).items())))

print('\n=== structural predicates: does any yield 1201? ===')
low={min(v) for v in collections.defaultdict(list).values()} if False else None
byclass=collections.defaultdict(list)
for c in kept: byclass[rd(c+12)].append(c)
preds={}
preds['kept 1214']=len(kept)
preds['has >=1 vtable backref']=sum(1 for c in kept if refs.get(c))
preds['has >=1 backref & pCD!=0']=sum(1 for c in kept if refs.get(c) and rd(c+16))
preds['pCD in .rdata']=sum(1 for c in kept if rd(c+16) and inse(rd(c+16),RDATA))
preds['pCD in .data']=sum(1 for c in kept if rd(c+16) and inse(rd(c+16),DATA))
preds['mdisp==0']=sum(1 for c in kept if rd(c+4)==0)
preds['mdisp<=0x1000']=sum(1 for c in kept if rd(c+4)<=0x1000)
preds['minVA per class']=len({min(v) for v in byclass.values()})
preds['maxVA per class']=len({max(v) for v in byclass.values()})
preds['AV-side classes']=len({rd(c+12) for c in kept if not tds.get(rd(c+12),'?').startswith('.?AU')})
preds['name has $']=sum(1 for c in kept if '$' in tds.get(rd(c+12),'?'))
preds['name no $']=sum(1 for c in kept if '$' not in tds.get(rd(c+12),'?'))
preds['backref==1']=sum(1 for c in kept if len(refs.get(c,()))==1)
preds['backref>=2']=sum(1 for c in kept if len(refs.get(c,()))>=2)
for name,n in preds.items():
    flag='  <<< 1201' if n==1201 else ''
    print('  %-34s %5d%s'%(name,n,flag))
print('\n2-predicate AND combinations hitting 1201:')
ks=list(preds)
hit=[]
for i in range(len(ks)):
    for j in range(i+1,len(ks)):
        pass
print('  (structural single predicates: none equal 1201 ->',
      all(n!=1201 for n in preds.values()),')')
