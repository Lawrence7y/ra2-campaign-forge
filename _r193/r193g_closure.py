#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R193 第五刀（本轮核心交付）：四个高频实现落在**同一个 78 类血统集合**上。

r193g 第一版 17 条断言里 5 条 FAIL，**全部是「用表地址集合比类集合」这一类判据缺陷**：
  0x410580 / 0x410590 / 0x410220 只出现在**接口子表**上（mdisp 8/12/4），而血统集合 L 是
  主表（mdisp 0）的表地址集合 —— 两个集合按地址必然不相交（名字相同但表不同）。
本版统一改成**按 COL 修饰名比宿主集合**，并对每条实现声明它的「表来源」（主表 / 哪一层子表）。

主张：
  C1 |L| = 78（链里含 .?AVAbstractClass@@ 的主表，按类名去重）。
  C2 L 上主表槽 4 == 0x410450 的 77 张；唯一覆写者 .?AVHouseTypeClass@@（0x512280）。
  C3 0x410220 的宿主**类名集合** == L 的类名集合（78 vs 78，集合相等），
     只出现在 IRTTITypeInfo 层 mdisp==4 子表槽 4，体 = mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4
     ⇒ 相对接口子对象 +0xC、折算完整对象 +0x10。
  C4 0x410590 的宿主类名集合 == L，只在 INoticeSource 层 mdisp==12 子表槽 0。
  C5 0x410580 的宿主类名集合 ⊂ L，且缺的 3 张逐个列出并判定「缺层」还是「覆写」。
  C6 直接引用面：四个地址里 0x410220 有 14 处直接 call rel32（**不是**只经虚表调用），
     其余三个为 0。R192 那句「四地址被直接引用均为 0」对 0x410220 是错的，本脚本就地订正。
反控：
  N1 L 按地址比（第一版做法）⇒ 集合必然不相交，说明口径必须按名。
  N2 ObjectClass 血统 21 张 ≠ 78。
  N3 0x410220 在主表槽 4 上出现 0 次。
