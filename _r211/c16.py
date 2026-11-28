# -*- coding: utf-8 -*-
"""R211 c16（定稿）：律 W 用 COL 独立源重算 + 判别力反控。
律 W：V(c) == { r.mdisp : r ∈ BCA(c), r.mdisp != 0, pTD(r) ∈ INTERFACE ∪ TD_OWN }
      INTERFACE = 名字以 .?AU 开头 ; TD_OWN = 954 个 own COL 的 pTD 集合
反控（正向判据必须打不过的对照）：
  C1 每类取「全体 954 类 BCA 记录 mdisp 并集」⇒ 应几乎全失配
  C2 只取 nc==0 的记录
  C3 只取 pdisp!=-1 的记录（虚基）
  C4 「pTD ∈ TD_OWN」单独 ⇒ 91 失配
  C5 「.?AU」单独 ⇒ 159 失配
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
        COL[base+4*i]=dict(addr=base+4*i,sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}; pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
TDOWN=set(v['pTD'] for v in own.values())
# 独立源视图集合（COL 记录 mdisp）
V={a:set(COL[c]['mdisp'] for c in G[a])-{0} for a in CHD}
NM={a:own[a]['name'] for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
def test(f,label):
    bad=[a for a in CHD if set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and f(r))!=V[a]]
    ck(label,len(bad)==0,'失配 %d / 954'%len(bad))
    for a in bad[:5]: print('     %-34s V=%s S=%s'%(NM[a],sorted(V[a]),
        sorted(set(r['mdisp'] for r in ALLR[a] if r['mdisp']!=0 and f(r)))))
    return len(bad)
print('=== 律 W 定稿（COL 独立源）===')
test(lambda r: tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN,'W  .?AU ∨ pTD∈TD_OWN')
test(lambda r: not tdn(r['pTD']).startswith('.?AV') or r['pTD'] in TDOWN,'W2 ¬.?AV ∨ pTD∈TD_OWN（等价式）')
print('\n=== 反控 ===')
test(lambda r: True,'C0 无过滤（全非零 mdisp）')
test(lambda r: r['nc']==0,'C2 nc==0')
test(lambda r: r['pdisp']!=-1,'C3 pdisp!=-1（虚基）')
test(lambda r: r['pTD'] in TDOWN,'C4 pTD∈TD_OWN 单独')
test(lambda r: tdn(r['pTD']).startswith('.?AU'),'C5 .?AU 单独')
# C1 全集并集
uni=set(r['mdisp'] for a in CHD for r in ALLR[a] if r['mdisp']!=0)
hit=sum(1 for a in CHD if V[a]==uni)
ck('C1 全部记录并集套所有类', hit==0, '成立 %d / 954'%hit)
# 8 类证据汇总
EIGHT=[0x802a18,0x7fb4b0,0x7ffea0,0x800098,0x804ce0,0x8093f8,0x80c1d0,0x80d298]
print('\n=== 8 个 {4} 独立附加项类：V 侧 4 与 B 侧 4 双侧对应 ===')
for a in EIGHT:
    b4=[r for r in ALLR[a] if r['mdisp']==4]
    print('  %-34s 4∈V=%-5s B 侧 mdisp=4 记录 %d 条（%s）'%(NM[a],4 in V[a],len(b4),
        ', '.join(tdn(r['pTD']) for r in b4)))
ck('F1 8 类 4∈V 且 B 侧有 mdisp=4 记录', all(4 in V[a] and any(r['mdisp']==4 for r in ALLR[a]) for a in EIGHT), True)
# 全 954 类：4∈V 的类数
n4v=sum(1 for a in CHD if 4 in V[a]); n4b=sum(1 for a in CHD if any(r['mdisp']==4 for r in ALLR[a]))
ck('F2 4∈V 类数 == 4∈B 类数', n4v==n4b, '%d vs %d'%(n4v,n4b))
json.dump({'law_w':'V(c)=={mdisp | r in BCA(c), mdisp!=0, pTD in INTERFACE∪TD_OWN}',
  'classes':len(CHD),'n4v':n4v,'n4b':n4b,
  'eight':{hex(a):{'name':NM[a],'V':sorted(V[a]),'rec4':[tdn(r['pTD']) for r in ALLR[a] if r['mdisp']==4]} for a in EIGHT},
  'interfaces':sorted(set(tdn(r['pTD']) for a in CHD for r in ALLR[a] if tdn(r['pTD']).startswith('.?AU'))),
  'excluded':sorted(set(tdn(r['pTD']) for a in CHD for r in ALLR[a] if r['mdisp']!=0 and not(tdn(r['pTD']).startswith('.?AU') or r['pTD'] in TDOWN)))},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c16.json','w'),indent=1,ensure_ascii=False)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
