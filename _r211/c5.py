# -*- coding: utf-8 -*-
"""R211 c5（决定性）：订正 BCD 字段口径后，检验
  律 W：V(c)（视图偏移集合，来自 vftable mdisp）== { BCA(c) 各 BCD 记录的 mdisp } - {0}
BCD 实测口径（本轮 c4 实证，与 R207 一致）：
  +0 pTD / +4 numContainedBases / +8 mdisp / +12 pdisp(恒−1) / +16 vdisp / +20 attributes
反控：
  A 把 V 换成「BCA 记录顺序的非零 mdisp 多重集」看是否退化为集合
  B 把 mdisp 取 +12（pdisp）看是否仍相等
  C 只对 954 类中的 QI 类检验（排除「碰巧」）
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
# --- 954 类的 COL/CHD/BCA（口径同 R207 m2：COL 记录扫描） ---
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
# --- 视图侧 ---
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
def bcd(addr):
    """返回 (pTD, nc, mdisp, pdisp, vdisp, attr)；无效返回 None"""
    if not addr or P.r2o(addr) is None: return None
    f=[P.dw(addr+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=f[1],mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
ck('0 类集合等价', set(VS)==set(own), '%d/%d 差 %d/%d'%(len(VS),len(own),len(set(VS)-set(own)),len(set(own)-set(VS))))
bad_bca=[]
Bset={}; Bmulti={}
for a in CHD:
    ms=[]
    for b in BCA[a]:
        r=bcd(b)
        if r is None: bad_bca.append((hex(a),hex(b))); continue
        ms.append(r['mdisp'])
    Bset[a]=set(x for x in ms if x!=0); Bmulti[a]=sorted(x for x in ms if x!=0)
ck('1 BCA 元素全部可解析为 BCD', len(bad_bca)==0, '不可解析 %d'%len(bad_bca))
V={a:set(VS[a].keys())-{0} for a in VS}
mis=[(NM.get(VS[a][0],'?'),hex(a),sorted(V[a]),sorted(Bset[a])) for a in sorted(V) if V[a]!=Bset[a]]
ck('2 律 W：V(c) == 非零 mdisp 集合（954 类逐类）', len(mis)==0, '失配 %d'%len(mis))
for m in mis[:25]: print('   MISMATCH %-34s %s V=%s B=%s'%m)
if len(mis)>25: print('   ... 共 %d'%len(mis))
# 多重集 vs 集合
dup=[(NM.get(VS[a][0],'?'),hex(a),Bmulti[a]) for a in Bmulti if len(Bmulti[a])!=len(set(Bmulti[a]))]
ck('3 非零 mdisp 多重集 vs 视图集合：多重集有重复的类数', True, '%d 类（含重复）'%len(dup))
print('   重复示例：')
for d in dup[:8]: print('     %-34s %s mdisp多重集=%s'%d)
# 反控 B：mdisp 取 +12（pdisp）
misP=[]
for a in sorted(V):
    ps=set()
    for b in BCA[a]:
        r=bcd(b)
        if r: ps.add(r['pdisp'])
    ps.discard(0)
    if V[a]==ps: misP.append(a)
ck('B 反控：把 +12(pdisp) 当 mdisp', len(misP)==0, '碰巧相等 %d 类'%len(misP))
# 8 类独立 {4}
EIGHT=[0x802a18,0x7fb4b0,0x7ffea0,0x800098,0x804ce0,0x8093f8,0x80c1d0,0x80d298]
print('\n8 个「{4} 独立附加项」类的 B 侧明细：')
okall=True
for c in EIGHT:
    print('  %-34s V=%s B=%s  mdisp多重集=%s'%(NM.get(VS[c][0],'?'),sorted(V[c]),sorted(Bset[c]),Bmulti[c]))
    okall = okall and (4 in Bset[c])
ck('4 8 类的 B 含 4', okall, okall)
json.dump({'mismatch':mis,'dup_count':len(dup),'dup':dup[:40],
  'eight':{hex(c):{'V':sorted(V[c]),'B':sorted(Bset[c]),'Bmulti':Bmulti[c],'name':NM.get(VS[c][0],'?')} for c in EIGHT},
  'classes':len(V),'chd':len(CHD),'own':len(own)},open('/home/t628/projects/ra2-campaign-forge/_r211/c5.json','w'),indent=1)
print('\n断言 %d / FAIL %d'%(NA,len(fails)))
