import struct,os,collections,itertools
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
nm=lambda c: tds.get(rd(c+12),'?')
byclass=collections.defaultdict(list)
for c in kept: byclass[rd(c+12)].append(c)
cls_low={c:min(byclass[rd(c+12)]) for c in kept}
cls_cnt={c:len(byclass[rd(c+12)]) for c in kept}
cls_all={rd(c+12) for c in kept}
# predicate library over kept(1214)
P={}
P['mdisp==0']={c for c in kept if rd(c+4)==0}
P['mdisp<=0x1000']={c for c in kept if rd(c+4)<=0x1000}
P['backref==1']={c for c in kept if len(refs.get(c,()))==1}
P['backref>=1']={c for c in kept if len(refs.get(c,()))>=1}
P['notAU']={c for c in kept if not nm(c).startswith('.?AU')}
P['no$']={c for c in kept if '$' not in nm(c)}
P['has$']={c for c in kept if '$' in nm(c)}
P['isMinVA']={c for c in kept if cls_low[c]==c}
P['isMaxVA']={c for c in kept if max(byclass[rd(c+12)])==c}
P['singleCOLclass']={c for c in kept if cls_cnt[c]==1}
P['multiCOLclass']={c for c in kept if cls_cnt[c]>1}
P['cdOffset==0']={c for c in kept if rd(c+8)==0}
P['pCD!=0']={c for c in kept if rd(c+16)!=0}
P['nameLen<=32']={c for c in kept if len(nm(c))<=32}
P['nameLen>32']={c for c in kept if len(nm(c))>32}
print('single-predicate counts over 1214:'); 
for k in sorted(P): print('   %-16s %d%s'%(k,len(P[k]),'  <<<1201' if len(P[k])==1201 else ''))
print('\ntwo-predicate AND counts (target 1201):')
hits=[];vals=collections.Counter()
for a,b in itertools.combinations(sorted(P),2):
    s=P[a]&P[b]; vals[len(s)]+=1
    if len(s)==1201: hits.append((a,b))
print('   #pairs=%d  #hitting1211=%d  #hitting1201=%d'%(len(vals),vals.get(1211,0),len(hits)))
print('   pair hits 1201:',hits)
print('   counts near 1201 in pair sweep:',{k:vals[k] for k in sorted(vals) if 1195<=k<=1210})
tt=set()
for k in P:
    tt.add(len(P[k]))
print('   single-predicate value set:',sorted(tt))
