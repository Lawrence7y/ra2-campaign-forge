# -*- coding: utf-8 -*-
"""R210 c11: mdisp=4 视图的 BCD 双记录分解 —— 每类的 +4 是否恒有 .?AUIUnknown@@ 记录，
以及第二个记录（真接口）是否恰在「slot0 QI 返回 +4 偏移」的 4 个 QI 目标类里出现。
"""
import sys,struct,json,collections,re
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
def tdn(td):
    n=P.cstr(td+8,300); return n.decode('latin1') if n else '?'
def has_head(td): return P.where(td)=='.data' and tdn(td).startswith('.?A')
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
own={a:a+16 for a in CHD}
rows=[]
for a in CHD:
    ms=sorted({MD[c] for c in G[a] if c!=own[a]})
    if 4 not in ms: continue
    cands=[x for x in BCA[a] if s32(P.dw(x+8))==4 and has_head(P.dw(x))]
    names=sorted({tdn(P.dw(x)) for x in cands})
    rows.append((a,tdn(COL[own[a]]['pTD']),names))
ck('V0 有 mdisp=4 视图的类 = 91', len(rows)==91, len(rows))
iu=sum(1 for _,_,ns in rows if '.?AUIUnknown@@' in ns)
ck('V1 其中含 .?AUIUnknown@@ 记录的 = 91', iu==91, iu)
two=sum(1 for _,_,ns in rows if len(ns)==2)
ck('V2 恰两条 BCD 记录（IUnknown + 真接口）的类数 = 91', two==91, two)
real=collections.Counter(n for _,_,ns in rows for n in ns if n!='.?AUIUnknown@@')
print('# mdisp=4 的「真接口」名分布：',real.most_common())
ck('V3 真接口名合计 = 91', sum(real.values())==91, sum(real.values()))
groups=collections.defaultdict(list)
for a,cn,ns in rows:
    r=[n for n in ns if n!='.?AUIUnknown@@']
    groups[r[0] if r else None].append(cn)
for k,v in groups.items(): print('   %-34s n=%-3d 样例=%s'%(k,len(v),v[:4]))
json.dump(dict(rows=[[hex(a),cn,ns] for a,cn,ns in rows],
               real=dict(real), groups={str(k):len(v) for k,v in groups.items()}),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c11.json','w'),indent=0,ensure_ascii=False)
print('FAILS',fails)
