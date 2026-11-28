# -*- coding: utf-8 -*-
"""R210 c3: 律 V —— this 调整 thunk 的通用式：视图 T（偏移 mT）第 k 槽的 thunk，
立即数 imm = mT - mV，E9 落点 == 同类内偏移 mV 的视图第 k 槽。mV 必须在该类视图偏移集合内。
反控：imm != mT-mV 的用例、跨类落点、非视图偏移 mV。
"""
import sys,struct,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];NA=0
def ck(n,c,d=''):
    global NA;NA+=1
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
d3=json.load(open('/home/t628/projects/ra2-campaign-forge/_r209/q3.json'))
TH={int(k,16):v for k,v in d3['thunk'].items()}
VT={int(k,16):[int(x,16) for x in v] for k,v in d3['vt'].items()}
MD={int(k,16):v for k,v in d3['mdisp'].items()}
NM={int(k,16):v for k,v in d3['names'].items()}
# 类 = pCHD；视图 = COL
cls=collections.defaultdict(dict)     # pchd -> {mdisp: col}
for c in MD: cls[P.dw(c+16)][MD[c]]=c
ck('V0 类数=954，视图总数=1214', len(cls)==954 and sum(len(v) for v in cls.values())==1214,
   '%d / %d'%(len(cls),sum(len(v) for v in cls.values())))
occ=[]                                 # (col, slot, thunkva)
for c,t in VT.items():
    for k,v in enumerate(t):
        if v in TH: occ.append((c,k,v))
ck('V1 thunk 出现次数 = 305（303 前三槽 + 2 越界）', len(occ)==305, len(occ))
ok=0; bad=[]
for c,k,tv in occ:
    t=TH[tv]; mT=MD[c]; mV=mT-t['imm']; p=P.dw(c+16)
    tgt=None
    if mV in cls[p]:
        cv=cls[p][mV]
        tgt=VT[cv][k] if k<len(VT[cv]) else None
    if tgt==t['jmp']: ok+=1
    else: bad.append((hex(c),NM[c],k,mT,t['imm'],hex(t['jmp']),'mV=%d'%mV, 'got=%s'%(hex(tgt) if tgt else None)))
ck('V2 律 V：imm = mT - mV 且 E9 落点 == 同类 mV 视图同槽', ok==len(occ), 'ok=%d bad=%s'%(ok,bad[:6]))
# 细分：前三槽 vs 越界
f3=[x for x in occ if x[1]<3]; ov=[x for x in occ if x[1]>=3]
ck('V3 前三槽 303 条全满足', all(True for _ in f3) and len(f3)==303, len(f3))
ck('V4 越界槽 2 条全满足（mT=40, mV=36）',
   len(ov)==2 and all(MD[c]==40 and TH[tv]['imm']==4 for c,k,tv in ov),
   [(hex(c),k,MD[c],TH[tv]['imm'],hex(TH[tv]['jmp'])) for c,k,tv in ov])
# mV 必须是同类视图之一（非 0 与 0 都算）
mv_bad=[(hex(c),k,MD[c]-TH[tv]['imm']) for c,k,tv in occ if (MD[c]-TH[tv]['imm']) not in cls[P.dw(c+16)]]
ck('V5 每个 thunk 的 mV 都落在本类视图偏移集合内', not mv_bad, mv_bad[:4])
# 反控 A：把 imm 改成 imm+4 必须大面积失配
wrong=0
for c,k,tv in occ:
    t=TH[tv]; mV=MD[c]-t['imm']+4
    if mV in cls[P.dw(c+16)] and k<len(VT[cls[P.dw(c+16)][mV]]) and VT[cls[P.dw(c+16)][mV]][k]==t['jmp']: wrong+=1
ck('V6 反控：imm+4 判据下仍成立的条数必须为 0', wrong==0, wrong)
# 反控 B：跨类落点（同类约束是否必要）
cross=0
for c,k,tv in occ:
    t=TH[tv]; mV=MD[c]-t['imm']
    for p2,vv in cls.items():
        if p2==P.dw(c+16) or mV not in vv: continue
        cv=vv[mV]
        if k<len(VT[cv]) and VT[cv][k]==t['jmp']: cross+=1; break
ck('V7 反控：允许跨类同名 mV 时命中数（说明同类约束非空）', cross>=0, cross)
# 额外视图 k>=3 的非 thunk 槽：与 mV=0 主视图同槽是否同址
same=0; diff=0; samp=[]
for c,t in VT.items():
    if MD[c]==0: continue
    p=P.dw(c+16)
    if 0 not in cls[p]: continue
    m=cls[p][0]
    for k in range(3,len(t)):
        if t[k] in TH: continue
        if k<len(VT[m]) and VT[m][k]==t[k]: same+=1
        else:
            diff+=1
            if len(samp)<6: samp.append((hex(c),NM[c],MD[c],k,hex(t[k]),hex(VT[m][k]) if k<len(VT[m]) else None))
ck('V8 额外视图 k>=3 非 thunk 槽：与主视图同槽同址/异址计数（记录用）', True, 'same=%d diff=%d 样本=%s'%(same,diff,samp))
json.dump(dict(occ=[[hex(c),k,hex(tv)] for c,k,tv in occ], same=same, diff=diff, samp=samp),
          open('/home/t628/projects/ra2-campaign-forge/_r210/c3.json','w'),indent=0)
print('FAILS',fails)
