# -*- coding: utf-8 -*-
"""R211 c8（律 W' 定稿）：extras 全指向少数 pTD ⇒ 猜想：extras 的记录 pTD「没有自己的类/主视图」，
MSVC 仍为它写 BCD，但编译器不为它生成额外 vftable。
律 W'：V(c) == { r.mdisp : r ∈ BCA(c), r.mdisp != 0, r.pTD ∈ TD_OWN }   （TD_OWN = 存在 own COL 的 pTD 集合）
一次输出：
  L1 V ⊆ 全部 nonzero mdisp（上轮）
  L2 W' 失配清单
  L3 5 个 extras pTD 的定性：是否有 own COL / pTD 名 / 是否 onlysec
  L4 反控：把过滤条件换成「pTD ∈ .data 命名 TD」是否仍成立
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
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
V={a:set(VS[a].keys())-{0} for a in VS}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(a=b,pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdname(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else '?'
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
print('TD_OWN 大小 = %d （own COL 数 %d）'%(len(TDOWN),len(own)))
allr=[(a,rec(b)) for a in CHD for b in BCA[a]]
print('BCA 记录 %d ; 其中 pTD ∈ TD_OWN 的 %d ; 不在的 %d'%(len(allr),
      sum(1 for a,r in allr if r['pTD'] in TDOWN), sum(1 for a,r in allr if r['pTD'] not in TDOWN)))
def nmof(a): return NM.get(VS[a][0],'?') if a in VS and 0 in VS[a] else own[a]['name']
def sel(f):
    bad=[]
    for a in sorted(V):
        s=set(r['mdisp'] for _,r in allr if False)  # placeholder
    return bad
def test(f,label):
    bad=[]
    for a in sorted(V):
        s=set()
        for b in BCA[a]:
            r=rec(b)
            if r['mdisp']!=0 and f(r): s.add(r['mdisp'])
        if s!=V[a]: bad.append((nmof(a),hex(a),sorted(V[a]),sorted(s)))
    ck(label,len(bad)==0,'失配 %d'%len(bad))
    for x in bad[:10]: print('     %-32s %s V=%s S=%s'%x)
    return bad
test(lambda r: r['pTD'] in TDOWN, "L2 律 W'：pTD ∈ TD_OWN 时 V 逐类相等")
test(lambda r: P.where(r['pTD'])=='.data', 'L4 反控：pTD ∈ .data')
test(lambda r: r['pTD'] in TDOWN and r['pdisp']==-1, "L2b 律 W''：pTD∈TD_OWN ∧ pdisp==-1")
# L3 extras pTD 定性
EX=set()
for a in V:
    for b in BCA[a]:
        r=rec(b)
        if r['mdisp']!=0 and r['mdisp'] not in V[a]: EX.add(r['pTD'])
print('\n=== extras 涉及的 pTD 定性 ===')
for td in sorted(EX):
    inown = td in TDOWN
    hascol = td in set(v['pTD'] for v in COL.values())
    print('  pTD=%#010x  %-32s sec=%s  ∈TD_OWN=%s  被COL引用=%s  nc/name=%s'%(
        td,tdname(td),P.where(td),inown,hascol,''))
# 这些 pTD 在多少条 BCD 里出现
cnt=collections.Counter(r['pTD'] for _,r in allr)
print('\n  这些 pTD 的 BCD 记录数：%s'%[(hex(t),cnt[t]) for t in sorted(EX)])
# 反查：这些 pTD 对应的类名是否出现在 954 类名里
names954=set(NM.values())
for td in sorted(EX):
    n=tdname(td)
    print('  %#010x %-32s ∈954类名=%s'%(td,n,n in names954))
json.dump({'td_own':len(TDOWN),'extras_ptd':[hex(t) for t in sorted(EX)],
           'extras_ptd_names':{hex(t):tdname(t) for t in sorted(EX)},
           'records':len(allr)},open('/home/t628/projects/ra2-campaign-forge/_r211/c8.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
