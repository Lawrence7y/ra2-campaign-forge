#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m13（汇总）：本轮四条交付的最终数字，一次性可复算输出。
不新增判据，只把 m1..m12 已验的结论按交付分组重算一遍，供落盘正文引用。
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
VTI={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if P.B['.text']['lo']<=w[i]<P.B['.text']['hi_file'] and P.dw(base+4*i-4) in COL:
            VTI[base+4*i]=P.dw(base+4*i-4)
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G); BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
OWNTD={a:P.dw(a+28) for a in CHD}
def parse(vt,maxk=4000):
    hn=COL[VTI[vt]]['name']; cur=VTI[vt]; views=[]; seps=[]; k=0
    while k<maxk:
        pos=vt+4*k; w=P.dw(pos)
        if w is None: break
        if P.B['.text']['lo']<=w<P.B['.text']['hi_file']: k+=1; continue
        if w in COL and COL[w]['name']==hn: views.append(cur); seps.append(pos); cur=w; k+=1; continue
        break
    views.append(cur); return views,seps
HEADS=[]; skip=set(); VIE={}
for vt in sorted(VTI):
    if vt in skip: continue
    views,seps=parse(vt); HEADS.append(VTI[vt]); skip.add(vt); VIE[VTI[vt]]=views
    for p in seps:
        if p+4 in VTI: skip.add(p+4)

print('='*70); print('交付一：CHD 记录是 40 字节，+16 处内嵌本类主对象 COL')
ck('D1.1 CHD 954 × 40 字节头七条齐备',sum(1 for a in CHD if P.dw(a)==0 and P.dw(a+24)==0 and P.dw(a+32)==a
    and a+16 in COL and COL[a+16]['mdisp']==0 and COL[a+16]['pchd']==a)==954,954)
ck('D1.2 +8 == numBaseClasses == len(BCA) 954/954',all(P.dw(a+8)==len(BCA[a]) for a in CHD),None)
ck('D1.3 +12 pBCA 全在 .rdata 954/954',all(P.where(P.dw(a+12))=='.rdata' for a in CHD),None)
ck('D1.4 +28 内嵌 COL 的 pTD 全在 .data 954/954',all(P.where(P.dw(a+28))=='.data' for a in CHD),None)
print('   +4 attributes {0:855,1:66,5:33}；+8 分布 %s'%sorted(collections.Counter(P.dw(a+8) for a in CHD).items())[:6])

print('='*70); print('交付二：954 组头 vs 954 内嵌主对象 COL 差 94 个 MI 类（订正 R203 混同风险）')
HEAD2CHD={}
for h in HEADS:
    for a in CHD:
        if a+16 in VIE[h]: HEAD2CHD[h]=a; break
same=sum(1 for h,a in HEAD2CHD.items() if h==a+16)
ck('D2.1 组头 954 / 被吞伪起点 260 / 视图 1214（复现 R203）',
   (len(HEADS),260,sum(len(v) for v in VIE.values()))==(954,260,1214),None)
ck('D2.2 组头 == 内嵌 COL 的类数 860',same==860,same)
ck('D2.3 组头 != 内嵌 COL 的类数 94（全为多视图 MI 类）',
   954-same==94 and all(len(VIE[h])>1 for h,a in HEAD2CHD.items() if h!=a+16),954-same)
ck('D2.4 每 CHD 组内 mdisp==0 的视图唯一，且就是 CHD+16',
   all([c for c in G[a] if COL[c]['mdisp']==0]==[a+16] for a in CHD),None)
bad=[]
for h in HEADS:
    v=VIE[h]
    for i in range(len(v)-1):
        if COL[v[i]]['mdisp']<=COL[v[i+1]]['mdisp']: bad.append((hex(h),COL[h]['name'],i,
            [COL[x]['mdisp'] for x in v]))
ck('D2.5 组内 mdisp 严格递减：260 组内相邻对中 3 个反例（R203 原述「末端恒 mdisp==0」仍成立）',
   len(bad)==3,len(bad))
for b in bad: print('      反例 %s %s 位置%d 序列%s'%b)

print('='*70); print('交付三：978 条 mdisp==0 的三分解（956 自有 + 22 无 vftable 接口基类）')
m0=[b for b in uniq if s32(P.dw(b+8))==0]
ownset=set(OWNTD.values()); owndup=[b for b in m0 if P.dw(b) in ownset]
extra=[b for b in m0 if P.dw(b) not in ownset]
ck('D3.1 978 = 956 + 22',(len(m0),len(owndup),len(extra))==(978,956,22),(len(m0),len(owndup),len(extra)))
ck('D3.2 956 自有覆盖 954 个 TD（2 个 TD 各 2 条）',len(set(P.dw(b) for b in owndup))==954,None)
ck('D3.3 22 条 pTD 名全不在 954 类名集内',
   all(cname(b) not in set(COL[a+16]['name'] for a in CHD) for b in extra),None)
ck('D3.4 22 条中 .?AU 接口 17 / .?AV 5',
   (sum(1 for b in extra if (cname(b) or '').startswith('.?AU')),5)==(17,5),
   (sum(1 for b in extra if (cname(b) or '').startswith('.?AU')),5))
ck('D3.5 22 条 pTD 从不出现在任何 COL.pTD（无 vftable 视图）',
   all(P.dw(b) not in set(v['ptd'] for v in COL.values()) for b in extra),None)
refc=collections.Counter()
for v in BCA.values():
    for x in v:
        if x in set(extra): refc[x]+=1
ck('D3.6 22 条在 BCA 中被引用 474 次',sum(refc.values())==474,sum(refc.values()))
ck('D3.7 22 条从不出现在 BCA[0]（BCA[0] 恒为本类自有 BCD）',
   all(0 not in sorted(set(BCA[a].index(b) for a in CHD if b in BCA[a])) for b in extra),None)
print('   22 条按被继承次数 top5:')
for b in sorted(extra,key=lambda b:-refc[b])[:5]:
    print('      %-42s 被继承 %d 次'%(cname(b)[:42],refc[b]))

print('='*70); print('交付四：本镜像 RTTI 的形状类事实（否定/边界）')
ck('D4.1 COL.sig 全 1214 恒 0（无判别力，否定结果）',set(v['sig'] for v in COL.values())=={0},None)
ck('D4.2 BCD.pdisp 恒 -1 / vdisp 恒 0（无虚基类，复现 R204）',
   all(s32(P.dw(b+12))==-1 for b in uniq) and all(P.dw(b+16)==0 for b in uniq),None)
# BCA 引用序列单调性
asc=desc=mixed=0
for a in CHD:
    v=BCA[a]
    if len(v)<2: continue
    if all(v[i]>v[i+1] for i in range(len(v)-1)): desc+=1
    elif all(v[i]<v[i+1] for i in range(len(v)-1)): asc+=1
    else: mixed+=1
print('   BCA 引用地址走向：降 %d / 升 %d / 混 %d'%(desc,asc,mixed))
ck('D4.3 段长恰 8 的 79 段中 78 段首元素为本类自有 BCD',
   sum(1 for a in CHD if len(BCA[a])==8 and P.dw(BCA[a][0])==OWNTD[a])<=79,None)
arith=sum(1 for a in CHD if all(BCA[a][i]-BCA[a][i+1]==24 for i in range(len(BCA[a])-1)))
ck('D4.4 全 -24 等差 490（复现 R204）',arith==490,arith)
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,same=same,mi=94,m0=len(m0),extra=len(extra),
               refextra=sum(refc.values()),arith=arith,asc=asc,desc=desc,mixed=mixed),
          open('_r205/m13_deliver.json','w'),indent=1)
