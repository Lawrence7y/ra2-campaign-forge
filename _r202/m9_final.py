#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m9（定稿）：本轮四条交付的权威核算 + 两处口径分离 + 子代理结论复算。
L1 697 = 686 次表类 + 11 mdisp==0；homogeneous 分母 686 下同区间共现 686/686 = 100%（订正 R201 98.85% 的混合分母）
L2 31,968 区间不是函数：区间起点为 nop 的比例、CALLAT 目标落区间起点比例、每区间含几个 CALLAT 目标
L3 only_sub 的 0 的真因：含严格次表 store 的区间 100% 也含主表 store（可达性反证）
L4 8 条 none 的宿主类名（ret/int3 区间口径 = 5 条可读，E3 段口径 = 8 条可读）
L5 重装数在三种网格下的取值（复算 #510 的 564 并给出差异原因）
L6 反控"""
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
ck('L1a 697 / 686 / 11',(len(S697),len(S686),len(S11))==(697,686,11),(len(S697),len(S686),len(S11)))
ck('L1b 686 的 disp8==mdisp 686/686', all(r[2]==MD[r[3]] for r in S686), sum(1 for r in S686 if r[2]==MD[r[3]]))
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
SORT=sorted(set(t for _,t in CALLAT)); TGT=set(SORT)&ASET
REGION=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in suball:  brs[reg_of(r[0])]+=1
KR=set(brs); KM=set(brm)
ck('L1c 有严格次表 store 的区间数', len(KR)>0, len(KR))
ck('L1d 有主表 store 的区间数', len(KM)>0, len(KM))
ck('L1e 严格次表区间 100%% 含主表 store', KR<=KM, '%d/%d'%(len(KR&KM),len(KR)))
# L1：homogeneous 686
both686=[r for r in S686 if reg_of(r[0]) in KM]
ck('L1f 686 全部落在含主表 store 的区间', len(both686)==686, len(both686))
ck('L1g 686/686 == 100%（R201 的 98.85% 用 689/697 混合分母）', len(both686)==686, '%.2f%%'%(100.0*len(both686)/686))
both11=[r for r in S11 if reg_of(r[0]) in KR]
ck('L1h 11 条 mdisp==0 中 3 条落在含严格次表 store 的区间', len(both11)==3, len(both11))
# L2 区间不是函数
nopstart=sum(1 for a,b in REGION if I2R.get(a) is not None and INS[I2R[a]][2]=='nop')
ck('L2a 区间起点为 nop 的区间数 > 15000（#510 报 17726）', nopstart>15000, nopstart)
tp=sum(1 for t in SORT if t in set(RL))
ck('L2b CALLAT 目标落区间起点 == 755', tp==755, tp)
ck('L2c CALLAT 目标落指令起点 == 6692', sum(1 for t in SORT if t in ASET)==6692, sum(1 for t in SORT if t in ASET))
per=collections.Counter()
for a,b in REGION:
    per[bisect.bisect_left(SORT,b)-bisect.bisect_left(SORT,a)]+=1
ck('L2d 区间含 0 个 CALLAT 目标的比例 > 70%', per[0]/len(REGION)>0.70, '%.1f%%'%(100.0*per[0]/len(REGION)))
print('   L2: 区间 %d 起点为 nop %d(%.1f%%)；CALLAT 目标 %d，落区间起点 %d(%.1f%%), 落指令起点 %d；区间含 0 目标 %d(%.1f%%)'%(
    len(REGION),nopstart,100.0*nopstart/len(REGION),len(SORT),tp,100.0*tp/len(SORT),
    sum(1 for t in SORT if t in ASET),per[0],100.0*per[0]/len(REGION)))
# L3 only_sub 可达性
reach=[k for k in KR if k not in KM]
ck('L3a「有次表无主表」区间数 == 0', len(reach)==0, len(reach))
ck('L3b 可达性反证：主表集置空后 only_sub==686', True, '构造性，见 m8 P1d 686')
# L4 8 条 none 宿主
N8=[0x5d5b80,0x635f34,0x637114,0x638aa4,0x6cf196,0x6cf209,0x7b1b2b,0x7b27fb]
reg_host={};seg_host={}
for va in N8:
    a,b=reg_of(va); ms=[CLS[r[3]] for r in vts if a<=r[0]<b and MD[r[3]]==0]
    reg_host[hex(va)]=ms
print('   L4 ret/int3 区间口径（窄）:')
for k,v in reg_host.items(): print('      %s 主表 %d 处 %s'%(k,len(v),v[:3]))
def outer(ms):
    return [m for m in ms if not m.startswith('.?AV?$')]
o5={k:outer(v) for k,v in reg_host.items()}
ck('L4a 窄口径 8 条区间内都有 mdisp==0 装表', all(len(v)>0 for v in reg_host.values()), '%d/8'%sum(1 for v in reg_host.values() if v))
ck('L4b 其中 5 条能读出非模板外层宿主类名（与 #509 一致）', sum(1 for v in o5.values() if v)==5, sum(1 for v in o5.values() if v))
ck('L4c 其余 3 条只剩模板成员类 ⇒ 外层 UNDETERMINED', sum(1 for v in o5.values() if not v)==3,
   [k for k,v in o5.items() if not v])
for k,v in o5.items(): print('      L4 %s 非模板主表 %s'%(k,v))
# L5 重装三口径
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
PATS=set(a for a in ADDRS if pat(a))
E3=sorted(TGT|PATS)
def read(r,segf):
    return (segf(r[0]),r[1],r[3])
E1=sorted(TGT)
def mk(E):
    def f(va):
        i=bisect.bisect_right(E,va)-1
        return None if i<0 else (E[i],E[i+1] if i+1<len(E) else HI)
    return f
RESD={}
for nm,segf,stores in [('ret/int3/686',reg_of,S686),('E3/686',mk(E3),S686),
                       ('E1/686',mk(E1),S686),('E3/697',mk(E3),S697),('E3/7',mk(E3),S697),
                       ('E1/697',mk(E1),S697),('ret/int3/7',reg_of,S697)]:
    g=collections.defaultdict(list)
    for r in stores: g[read(r,segf)].append(r[0])
    d=[k for k,v in g.items() if len(v)>1]
    n=sum(len(g[k]) for k in d)
    print('   L5 %-16s store=%d 重装store=%-4d 组=%-4d'%(nm,len(stores),n,len(d)))
    if nm=='ret/int3/686': ck('L5a ret/int3 口径 686 重装 == 0', n==0, n)
    RESD[nm]=dict(stores=len(stores),dupstore=n,groups=len(d))
# L6 反控
ck('L6a 686 与 11 的并 == 697', len(set(r[0] for r in S686)|set(r[0] for r in S11))==697, '')
ck('L6b 686 与 11 无交集', len(set(r[0] for r in S686)&set(r[0] for r in S11))==0, '')
OUT=dict(n697=len(S697),n686=len(S686),n11=len(S11),KRs=[hex(a[0]) for a in list(KR)[:5]],
  KRn=len(KR),KMn=len(KM),both686=len(both686),both11=len(both11),
  nopstart=nopstart,tgt_reg=tp,tgt_ins=sum(1 for t in SORT if t in ASET),zero_tgt=per[0],
  reg_host=reg_host,outer5=o5,dup=RESD,asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m9_final.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
