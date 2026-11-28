# -*- coding: utf-8 -*-
"""R211 c3：决定性检验 —— 律 U 是不是 BCA/BCD 表的推论？
对 954 个类：视图偏移集合 V(c)（来自 vftable mdisp）vs BCA 里本类视图记录的非零 mdisp 集合 B(c)。
一次输出：
  (1) 全量对照：V=={0}∪B 的类数 / 失配清单（全列）
  (2) {4} 存在性：4 ∈ B(c) 的类数；4 ∈ V(c) 的类数；{4} 独立附加项的 8 类在 B 侧的 mdisp 集合
  (3) 反控 A：把 B 换成「全部 BCD 记录的 mdisp」不限本 CHD；
  (4) 反控 B：把 V 换成「BCD 记录在 BCA 中的出现顺序」看是否仍相等
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
NB={a:P.dw(a+8) for a in CHD}
pBCA={a:P.dw(a+12) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own={}
for a in CHD:
    for c in G[a]:
        if c==a+16: own[a]=COL[c]
# 视图侧：mdisp 集合（排除 0）
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
VS=collections.defaultdict(dict)
for v in MD: VS[P.dw(v+16)][MD[v]]=v
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
# 每类的 B 集合：BCA 指向的 BCD 记录的 mdisp（排除本类主记录 mdisp=0 的自身？先全部取）
B={}; Braw={}
for a in CHD:
    ms=[]
    for b in BCA[a]:
        r=COL.get(b)
        if r is None: continue
        ms.append(r['mdisp'])
    Braw[a]=ms
    B[a]=set(x for x in ms if x!=0)
V={a:set(VS[a].keys())-{0} for a in VS}
print('类数：视图侧 %d / CHD 侧 %d ；CHD 有 own 记录 %d'%(len(VS),len(CHD),len(own)))
ck('0 类集合等价（视图侧 vs CHD own）', set(VS)==set(own), '%d vs %d 差集 %d/%d'%(len(VS),len(own),len(set(VS)-set(own)),len(set(own)-set(VS))))
def nm(a):
    return NM.get(VS[a][0],'?') if a in VS and 0 in VS[a] else (own[a]['name'] if a in own else '?')
mis=[]
for a in sorted(V):
    if V[a]!=B[a]: mis.append((nm(a),hex(a),sorted(V[a]),sorted(B[a]),sorted(Braw[a])))
ck('1 律 W：V(c) == B(c)（非零 mdisp 集合）逐类相等', len(mis)==0, '失配 %d 类'%len(mis))
for m in mis[:40]: print('   MISMATCH %-34s %s V=%s B=%s Braw=%s'%m)
if len(mis)>40: print('   ... 共 %d'%len(mis))
# {4} 分析
fourB=[a for a in B if 4 in B[a]]
fourV=[a for a in V if 4 in V[a]]
ck('2 4∈B 的类数 == 4∈V 的类数', len(fourB)==len(fourV), '%d vs %d'%(len(fourB),len(fourV)))
ck('3 两者集合完全相同', set(fourB)==set(fourV), '差 %d/%d'%(len(set(fourB)-set(fourV)),len(set(fourV)-set(fourB))))
EIGHT=[0x802a18,0x7fb4b0,0x7ffea0,0x800098,0x804ce0,0x8093f8,0x80c1d0,0x80d298]
print('\n8 个 {4} 独立附加项类的 B 侧 mdisp 集合（Braw 保留记录顺序）：')
for c in EIGHT:
    print('  %-34s V=%s B=%s Braw=%s'%(nm(c),sorted(V[c]),sorted(B[c]),Braw[c]))
ck('4 8 类的 B 含 4', all(4 in B[c] for c in EIGHT), [4 in B[c] for c in EIGHT])
# 反控 A：全部 BCD 记录 mdisp 并集
allB=set(x for a in B for x in B[a])
ck('A 反控：全量 mdisp 并集套所有类' , all(V[a]==allB for a in V), '成立 %d / %d'%(sum(1 for a in V if V[a]==allB),len(V)))
json.dump({'mismatch':[[m[0],m[1],m[2],m[3],m[4]] for m in mis],
           'fourB':len(fourB),'fourV':len(fourV),
           'eight':{hex(c):{'V':sorted(V[c]),'B':sorted(B[c]),'Braw':Braw[c],'name':nm(c)} for c in EIGHT},
           'classes':len(V),'chd':len(CHD),'own':len(own)},
          open('/home/t628/projects/ra2-campaign-forge/_r211/c3.json','w'),indent=1)
print('\nWROTE c3.json  断言 %d 条 / FAIL %d'%(NA,len(fails)))
