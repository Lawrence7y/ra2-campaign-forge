# -*- coding: utf-8 -*-
"""R211 c19：91 个 mdisp=4 类的第二记录身份分解 + 律 U/律 W 接合。
输出：91 类按「mdisp=4 的第二条记录 pTD」分组；每组数量；组内 V 分布；
      以及 HouseClass QI 返回集合 vs V 的差集（订正 R210「唯一反例」措辞）。
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
V={a:set(COL[c]['mdisp'] for c in G[a])-{0} for a in CHD}
NM={a:own[a]['name'] for a in CHD}
def rec(b):
    f=[P.dw(b+4*z) for z in range(6)]
    return dict(pTD=f[0],nc=s32(f[1]),mdisp=s32(f[2]),pdisp=s32(f[3]),vdisp=s32(f[4]),attr=f[5])
def tdn(td):
    nm=P.cstr(td+8,300); return nm.decode('latin1') if nm else ''
ALLR={a:[rec(b) for b in BCA[a]] for a in CHD}
grp=collections.Counter(); ex=collections.defaultdict(list)
for a in CHD:
    r4=[r for r in ALLR[a] if r['mdisp']==4]
    if not r4: continue
    key=tuple(sorted(tdn(r['pTD']) for r in r4))
    grp[key]+=1; ex[key].append((NM[a],sorted(V[a])))
print('=== mdisp=4 记录的 pTD 组合 → 类数 ===')
for k,v in grp.most_common():
    print('  n=%-3d %s'%(v,' + '.join(k)))
    for e in ex[k][:3]: print('        %-40s V=%s'%e)
print('\n=== 各组 V 分布 ===')
for k,v in grp.most_common():
    vd=collections.Counter(str(e[1]) for e in ex[k])
    print('  %-60s %s'%(' + '.join(k),dict(vd)))
# HouseClass QI 返回 vs V
print('\n=== HouseClass: QI 0x4f6830 返回偏移 vs V ===')
print('  V = %s'%sorted(V[0x802a18]))
print('  QI 返回（c2/c13 实证）= {0(IUnknown,IPersist,IPersistStream), 36(0x24), 40(0x28), 44(0x2c)}')
print('  V - QI = %s'%sorted(V[0x802a18]-{0,36,40,44}))
print('  QI - V = %s'%sorted({0,36,40,44}-V[0x802a18]))
json.dump({'groups':{' + '.join(k):{'n':v,'classes':ex[k]} for k,v in grp.items()},
  'house_V':sorted(V[0x802a18]),'house_qi':[0,36,40,44]},
  open('/home/t628/projects/ra2-campaign-forge/_r211/c19.json','w'),indent=1,ensure_ascii=False)
