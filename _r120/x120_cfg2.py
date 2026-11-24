# Reverse-CFG enclosure: which function starts can reach each site without crossing another start.
import struct, json, re, array as _ar
P='/home/t628/projects/ra2-campaign-forge/ra2bench/gamemd.exe'
OUT='/home/t628/projects/ra2-campaign-forge/_r120/'
d=open(P,'rb').read()
e=struct.unpack_from('<I',d,0x3c)[0]
nsec=struct.unpack_from('<H',d,e+6)[0]; optsz=struct.unpack_from('<H',d,e+20)[0]
IB=struct.unpack_from('<I',d,e+24+28)[0]
sec=e+24+optsz; SEC={}
for i in range(nsec):
    nm=d[sec+40*i:sec+40*i+8].rstrip(b'\0').decode('latin1')
    vs,va,rs,ra=struct.unpack_from('<IIII',d,sec+40*i+8); SEC[nm]=dict(va=va,vs=vs,raw=ra,rawsz=rs)
tv=SEC['.text']; text=d[tv['raw']:tv['raw']+tv['vs']]; base=IB+tv['va']; tend=base+len(text)
def ld(n,t):
    a=_ar.array(t); a.frombytes(open(OUT+n+'.bin','rb').read()); return a
rdA=ld('rd2_addr','I'); rdZ=ld('rd2_size','B'); rdK=ld('rd2_kind','B')
rdT=ld('rd2_tgt','I'); rdF=ld('rd2_flow','B')
starts=ld('a2_starts','I'); kinds=ld('a2_kinds','B'); sizes=ld('a2_sizes','B')
pushes=ld('a2_pushes','I'); pushv=ld('a2_pushv','I')
calls=ld('a2_calls','I'); callk=ld('a2_callk','B'); callt=ld('a2_callt','I')
pushset={a:v for a,v in zip(pushes,pushv)}; ns=len(starts)
startset=set(int(x) for x in starts)
B1=set(int(a) for a in starts if (int(a)-base)>0 and text[int(a)-base-1]==0xCC)
B2=set(int(starts[i]) for i in range(1,ns) if kinds[i-1] in (1,2))
B3=set(int(callt[i]) for i in range(len(calls)) if callk[i]==3 and base<=int(callt[i])<tend and int(callt[i]) in startset)
RDB=set(int(t) for t,k in zip(rdT,rdK) if k==3 and base<=int(t)<tend and int(t) in startset)
ALL=set(B1)|set(B2)|set(B3)|set(RDB)
NODE={}
for a,z,k,t,f in zip(rdA,rdZ,rdK,rdT,rdF): NODE[int(a)]=(int(z),int(k),int(t),int(f))
# reverse adjacency built lazily per query: compute predecessor candidates arithmetically
import bisect
rda=[int(x) for x in rdA]
def preds(a):
    out=[]
    # fallthrough / adjacent only possible from within max insn length 15 bytes back
    for k in range(1,16):
        p=a-k
        if p in NODE:
            z,kk,t,f=NODE[p]
            if f==1 and p+z==a: out.append(p)
            if kk in (2,6) and t==a: out.append(p)
        if p in NODE and NODE[p][1]==3 and NODE[p][2]==a: out.append(p)
    return out
def enclosure(site):
    seen={site}; work=[site]; startsfound=set()
    while work:
        a=work.pop()
        for p in preds(a):
            if p in seen: continue
            if p in ALL:
                startsfound.add(p)
                # do not expand across a function boundary
                continue
            seen.add(p); work.append(p)
    return startsfound
def guid_ok(b,drop_d2=False,d4=0x46000000,d3low=0x00C0):
    d1,d2,d3,d4_=struct.unpack('<4I',b)
    if d4_!=d4: return False
    if not drop_d2 and d2!=0: return False
    if d3low is not None and (d3&0xFFFF)!=d3low: return False
    return True
def scan(drop_d2=False,d4=0x46000000,d3low=0x00C0,sections=('.rdata','.data')):
    hits={}
    for nm in sections:
        s=SEC[nm]; blob=d[s['raw']:s['raw']+min(s['vs'],s['rawsz'])]
        for off in range(0,len(blob)-16,4):
            if guid_ok(blob[off:off+16],drop_d2,d4,d3low): hits[IB+s['va']+off]=nm
    return hits
iid=scan(); iidset=set(iid)
T1=0x7f7c80
raw1=[base+m.start() for m in re.finditer(re.escape(b'\x68'+T1.to_bytes(4,'little')),text)]
sites1=[a for a in raw1 if a in pushset and pushset[a]==T1]
rows=[]
for a in sites1:
    enc=enclosure(a)
    rows.append(dict(site=hex(a),enclosing_starts=[hex(x) for x in sorted(enc)],
                     n=len(enc)))
import collections
print('sites',len(sites1),'enclosure cardinality histogram',collections.Counter(r['n'] for r in rows))
for r in rows[:12]: print(' ',r['site'],r['enclosing_starts'])
json.dump(dict(sites=rows,hist=dict(collections.Counter(r['n'] for r in rows))),
          open(OUT+'x120exec_enclosure.json','w'),indent=1)
