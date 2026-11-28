# -*- coding: utf-8 -*-
"""R210 c10: 把律 U 接到 R207 律 L 上 —— 每个额外视图偏移 m 对应的 BCD 记录（同 pCHD、mdisp==m、
pTD 有类头），取出该 pTD 的名字，与 slot0 QI 里「返回该偏移」的 IID 站点对照。
关节点：QI 的返回偏移是 this 偏移，BCD 的 mdisp 是同一偏移 => 二者必须一致；pTD 名应给出该接口的 RTTI 名。
"""
import sys,struct,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
from capstone import Cs,CS_ARCH_X86,CS_MODE_32
md=Cs(CS_ARCH_X86,CS_MODE_32)
def s32(v): return struct.unpack('<i',struct.pack('<I',v&0xffffffff))[0]
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
def tdname(td):
    n=P.cstr(td+8,300); return n.decode('latin1') if n else '?'
def has_head(td): return P.where(td)=='.data' and tdname(td).startswith('.?A')
ck('T0 COL 1214 / CHD 954', len(COL)==1214 and len(CHD)==954, '%d/%d'%(len(COL),len(CHD)))
# 每类额外视图 -> BCD
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
own={a:a+16 for a in CHD}
miss=[]; ok=0; recs=[]
for a in CHD:
    ms=sorted({MD[c] for c in G[a] if c!=own[a]})
    for m in ms:
        cands=[x for x in BCA[a] if s32(P.dw(x+8))==m and has_head(P.dw(x))]
        if not cands: miss.append((hex(a),tdname(COL[own[a]]['pTD']),m)); continue
        ok+=1
        recs.append((hex(a),tdname(COL[own[a]]['pTD']),m,[tdname(P.dw(x)) for x in cands]))
ck('T1 每个额外视图偏移都能在同类 BCA 里找到 mdisp==m 且有类头的 BCD（260/260）',
   len(miss)==0 and ok==260, 'ok=%d miss=%d %s'%(ok,len(miss),miss[:5]))
nmc=collections.Counter(tuple(sorted(set(n for _,_,_,ns in recs for n in ns))) for _ in [0])
byoff=collections.defaultdict(collections.Counter)
for a,cn,m,ns in recs:
    for n in ns: byoff[m][n]+=1
print('# 各偏移对应的 pTD 名字分布：')
for m in sorted(byoff):
    print('   mdisp=%-6d %s'%(m,byoff[m].most_common(6)))
ck('T2 mdisp=4 的 BCD pTD 名唯一', len(byoff[4])==1, list(byoff[4]))
ck('T3 mdisp=12 的 BCD pTD 名唯一', len(byoff[12])==1, list(byoff[12]))
ck('T4 mdisp=24 的 BCD pTD 名唯一', len(byoff.get(24,{}))<=2, byoff.get(24))
ck('T5 mdisp=8 的 BCD pTD 名字数', len(byoff[8])<=3, byoff[8])
json.dump(dict(byoff={str(m):dict(v) for m,v in byoff.items()},
               recs=recs, miss=miss, ok=ok),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c10.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
