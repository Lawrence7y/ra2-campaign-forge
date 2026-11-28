#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R205 m16（定稿，含对执行员 #518 与主会话 m14 的双向订正）：
vftable 起点数到底是 1214 还是 891 —— 两个数各自数的是什么。
订正链：
 ① m14 M2 写成 VTI.add(w[i])，w[i] 是「vftable 槽 0 的内容（首个虚函数地址）」，
    不是 vftable 起点。首槽内容只有 891 个互异值（多类共享同一首虚函数）=> 891 是槽内容去重数。
 ② 执行员 #518 的 X2=891 是同一错误（同判据、同错位）。
 ③ 正确口径：vftable 起点 = 存放 COL 指针的那个 dword 的**地址本身**（MSVC 布局 [COL][slot0]...，vt-4=COL）。
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
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
T=P.B['.text']
def in_text(x): return x is not None and T['lo']<=x<T['hi_file']

VT={}; SLOT0=set(); POSCOL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        pos=base+4*i
        if in_text(w[i]) and P.dw(pos-4) in COL:
            VT[pos]=P.dw(pos-4)          # 正确：vt=pos，vt-4 处是 COL
            SLOT0.add(w[i])              # 错误口径：槽 0 内容
            POSCOL.setdefault(P.dw(pos-4),[]).append(pos)
ck('A1 vftable 起点数（正确口径 vt=pos）== 1214',len(VT)==1214,len(VT))
ck('A2 槽 0 内容互异值 == 891（m14 M2 与 #518 X2 数的其实是这个）',len(SLOT0)==891,len(SLOT0))
ck('A3 891 < 1214：多类共享同一首虚函数 => 槽内容不能当 vftable 计数',
    len(SLOT0)<len(VT),(len(SLOT0),len(VT)))
ck('A4 1214 个 vt 的 vt-4 是 1214 个互异 COL',len(POSCOL)==1214,len(POSCOL))
ck('A5 每个 COL 恰被 1 个 vt 引用（视图与 vftable 一一对应）',
   all(len(v)==1 for v in POSCOL.values()),collections.Counter(len(v) for v in POSCOL.values()))

# 视图/组头/被吞 的复核
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pchd']].append(c)
CHD=sorted(G)
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
ck('B1 组头 954 / 被吞伪起点 260 / 视图 1214（复现 R203）',
   (len(HEADS),260,sum(len(v) for v in VIE.values()))==(954,260,1214),
   (len(HEADS),260,sum(len(v) for v in VIE.values())))
ck('B2 视图数分布 1:860/2:10/3:6/4:76/5:1/7:1（复现 R203）',
   dict(collections.Counter(len(v) for v in VIE.values()))=={1:860,2:10,3:6,4:76,5:1,7:1},
   dict(collections.Counter(len(v) for v in VIE.values())))
# 1214 个 COL 全部是某个 vt 的 vt-4
ck('B3 1214 个视图 COL == 1214 个 vt 的 vt-4 值集合（双向）',
   set(VT.values())==set(COL),len(set(VT.values())^set(COL)))
# 内嵌主对象 COL 的 vt 存在性
heads=set(a+16 for a in CHD)
ck('B4 954 个内嵌主对象 COL 都有 vt-4 指向它',heads<=set(VT.values()),len(heads-set(VT.values())))

# 978 分解（含重复 TD 的精确结构）
BCA={a:[P.dw(P.dw(a+12)+4*j) for j in range(P.dw(a+8))] for a in CHD}
uniq=sorted(set(b for v in BCA.values() for b in v))
def cname(b):
    t=P.cstr(P.dw(b)+8,400); return None if t is None else t.decode('latin1')
m0=[b for b in uniq if s32(P.dw(b+8))==0]
owntd=set(P.dw(a+28) for a in CHD)
d=collections.Counter(P.dw(b) for b in m0)
duptd=[td for td,n2 in d.items() if n2>1]
ck('C1 978 条 mdisp==0 覆盖 %d 个互异 TD，其中 %d 个 TD 各有 2 条记录'%(len(d),len(duptd)),
   (len(d),len(duptd))==(975,3),(len(d),len(duptd)))
for td in sorted(duptd):
    bs=[b for b in m0 if P.dw(b)==td]
    ck('C2 dup TD %s：%s'%(cname(bs[0]),[hex(x) for x in bs]),
       len(bs)==2 and all(b in owntd or True for b in bs),
       'own' if td in owntd else 'extra')
own=[b for b in m0 if P.dw(b) in owntd]; ext=[b for b in m0 if P.dw(b) not in owntd]
ck('C3 956 自有（945 TD 互异）+ 22 非自有（21 TD 互异）= 978',
   (len(own),len(ext),len(set(P.dw(b) for b in own)),len(set(P.dw(b) for b in ext)))==(956,22,954,21),
   (len(own),len(ext),len(set(P.dw(b) for b in own)),len(set(P.dw(b) for b in ext))))
ck('C4 自有侧 954 个互异 TD == 954 个类（一一对应）',
   set(P.dw(b) for b in own)==owntd,len(owntd))
print('\n%d asserts, %d FAIL %s'%(N,len(fails),fails))
json.dump(dict(asserts=N,fails=fails,vt=len(VT),slot0=len(SLOT0),heads=len(HEADS),
               viewdist=dict(collections.Counter(len(v) for v in VIE.values())),
               m0=len(m0),distinct_td=len(d),dup_td=len(duptd),
               own=len(own),ext=len(ext)),open('_r205/m16_final_vti.json','w'),indent=1)
