#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m14（落盘权威）：本轮写入四件套的每个数字都在此复算一次。
X1 697/686/11 三数 + 686 的 mdisp 4:345/8:341；
X2 区间 31,968 / 边界 31,967 / nop 起点 17,726(55.4%)；
X3 CALLAT 目标 6,719：落指令起点 6,692 / 落区间起点 755；区间含 0 目标 25,357(79.3%)；
X4 区间起点匹配序言 411（P1/P3/P4 分布）；(i)或(ii) = 864；
X5 三种网格 697/686 三分类（ret/int3、E1、E3）；
X6 388 个区间含次表 store，100% 也含主表 store；only_sub=0 的真因；
X7 8 条 none 宿主类名（5 条非模板 + 3 条 UNDETERMINED）；
X8 11 条两机制分离（3 覆盖 / 8 不覆盖）；686 后继覆盖 12/686=1.7%；
X9 COL 指针恒 vt-4 1214/1214；COL 地址 916 个取值；
X10 反控。"""
import sys, struct, json, bisect, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn];n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
def in_text(x): return x is not None and LO<=x<HI
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),name=nm.decode('latin1'))
VT={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if in_text(w[i]) and P.dw(base+4*i-4) in COL: VT[base+4*i]=P.dw(base+4*i-4)
MD={vt:COL[VT[vt]]['mdisp'] for vt in VT}
CLS={vt:COL[VT[vt]]['name'] for vt in VT}
def extract():
    rec=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
    while pos<end-4:
        if RAW[pos]==0x66:
            if pos+2<end and RAW[pos+1]==0xC7:
                mo=RAW[pos+2]>>6; pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
            pos+=1; continue
        if RAW[pos]!=0xC7: pos+=1; continue
        modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1; continue
        va=LO+(pos-T['rawptr'])
        if mod==1:
            d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
            rec.append((va,rm,d,im)); pos+=7
        elif mod==2:
            d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
            rec.append((va,rm,d,im)); pos+=10
        else:
            im=struct.unpack_from('<I',RAW,pos+2)[0]; rec.append((va,rm,0,im)); pos+=6
    return rec
allsite=extract()
vts=[r for r in allsite if r[3] in VT]
mainall=[r for r in vts if MD[r[3]]==0]
suball=[r for r in vts if MD[r[3]]!=0]
S697=[r for r in vts if 1<=r[2]<=9]
S686=[r for r in S697 if MD[r[3]]!=0]
S11=[r for r in S697 if MD[r[3]]==0]
# X1
ck('X1a 697/686/11',(len(S697),len(S686),len(S11))==(697,686,11),(len(S697),len(S686),len(S11)))
c4=collections.Counter(MD[r[3]] for r in S686)
ck('X1b 686 的 mdisp 4:345/8:341',c4==collections.Counter({4:345,8:341}),dict(c4))
ck('X1c 686 disp8==mdisp 686/686',all(r[2]==MD[r[3]] for r in S686),sum(1 for r in S686 if r[2]==MD[r[3]]))
ck('X1d 11 条 mdisp 全 0 且 disp∈{4,8}',all(MD[r[3]]==0 for r in S11) and set(r[2] for r in S11)=={4,8},
   dict(collections.Counter(r[2] for r in S11)))
# 指令流
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[];CALLAT=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op))
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t))
        p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]; ASET=set(ADDRS); I2R={a:i for i,a in enumerate(ADDRS)}
SORT=sorted(set(t for _,t in CALLAT)); TGTSET=set(SORT)
REGION=[];st=LO;nb=0
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz; nb+=1
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]; RSET=set(RL)
# X2
ck('X2a 边界 31,967 / 区间 31,968',(nb,len(REGION))==(31967,31968),(nb,len(REGION)))
nopstart=sum(1 for a in RL if a in I2R and INS[I2R[a]][2]=='nop')
ck('X2b 区间起点为 nop 17,726',nopstart==17726,nopstart)
ck('X2c nop 起点比例 55.4%',abs(100.0*nopstart/len(REGION)-55.4)<0.1,'%.2f%%'%(100.0*nopstart/len(REGION)))
# X3
ck('X3a CALLAT 去重目标 6,719',len(SORT)==6719,len(SORT))
ck('X3b 落指令起点 6,692',sum(1 for t in SORT if t in ASET)==6692,sum(1 for t in SORT if t in ASET))
ck('X3c 落区间起点 755',sum(1 for t in SORT if t in RSET)==755,sum(1 for t in SORT if t in RSET))
per=collections.Counter()
for a,b in REGION: per[bisect.bisect_left(SORT,b)-bisect.bisect_left(SORT,a)]+=1
ck('X3d 区间含 0 目标 25,357',per[0]==25357,per[0])
# X4
def pat(a):
    i=I2R.get(a)
    if i is None: return None
    w=INS[i:i+3]
    if len(w)<2: return None
    m=[x[2] for x in w]; o=[x[3].replace(' ','') for x in w]
    if m[0]=='push' and o[0]=='ebp' and m[1]=='mov' and o[1]=='ebp,esp': return 'P1'
    if m[0]=='mov' and o[0]=='edi,edi' and m[1]=='push' and o[1]=='ebp':
        return 'P3' if (len(w)>2 and m[2]=='mov' and o[2]=='ebp,esp') else 'P3b'
    if m[0]=='sub' and o[0].startswith('esp,'): return 'P4'
    return None
PR={a:pat(a) for a in RL}
PR={a:v for a,v in PR.items() if v}
ck('X4a 区间起点匹配序言 411',len(PR)==411,len(PR))
ck('X4b 序言模式 P1 249 / P4 158 / P3 4',dict(collections.Counter(PR.values()))=={'P1':249,'P4':158,'P3':4},
   dict(collections.Counter(PR.values())))
CALLATREG=set(a for a in RL if a in TGTSET)
ck('X4c (i)=755 (ii)=411 (i|ii)=864',len(CALLATREG)==755 and len(CALLATREG|set(PR))==864,
   (len(CALLATREG),len(PR),len(CALLATREG|set(PR))))
# X5
PATS=set(PR); E1=sorted(TGTSET&ASET); E3=sorted(TGTSET&ASET|PATS)
def mk(E):
    def f(va):
        i=bisect.bisect_right(E,va)-1
        return None if i<0 else (E[i],E[i+1] if i+1<len(E) else HI)
    return f
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
def run(segf,stores):
    bm=collections.defaultdict(int); bs=collections.defaultdict(int)
    for r in mainall: bm[segf(r[0])]+=1
    for r in suball:  bs[segf(r[0])]+=1
    c=collections.Counter()
    for r in stores:
        k=segf(r[0])
        if bm[k]>0 and bs[k]>0: c['both']+=1
        elif bs[k]>0: c['only_sub']+=1
        else: c['none']+=1
    return c
R={}
for nm,segf in [('retint3',reg_of),('E1',mk(E1)),('E3',mk(E3))]:
    c7=run(segf,S697); c6=run(segf,S686)
    R[nm]=dict(n697=dict(c7),n686=dict(c6))
    print('   X5 %-8s 697: both=%-3d only_sub=%-2d none=%-2d | 686: both=%-3d only_sub=%-2d none=%-2d'%(
        nm,c7['both'],c7['only_sub'],c7['none'],c6['both'],c6['only_sub'],c6['none']))
ck('X5a ret/int3 697=689/0/8',(R['retint3']['n697']['both'],R['retint3']['n697']['none'])==(689,8),R['retint3']['n697'])
ck('X5b E1 697=691/0/6',(R['E1']['n697']['both'],R['E1']['n697']['none'])==(691,6),R['E1']['n697'])
ck('X5c E3 697=691/0/6',(R['E3']['n697']['both'],R['E3']['n697']['none'])==(691,6),R['E3']['n697'])
ck('X5d 三口径下 686 都是 both=686/only_sub=0/none=0',
   all(v['n686']=={'both':686} for v in R.values()),{k:v['n686'] for k,v in R.items()})
# X6
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in suball:  brs[reg_of(r[0])]+=1
KR=set(brs); KM=set(brm)
ck('X6a 含次表 store 的区间 388',len(KR)==388,len(KR))
ck('X6b 其中 100%% 也含主表 store',KR<=KM,'%d/%d'%(len(KR&KM),len(KR)))
ck('X6c 「有次表无主表」区间 0',len(KR-KM)==0,len(KR-KM))
ck('X6d 含主表 store 的区间数',len(KM)>0,len(KM))
# X7
N8=[0x5d5b80,0x635f34,0x637114,0x638aa4,0x6cf196,0x6cf209,0x7b1b2b,0x7b27fb]
OK5={'0x5d5b80':'.?AVMultiplayerGameMode@@','0x6cf196':'.?AVSwizzleManagerClass@@','0x6cf209':'.?AVSwizzleManagerClass@@',
     '0x7b1b2b':'.?AVWinsockInterfaceClass@@','0x7b27fb':'.?AVWinsockInterfaceClass@@'}
host={}
for va in N8:
    a,b=reg_of(va)
    ms=[CLS[r[3]] for r in vts if a<=r[0]<b and MD[r[3]]==0]
    outer=[m for m in ms if not m.startswith('.?AV?$')]
    host[hex(va)]=dict(seg=[hex(a),hex(b)],all_mains=ms,outer=outer)
ck('X7a 8 条中 5 条取得非模板外层类名',sum(1 for v in host.values() if v['outer'])==5,
   sum(1 for v in host.values() if v['outer']))
ck('X7b 5 条类名与期望逐条一致',all(OK5[k] in host[k]['outer'] for k in OK5),OK5)
ck('X7c 3 条只有模板成员类主表',[k for k,v in host.items() if not v['outer']]==['0x635f34','0x637114','0x638aa4'],
   [k for k,v in host.items() if not v['outer']])
# X8
def slot_seq(r):
    a,b=reg_of(r[0])
    seq=sorted([x for x in vts if a<=x[0]<b and x[1]==r[1] and x[2]==r[2]])
    return seq
def cover(r): return any(x[0]>r[0] and MD[x[3]]==x[2] for x in slot_seq(r))
cov11=[r for r in S11 if cover(r)]
cov686=[r for r in S686 if cover(r)]
ck('X8a 11 条后继同槽位覆盖 3 条',len(cov11)==3,[hex(r[0]) for r in cov11])
ck('X8b 3 条全是 .?AVINoticeSink@@',all(CLS[r[3]]=='.?AVINoticeSink@@' for r in cov11),[CLS[r[3]] for r in cov11])
ck('X8c 686 后继覆盖 12 条 (1.7%)',len(cov686)==12,len(cov686))
ck('X8d 8 条未覆盖全是模板容器',all(CLS[r[3]].startswith('.?AV?$') for r in S11 if not cover(r)),'8')
print('   X8: 11 条 → 3 覆盖(INoticeSink) / 8 不覆盖(模板容器)；686 后继覆盖 12/686=1.7%%；富集 %0.1f 倍'%(27.3/1.7))
# X9
ck('X9a COL 指针恒 vt-4 1214/1214',all(P.dw(v-4) in COL for v in VT) and len(VT)==1214,sum(1 for v in VT if P.dw(v-4) in COL))
dx=collections.Counter(VT[v]-v for v in VT)
ck('X9b COL 地址-虚表地址 916 个取值',len(dx)==916,len(dx))
# X10
ck('X10a 686 ∪ 11 == 697 且不相交',len(set(r[0] for r in S686)|set(r[0] for r in S11))==697 and not (set(r[0] for r in S686)&set(r[0] for r in S11)),'')
ck('X10b 反控：E3 每入口 +1 字节后结果改变',
   run(mk(sorted(set(a+1 for a in E3))),S686)!={'both':686},dict(run(mk(sorted(set(a+1 for a in E3))),S686)))
OUT=dict(X1=dict(n697=len(S697),n686=len(S686),n11=len(S11),mdisp=dict(c4)),
  X2=dict(bends=nb,regions=len(REGION),nopstart=nopstart),
  X3=dict(tgt=len(SORT),tgt_ins=sum(1 for t in SORT if t in ASET),tgt_reg=sum(1 for t in SORT if t in RSET),zero=per[0]),
  X4=dict(pats=dict(collections.Counter(PR.values())),i=755,union=864),
  X5=R,X6=dict(KRn=len(KR),KMn=len(KM)),X7=host,
  X8=dict(cov11=[hex(r[0]) for r in cov11],cov686=len(cov686),nocov11=[hex(r[0]) for r in S11 if not cover(r)]),
  X9=dict(vt=len(VT),colptr=sum(1 for v in VT if P.dw(v-4) in COL),distinct=len(dx)),
  asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m14_authority.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
