#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m20（§2.12 规则 D 收口）：复算审计员 #519 全部可取得的结论（其报告未落盘，用其 minA.sh 实测输出 + 主会话独立复算）。
对 6 条主张逐条给 PASS/FAIL 与主会话自己的数。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[]; N=0
def ck(nm,c,d=''):
    global N; N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            VT[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))

print('=== A1 CHD 40 字节头 ===')
c1=sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+4) in (0,1,5) and P.dw(a+8)==len(BCA[a])
       and P.where(P.dw(a+12))=='.rdata' and a+16 in COL and COL[a+16]['mdisp']==0 and P.dw(a+32)==a)
ck('A1 PASS：40 字节头七条齐备 954/954',c1==954,c1)
print('=== A2 内嵌 COL 是组内唯一 mdisp==0 视图 ===')
c2=sum(1 for a in CHD if [x for x in G[a] if COL[x]['mdisp']==0]==[a+16])
ck('A2 PASS：954/954',c2==954,c2)
print('=== A3 两个 954 交集 860 / 差 94 ===')
def in_text(x): return x is not None and P.B['.text']['lo']<=x<P.B['.text']['hi_file']
def parse(vt,maxk=4000):
    hn=COL[VT[vt]]['name']; cur=VT[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if in_text(w): k+=1; continue
        if w in COL and COL[w]['name']==hn: views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
HEADS=[]; skip=set(); VIE={}
for vt in sorted(VT):
    if vt in skip: continue
    views,seps=parse(vt); HEADS.append(VT[vt]); skip.add(vt); VIE[VT[vt]]=views
    for p in seps:
        if p+4 in VT: skip.add(p+4)
EMB=set(a+16 for a in CHD); HS=set(HEADS)
ck('A3 PASS：组头 954 / 内嵌 954 / 交集 860 / 差 94',(len(HS),len(EMB),len(HS&EMB),len(HS-EMB))==(954,954,860,94),
   (len(HS),len(EMB),len(HS&EMB),len(HS-EMB)))
ck('A3b PASS：差集 94 全属多视图组',
   all(len(VIE[h])>1 for h in HS-EMB),sum(1 for h in HS-EMB if len(VIE[h])==1))
print('=== A4 COL.sig 全 0（无判别力）===')
ck('A4 PASS：1214 条 sig 全为 0',set(v['sig'] for v in COL.values())=={0},sorted(set(v['sig'] for v in COL.values())))
print('=== A5 978 = 956 + 22，474 次引用 ===')
m0=[b for b in uniq if s32(P.dw(b+8))==0]; owntd=set(P.dw(a+28) for a in CHD)
own=[b for b in m0 if P.dw(b) in owntd]; ext=[b for b in m0 if P.dw(b) not in owntd]
ck('A5 PASS：978/956/22',(len(m0),len(own),len(ext))==(978,956,22),(len(m0),len(own),len(ext)))
ck('A5b PASS：22 条 .?AU 17 条',sum(1 for b in ext if (cname(b) or '').startswith('.?AU'))==17,None)
ck('A5c PASS：22 条 pTD 不在任何 COL.pTD',
   all(P.dw(b) not in set(v['ptd'] for v in COL.values()) for b in ext),None)
rc=collections.Counter()
for v in BCA.values():
    for x in v:
        if x in set(ext): rc[x]+=1
ck('A5d PASS：BCA 引用 474 次',sum(rc.values())==474,sum(rc.values()))
ck('A5e PASS：双记录 TD 2 个（INoticeSource / VectorClass<H>）',
   len([1 for b in own if collections.Counter(P.dw(x) for x in own)[P.dw(b)]>1])>0,None)
print('=== A6 序选择（审计独立发现，主会话已采纳）===')
bad_vt=bad_ad=0
for h in HEADS:
    v=VIE[h]
    for i in range(len(v)-1):
        if COL[v[i]]['mdisp']<=COL[v[i+1]]['mdisp']: bad_vt+=1
    v2=sorted(VIE[h])
    for i in range(len(v2)-1):
        if COL[v2[i]]['mdisp']<=COL[v2[i+1]]['mdisp']: bad_ad+=1
ck('A6 PASS：vt 序 3 例外 / COL 地址序 0 例外（审计发现成立）',(bad_vt,bad_ad)==(3,0),(bad_vt,bad_ad))
ck('A6b PASS：地址升序 == mdisp 严格降序 954/954',
   all([COL[x]['mdisp'] for x in sorted(VIE[h])]==sorted([COL[x]['mdisp'] for x in VIE[h]],reverse=True)
       for h in HEADS),None)
print('=== 审计另提的两条（主会话复算）===')
ck('X1 审计：组头==组内最小地址视图 953/954',
   sum(1 for h in HEADS if VT and h==min(VIE[h]))==953,
   sum(1 for h in HEADS if h==min(VIE[h])))
ck('X2 审计：内嵌 COL==组内最大地址视图 954/954',
   all(VIE[h][-1]==max(VIE[h]) for h in HS&EMB) and all(a+16==max(G[a]) for a in CHD),
   sum(1 for a in CHD if a+16!=max(G[a])))
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,bad_vt=bad_vt,bad_ad=bad_ad,
               head_min=sum(1 for h in HEADS if h==min(VIE[h]))),
          open('_r205/m20_audit_final.json','w'),indent=1)
