# -*- coding: utf-8 -*-
"""R211 c6：15 个律 W 失配的成因。
假设 H1：Type-1（10 类，B 多出 mdisp）的多出项是「虚基」记录（pdisp != -1 或 nc != -1 等）。
假设 H2：Type-2（5 类，ATL CComObject/EventSink，V 空但 B={4}）根本没有第二 vftable。
一次输出：15 类逐记录六字段全表；按全部 954 类统计「pdisp 取值分布」「nc 取值分布」，
以及律 W'（只取满足某条件的记录）是否 954/954 成立。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a].keys())-{0} for a in VS}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(a=b,pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
# 全量记录统计
allr=[]
for a in CHD:
    for b in BCA[a]:
        r=rec(b); r['chd']=a; allr.append(r)
print('BCA 记录总数 = %d'%len(allr))
print('pdisp 取值分布: %s'%collections.Counter(r['pdisp'] for r in allr).most_common(6))
print('nc    取值分布: %s'%collections.Counter(r['nc'] for r in allr).most_common(6))
print('vdisp 取值分布: %s'%collections.Counter(r['vdisp'] for r in allr).most_common(6))
print('mdisp==0 记录数=%d ; mdisp!=0 记录数=%d'%(sum(1 for r in allr if r['mdisp']==0),sum(1 for r in allr if r['mdisp']!=0)))
MIS=['0x7fb4b0','0x7fba50','0x7fc350','0x800600','0x800938','0x8033a8','0x80c048','0x80c3d0','0x80cc58','0x80cde8','0x80e680','0x80e740','0x80e780','0x80e7c0','0x80e998']
print('\n=== 15 个失配类的 BCA 记录全表 ===')
for h in MIS:
    a=int(h,16)
    print('\n%s  %s   n=%d  V=%s'%(h,NM.get(VS[a][0],'?') if a in VS else own[a]['name'],NB[a],sorted(V.get(a,set()))))
    for b in BCA[a]:
        r=rec(b)
        print('   BCD=%#010x pTD=%#010x nc=%d mdisp=%d pdisp=%d vdisp=%d attr=%#x'%(r['a'],r['pTD'],r['nc'],r['mdisp'],r['pdisp'],r['vdisp'],r['attr']))
# H1 检验：只看 nc == -1 && pdisp == -1 && vdisp>=0 的记录？
def testset(f,name):
    bad=[]
    for a in sorted(V):
        s=set(r['mdisp'] for r in (rec(b) for b in BCA[a]) if r['mdisp']!=0 and f(r))
        if s!=V[a]: bad.append((NM.get(VS[a][0],'?'),hex(a),sorted(V[a]),sorted(s)))
    print('%-58s 失配 %d 类'%(name,len(bad)))
    for x in bad[:6]: print('     %-30s %s V=%s S=%s'%x)
    return bad
print()
testset(lambda r:True,'W  : 全部非零 mdisp')
testset(lambda r:r['nc']==-1,'W1 : nc == -1')
testset(lambda r:r['pdisp']==-1 or r['pdisp']==0,'W2 : pdisp ∈ {-1,0}')
testset(lambda r:r['vdisp']>=0,'W3 : vdisp >= 0')
testset(lambda r:r['nc']==-1 and r['pdisp']==-1,'W4 : nc==-1 ∧ pdisp==-1')
