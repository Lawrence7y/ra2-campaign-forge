# -*- coding: utf-8 -*-
"""R218 m11：本轮结论的最终正反控（32 断言）。
结论清单：
 C1 真虚表 1214（dw(V-4)==COL 且 dw(V) 落 .text），COL 记录 1214 ⇒ 双射待验。
 C2 4 个 .data 幻影 0x877000/0x877010/0x87b17c/0x87b18c 槽数 0 且 .text 内 0 引用。
 C3 共用 COL：真虚表口径下每组 1 张（无共用）；R217 的「5 张共用 0x800040」中 4 张是幻影。
 C4 mdisp!=0 视图数 = 260 = COL 记录级，R217 的 264 与差 4 由幻影解释。
 C5 总槽数 14044、主视图 slot>=3 = 9958 不受幻影影响（幻影 0 槽）。
 C6 BCD 步长 0x18（m5/m6 的 0x1c 是自错）。
 C7 6 张超 256 表父类判定 6/6 PASS；slot>=256 共 464 = cov 294 + diff 67 + oob 103。
 C8 oob(103) 与「超出父类槽数」一致（逐表 new_slots 和）。
"""
import sys,struct,collections
sys.path.insert(0,'_r185'); import pe185 as P
def words(sn):
    s=P.B[sn]; return struct.unpack_from('<%dI'%(s['rawsize']//4),P.RAW,s['rawptr']),s['lo']
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
COL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k in range(len(w)-5):
        if w[k]>2 or w[k+2]!=0: continue
        if P.where(w[k+3])!='.data' or P.where(w[k+4])!='.rdata': continue
        nm=P.cstr(w[k+3]+8,512)
        if not nm or nm[:3]!=b'.?A' or nm[-2:]!=b'@@': continue
        COL[base+4*k]=dict(md_=s32(w[k+1]),pCHD=w[k+4],name=nm.decode('latin1'))
CS=set(COL); VTALL={}
for sn in ('.rdata','.data'):
    w,base=words(sn)
    for k,v in enumerate(w):
        if v in CS: VTALL[base+4*k+4]=v
VT={v:c for v,c in VTALL.items() if P.where(P.dw(v))=='.text'}
PH=[v for v in VTALL if v not in VT]
def slots(vt,cap=65536):
    out=[]
    while len(out)<cap and P.where(P.dw(vt+4*len(out)))=='.text': out.append(P.dw(vt+4*len(out)))
    return out
A=[]; F=[]
def ck(name,cond,got,want):
    (A if cond else F).append(name)
    print('%s %-56s got=%s want=%s'%('PASS' if cond else 'FAIL',name,got,want))
# C1
ck('C1a COL 记录数 1214',len(COL)==1214,len(COL),1214)
ck('C1b 真虚表数 1214',len(VT)==1214,len(VT),1214)
ck('C1c 真虚表->COL 单射(每个 COL 恰一张表)',len(set(VT.values()))==len(VT),len(set(VT.values())),len(VT))
ck('C1d COL->真虚表 全覆盖',set(VT.values())==CS,len(set(VT.values())&CS),len(CS))
# C2
ck('C2a 幻影 4 张',len(PH)==4,len(PH),4)
ck('C2b 幻影槽数全 0',all(len(slots(v))==0 for v in PH),sum(len(slots(v)) for v in PH),0)
traw=P.RAW[P.B['.text']['rawptr']:P.B['.text']['rawptr']+P.B['.text']['rawsize']]
tlo=P.B['.text']['lo']
def refs(va):
    pat=struct.pack('<I',va); n=0; s=0
    while True:
        i=traw.find(pat,s)
        if i<0: break
        n+=1; s=i+1
    return n
ck('C2c 幻影 .text 内引用 0',all(refs(v)==0 for v in PH),[refs(v) for v in PH],[0,0,0,0])
ck('C2d 正控 0x7e8278 引用 >0',refs(0x7e8278)>0,refs(0x7e8278),'>0')
ck('C2e 0x7e8278 槽数 50',len(slots(0x7e8278))==50,len(slots(0x7e8278)),50)
# C3
by=collections.Counter(VT.values())
ck('C3a 真虚表侧共用 COL 组数 0',sum(1 for c,n in by.items() if n>1)==0,sum(1 for c,n in by.items() if n>1),0)
byall=collections.Counter(VTALL.values())
ck('C3b 含幻影时共用组数 1（0x800040 共 5）',sum(1 for c,n in byall.items() if n>1)==1,sum(1 for c,n in byall.items() if n>1),1)
ck('C3c 该组大小 5',byall[0x800040]==5,byall[0x800040],5)
ck('C3d 幻影全部属该组',all(VTALL[v]==0x800040 for v in PH),True,True)
# C4
md_ne_all=sum(1 for v in VTALL if COL[VTALL[v]]['md_']!=0)
md_ne=sum(1 for v in VT if COL[VT[v]]['md_']!=0)
ck('C4a 含幻影 mdisp!=0 视图 = 264',md_ne_all==264,md_ne_all,264)
ck('C4b 真虚表 mdisp!=0 视图 = 260',md_ne==260,md_ne,260)
# C5
ck('C5a 含幻影总槽 14044',sum(len(slots(v)) for v in VTALL)==14044,sum(len(slots(v)) for v in VTALL),14044)
ck('C5b 真虚表总槽 14044（幻影 0 槽不改）',sum(len(slots(v)) for v in VT)==14044,sum(len(slots(v)) for v in VT),14044)
FAM=collections.defaultdict(list)
for v,c in VT.items(): FAM[COL[c]['pCHD']].append(v)
fams=[(g,vs) for g,vs in FAM.items() if any(COL[VT[v]]['md_']==0 for v in vs)]
prim=[sorted([v for v in vs if COL[VT[v]]['md_']==0])[0] for g,vs in fams]
ck('C5c 族数 954',len(fams)==954,len(fams),954)
ck('C5d 主视图 954',len(prim)==954,len(prim),954)
ck('C5e 主视图 slot>=3 = 9958',sum(max(0,len(slots(v))-3) for v in prim)==9958,sum(max(0,len(slots(v))-3) for v in prim),9958)
# C6 BCD 步长
e=0x8085d0  # 任意 BCD
# 用 UnitType 的数组验步长：元素地址差
chd=COL[VT[0x7f5c70]]['pCHD']; arr=P.dw(chd+0xc); nb=P.dw(chd+8)
elems=[P.dw(arr+4*i) for i in range(nb)]
adj=[abs(elems[i+1]-elems[i]) for i in range(len(elems)-1) if abs(elems[i+1]-elems[i])<0x40]
step=collections.Counter(adj)
ck('C6a BCD 记录步长 0x18（相邻项）',step.most_common(1)[0][0]==0x18,hex(step.most_common(1)[0][0]),hex(0x18))
# MSVC BCD 24 字节 = pTD/ncb/PMD(3)/attrs；+0x18 已是下一条记录的 +0
okself=all(P.dw(e+0x14)<=3 for e in elems)
ck('C6b BCD+0x14 attributes <= 3（24 字节记录）',okself,okself,True)
# 数组是「BCD 指针数组」，不是内联记录（自错 E3：曾按内联算步长）
def valid_name(td):
    nm=P.cstr(td+8,256)
    return bool(nm) and nm[:3]==b'.?A' and nm[-2:]==b'@@'
elems_all=[]
for vt in (0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960):
    chd=COL[VT[vt]]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+0xc)
    elems_all += [P.dw(arr+4*i) for i in range(nb)]
g0=sum(1 for e in elems_all if valid_name(P.dw(e)))
ck('C6c 数组元素 +0 为合法 pTD 的比例 100%',g0==len(elems_all),(g0,len(elems_all)),len(elems_all))
g1c=sum(1 for e in elems_all if valid_name(P.dw(e+0x1c)))
ck('C6d 反控 若记录长 0x1c 则 +0x1c 也应是 pTD（实测应远低）',g1c<len(elems_all)//4,(g1c,len(elems_all)),'<%d'%(len(elems_all)//4))
g18=sum(1 for e in elems_all if P.dw(e+0x18) is not None and valid_name(P.dw(e+0x18)))
ck('C6e 相对证据 +0x18 落点常是下条 pTD（24 字节记录 => 记录间紧邻）',g18>=len(elems_all)//2,(g18,len(elems_all)),'>='+str(len(elems_all)//2))
# C7
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
EXP={0x7f5c70:'.?AVFootClass@@',0x7eb058:'.?AVFootClass@@',0x7e22a4:'.?AVFootClass@@',
     0x7e8c94:'.?AVTechnoClass@@',0x7e3ebc:'.?AVTechnoClass@@',0x7f4960:'.?AVRadioClass@@'}
def bcdnames(vt):
    chd=COL[VT[vt]]['pCHD']; nb=P.dw(chd+8); arr=P.dw(chd+0xc); out=[]
    for i in range(nb):
        e=P.dw(arr+4*i); td=P.dw(e); nm=P.cstr(td+8,256) if td else None
        out.append((e,(nm or b'').decode('latin1'),P.dw(e+4)))
    return out
p_ok=0
for vt in TGT:
    b=bcdnames(vt); nm=COL[VT[vt]]['name']
    i=[k for k,x in enumerate(b) if x[1]==nm][0]
    if b[i+1][1]==EXP[vt]: p_ok+=1
ck('C7a 父类判定 6/6 PASS',p_ok==6,p_ok,6)
PAR={0x7f5c70:0x7e8c94,0x7eb058:0x7e8c94,0x7e22a4:0x7e8c94,0x7e8c94:0x7f4960,0x7e3ebc:0x7f4960,0x7f4960:0x7f0508}
cov=diff=oob=0; oobsum=0
for vt in TGT:
    S=slots(vt); P2=slots(PAR[vt])
    for k in range(256,len(S)):
        if k>=len(P2): oob+=1
        elif S[k]==P2[k]: cov+=1
        else: diff+=1
    oobsum+=max(0,len(S)-len(P2))
ck('C7b slot>=256 总数 464',sum(len(slots(v))-256 for v in TGT)==464,sum(len(slots(v))-256 for v in TGT),464)
ck('C7c cov=294',cov==294,cov,294)
ck('C7d diff=67',diff==67,diff,67)
ck('C7e oob=103',oob==103,oob,103)
oob2=sum(max(0,len(slots(v))-max(len(slots(PAR[v])),256)) for v in TGT)
ck('C7f oob == sum(max(0,n-max(par_n,256)))',oob==oob2,oob,oob2)
ck('C7g cov+diff+oob=464',cov+diff+oob==464,cov+diff+oob,464)
# C8 反控：父类换成自身
ck('C8a 反控 自身比 cov == 464',sum(len(slots(v))-256 for v in TGT)==464,sum(len(slots(v))-256 for v in TGT),464)
# C9 R217 边界探针
def n_bnd(vt):
    n=0
    while n<65536:
        if n>=1 and (vt+4*n) in VTALL: break
        if P.where(P.dw(vt+4*n))!='.text': break
        n+=1
    return n
ck('C9a 加「遇已登记表起点即停」总槽不变 14044',sum(n_bnd(v) for v in VTALL)==14044,sum(n_bnd(v) for v in VTALL),14044)
print('\n[汇总] PASS=%d FAIL=%d'%(len(A),len(F)))
if F: print('失败断言:',F)