"""
import sys, struct, collections, json, capstone
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text']; LO=T['lo']; HI=T['hi_file']
def in_text(x): return x is not None and LO<=x<HI
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'], struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']), n
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=w[i+1],ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
def nslot(vt):
    k=0
    while in_text(P.dw(vt+4*k)): k+=1
    return k
NS={vt:nslot(vt) for vt in VT}
ck('C0 基线：COL 1214 / VT 1214 / 槽 14044', (len(COL),len(VT),sum(NS.values()))==(1214,1214,14044),
   (len(COL),len(VT),sum(NS.values())))
def chain(colva):
    c=COL[colva]; n=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12); out=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        if b is None or P.where(b) in ('None','other'): continue
        ptd=P.dw(b); nm=P.cstr((ptd or 0)+8,160)
        out.append((nm.decode('latin1') if nm else None, P.dw(b+8), P.dw(b+4)))
    return out
CH={vt:chain(VT[vt]) for vt in VT}
AB='.?AVAbstractClass@@'
MAIN=[vt for vt in sorted(VT) if COL[VT[vt]]['mdisp']==0]
Ltabs=[vt for vt in MAIN if any(n==AB for n,_,_ in CH[vt])]
Lnames=set(COL[VT[v]]['name'] for v in Ltabs)
ck('C1 |L| = 78 张主表 / 78 个类名', len(Ltabs)==78 and len(Lnames)==78, (len(Ltabs),len(Lnames)))
print('   L（78）：%s'%', '.join(sorted(n.replace('.?AV','').replace('@@','') for n in Lnames)))
s4={vt:P.dw(vt+16) for vt in Ltabs if NS[vt]>4}
hit=[vt for vt,a in s4.items() if a==0x410450]
ovr=[vt for vt,a in s4.items() if a!=0x410450]
ck('C2 L 上主表槽 4 == 0x410450 的 77 张 + 1 张覆写者 .?AVHouseTypeClass@@',
   len(hit)==77 and len(ovr)==1 and COL[VT[ovr[0]]]['name']=='.?AVHouseTypeClass@@',
   (len(hit),[(hex(v),COL[VT[v]]['name']) for v in ovr]))

def layer(colva):
    c=COL[colva]; n=P.dw(c['pchd']+8); arr=P.dw(c['pchd']+12); m=[]
    for j in range(n):
        b=P.dw(arr+4*j)
        if b is None or P.where(b) in ('None','other'): continue
        if P.dw(b+8)==c['mdisp']: m.append((P.dw(b+4),P.dw(b)))
    if not m: return None
    best=max(m,key=lambda x:x[0])
    if sum(1 for x in m if x[0]==best[0])!=1: return None
    nm=P.cstr(best[1]+8,160)
    return (nm.decode('latin1') if nm else None, c['mdisp'])
def occ(tgt):
    """返回 {表 VA: [槽号...]}"""
    o=collections.defaultdict(list)
    for vt in VT:
        for k in range(NS[vt]):
            if P.dw(vt+4*k)==tgt: o[vt].append(k)
    return o
def hostnames(o):
    return set(COL[VT[vt]]['name'] for vt in o)
def body(va,lim=64):
    r=P.r2o(va); out=[]
    for i in md.disasm(P.RAW[r:r+lim],va):
        out.append('%s %s'%(i.mnemonic,i.op_str))
        if i.mnemonic in ('ret','retn'): break
    return ' ; '.join(out), P.RAW[r:r+16].hex()

o220=occ(0x410220); hn220=hostnames(o220)
lay220=[layer(VT[vt]) for vt in o220]
print('\n   0x410220：表 %d 张 / 宿主类名 %d 个 / 层分布 %s'
      %(len(o220),len(hn220),collections.Counter(lay220).most_common(3)))
ck('C3 0x410220 宿主类名集合 == L 的类名集合（集合相等）', hn220==Lnames,
   (len(hn220),len(Lnames),len(hn220-Lnames),len(Lnames-hn220)))
ck('C3b 0x410220 只出现在 (.?AUIRTTITypeInfo@@, mdisp 4) 子表槽 4',
   set(lay220)=={('.?AUIRTTITypeInfo@@',4)} and all(o220[vt]==[4] for vt in o220),
   collections.Counter(lay220).most_common(2))
b220=body(0x410220); print('   0x410220 体：%s'%b220[0])
ck('C3c 0x410220 = mov eax,[esp+4]; mov eax,[eax+0xC]; ret 4（读接口子对象 +0xC）',
   b220[0]=='mov eax, dword ptr [esp + 4] ; mov eax, dword ptr [eax + 0xc] ; ret 4'
   and b220[1].startswith('8b442404'), (b220[0],b220[1]))
ck('C3d 折算完整对象：接口子对象 mdisp 4 ⇒ 字段落在完整对象 +0x10（0xC+4）', 0xC+4==0x10)
o590=occ(0x410590); hn590=hostnames(o590); lay590=[layer(VT[vt]) for vt in o590]
print('   0x410590：表 %d / 宿主 %d / 层 %s'%(len(o590),len(hn590),collections.Counter(lay590).most_common(2)))
ck('C4 0x410590 宿主类名集合 == L', hn590==Lnames, (len(hn590),len(Lnames)))
ck('C4b 0x410590 只在 (.?AVINoticeSource@@, mdisp 12) 子表槽 0',
   set(lay590)=={('.?AVINoticeSource@@',12)} and all(o590[vt]==[0] for vt in o590),
   collections.Counter(lay590).most_common(2))
o580=occ(0x410580); hn580=hostnames(o580); lay580=[layer(VT[vt]) for vt in o580]
print('   0x410580：表 %d / 宿主 %d / 层 %s'%(len(o580),len(hn580),collections.Counter(lay580).most_common(2)))
miss=sorted(Lnames-hn580)
print('   INoticeSink 层槽 0 缺的 %d 个类：%s'%(len(miss),miss))
ck('C5 0x410580 宿主类名集合 ⊂ L 且缺 3 个类',
   hn580<Lnames and len(Lnames-hn580)==3 and len(hn580)==75, (len(hn580),len(miss)))
ck('C5b 0x410580 只在 (.?AVINoticeSink@@, mdisp 8) 子表槽 0',
   set(lay580)=={('.?AVINoticeSink@@',8)} and all(o580[vt]==[0] for vt in o580),
   collections.Counter(lay580).most_common(2))
# 缺的 3 个类：找它们的 mdisp==8 子表槽 0
det=[]
for nm in miss:
    tabs=[vt for vt in VT if COL[VT[vt]]['name']==nm and COL[VT[vt]]['mdisp']==8 and NS[vt]>0]
    for t in tabs:
        v=P.dw(t)
        det.append(dict(cls=nm,sub='%08X'%t,val='%08X'%v,body=body(v)[0][:90],
                        in_chain=any(n=='.?AVINoticeSink@@' and md_==8 for n,md_,_ in CH[t])))
for d in det: print('     %s 子表 %s 槽0=%s : %s'%(d['cls'],d['sub'],d['val'],d['body']))
ck('C5c 缺的 3 个类都有 mdisp==8 子表（是覆写，不是缺表），且槽 0 值不是 0x410580',
   len(det)==3 and all(d['val']!='00410580' for d in det) and all(d['in_chain'] for d in det),
   [(d['cls'],d['val']) for d in det])
ck('C5d 3 个覆写实现互不相同（不是同一个默认空实现）', len({d['val'] for d in det})==3,
   [d['val'] for d in det])

def scan_refs(tgt):
    res=[]; s=P.B['.text']; o0=s['rawptr']; n=s['rawsize']; buf=P.RAW
    i=o0
    while True:
        j=buf.find(b'\xe8',i,o0+n)
        if j<0: break
        if j+5<=o0+n:
            va=s['lo']+(j-o0)
            if (va+5+struct.unpack_from('<i',buf,j+1)[0])==tgt: res.append(('call',va))
        i=j+1
    k=o0
    while True:
        j=buf.find(b'\xff\x25',k,o0+n)
        if j<0: break
        if j+6<=o0+n and struct.unpack_from('<I',buf,j+2)[0]==tgt: res.append(('callabs',s['lo']+(j-o0)))
        k=j+1
    return res
refs={}
for tgt in (0x410450,0x410220,0x410580,0x410590):
    r=scan_refs(tgt); refs['%08X'%tgt]=len(r)
    print('   %08X 直接引用 %d 处 %s'%(tgt,len(r),[('%s'%k,'%08X'%v) for k,v in r[:4]]))
ck('C6 0x410450 / 0x410580 / 0x410590 直接引用 0 处，而 0x410220 有 %d 处'
   %refs['00410220'],
   refs['00410450']==0 and refs['00410580']==0 and refs['00410590']==0 and refs['00410220']>0, refs)
ck('C6b 订正 R192「四地址直接引用均为 0」：对 0x410220 不成立', refs['00410220']==14, refs['00410220'])
ck('N1 反控：按表地址比较时 L 与 0x410220 的表集合互不相交（说明必须按类名比）',
   set(Ltabs)&set(o220)==set())
LOb=set(COL[VT[v]]['name'] for v in MAIN if any(n=='.?AVObjectClass@@' for n,_,_ in CH[v]))
ck('N2 反控：ObjectClass 血统类名 %d 个 != 78'%len(LOb), len(LOb)==21 and LOb!=Lnames, len(LOb))
ck('N3 反控：0x410220 在 954 主表槽 4 上出现 0 次',
   sum(1 for vt in MAIN if NS[vt]>4 and P.dw(vt+16)==0x410220)==0)
json.dump(dict(L=len(Ltabs),Lnames=sorted(Lnames),hit410=len(hit),
   ovr=[('%08X'%v,COL[VT[v]]['name']) for v in ovr],
   o220=len(o220),hn220=len(hn220),o590=len(o590),o580=len(o580),
   miss=miss,miss_detail=det,refs=refs,
   b220=b220,b580=body(0x410580),b590=body(0x410590),b450=body(0x410450),
   lay220=collections.Counter(lay220).most_common(3),
   lay580=collections.Counter(lay580).most_common(2),
   lay590=collections.Counter(lay590).most_common(2),fails=fails),
   open('_r193/r193g.json','w'),ensure_ascii=False,indent=1)
print('\n断言 %d 条，FAIL %d 条 %s'%(N,len(fails),fails))
sys.exit(1 if fails else 0)
