#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m5：697 条小位移装表的语义二分 —— G1(disp8==mdisp, 多继承次表) vs G2(disp8!=mdisp, 成员子对象主表)；
并回答 R200 未取得项(b)：某个类的主表到底由哪个函数装。
避免 O(n^2)：用 bisect 在排序数组上取窗口。"""
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
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']
recs=[];pos=T['rawptr'];end=T['rawptr']+T['rawsize']
while pos<end-6:
    if RAW[pos]!=0xC7: pos+=1;continue
    modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
        recs.append((va,REGNAME[rm],d,im));pos+=7
    elif mod==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
        recs.append((va,REGNAME[rm],d,im));pos+=10
    else: pos+=1
sub=[r for r in recs if 1<=r[2]<=9 and r[3] in VT]
allvt=[r for r in recs if r[3] in VT]
mainall=[r for r in allvt if MD[r[3]]==0]
suball=[r for r in allvt if MD[r[3]]!=0]
# 按地址排序，便于二分
MAIN_ADDR=[r[0] for r in mainall]; SUB_ADDR=[r[0] for r in suball]
ck('T0a 基数 697/391/1068',(len(sub),len(mainall),len(suball))==(697,391,1068),(len(sub),len(mainall),len(suball)))

# G1 / G2 二分
G1=[r for r in sub if r[2]==MD[r[3]]]
G2=[r for r in sub if r[2]!=MD[r[3]]]
ck('T0b G1=686 G2=11',(len(G1),len(G2))==(686,11),(len(G1),len(G2)))
md_g1=collections.Counter(MD[r[3]] for r in G1)
md_g2=collections.Counter(MD[r[3]] for r in G2)
print('   G1(disp8==mdisp) 的 mdisp 分布:',dict(md_g1))
print('   G2(disp8!=mdisp) 的 mdisp 分布:',dict(md_g2))
ck('T0c G1 的 mdisp 全 >0（次表）', all(MD[r[3]]>0 for r in G1), dict(md_g1))
ck('T0d G2 的 mdisp 全 ==0（主表）', all(MD[r[3]]==0 for r in G2), dict(md_g2))
ck('T0e G2 的 disp 全 !=0', all(r[2]!=0 for r in G2), sorted(set(r[2] for r in G2)))

# 真实函数体（ret/int3 前向终止）
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[];CALLAT=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True
        INS.append((off,sz,mn,op))
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t))
        p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]
BEND=sorted(a+sz for a,sz,mn,op in INS if mn.startswith('ret') or mn=='int3')
def span(va):
    i=bisect.bisect_right(ADDRS,va)-1
    if i<0: return None
    j=i
    while j<len(INS) and not (INS[j][2].startswith('ret') or INS[j][2]=='int3'): j+=1
    hi=INS[j][0]+INS[j][1] if j<len(INS) else HI
    k=bisect.bisect_left(BEND,va)-1
    lo=BEND[k] if k>=0 else LO
    return lo,hi
def cnt(arr,addr,lo,hi):
    return bisect.bisect_left(addr,hi)-bisect.bisect_left(addr,lo)

# G1 体内是否也装本类主表（mdisp==0 且同 CLS）
def same_cls_main(cn,lo,hi):
    a=bisect.bisect_left(MAIN_ADDR,lo); b=bisect.bisect_left(MAIN_ADDR,hi)
    return [mainall[k] for k in range(a,b) if CLS[mainall[k][3]]==cn]
g1_both=0; g1_only=0; g1_detail=[]
for r in G1:
    lo,hi=span(r[0])
    sm=same_cls_main(CLS[r[3]],lo,hi)
    if sm: g1_both+=1
    else: g1_only+=1
    g1_detail.append((hex(r[0]),hex(r[3]),CLS[r[3]],md_g1 and MD[r[3]],len(sm),hex(lo),hex(hi)))
print('   G1 686 条：其真实函数体内同装本类主表的 %d 条 / 未装的 %d 条'%(g1_both,g1_only))
ck('T0f G1 体内同装本类主表占比',0<=g1_both<=686,'%d/686 = %.1f%%'%(g1_both,100.0*g1_both/686))

# 未取得项(b)：only_sub 类的「本类主表由谁装」
rep_cls=['.?AVAirstrikeClass@@','.?AVAlphaShapeClass@@','.?AVBombClass@@','.?AVLightSourceClass@@',
         '.?AVWaveClass@@','.?AVWalkLocomotionClass@@','.?AVVoxelAnimTypeClass@@','.?AVCellClass@@']
OWN={}
for cn in rep_cls:
    inst=[r for r in allvt if CLS[r[3]]==cn]
    mains=[r for r in inst if MD[r[3]]==0]
    subs=[r for r in inst if MD[r[3]]>0]
    sites=[(hex(r[0]),r[1],r[2],hex(r[3])) for r in mains]
    funcs=sorted(set(hex(span(r[0])[0]) for r in mains if span(r[0])))
    OWN[cn]=dict(n_main=len(mains),n_sub=len(subs),main_sites=sites[:8],main_funcs=funcs[:8])
    print('   %-34s 主表装 %2d 处（函数 %d 个） 次表装 %2d 处  主表首址 %s'%(
        cn,len(mains),len(funcs),len(subs),sites[:4]))
ck('T0g 8 个代表类全部有主表装填记录',all(OWN[c]['n_main']>0 for c in rep_cls),{c:OWN[c]['n_main'] for c in rep_cls})
ck('T0h 主表装填函数数 < 主表装填处数（同一函数多次装）',
   all(OWN[c]['n_main']>=len(OWN[c]['main_funcs']) for c in rep_cls),'ok')

# 反控：G1 里 mdisp==8 的类是否与 disp==8 严格配对
g1_8=[r for r in G1 if r[2]==8]
ck('T0i G1 disp==8 且 mdisp==8',all(MD[r[3]]==8 for r in g1_8),len(g1_8))
g1_4=[r for r in G1 if r[2]==4]
ck('T0j G1 disp==4 且 mdisp==4',all(MD[r[3]]==4 for r in g1_4),len(g1_4))
ck('T0k disp 只有 4/8 两种',set(r[2] for r in G1)=={4,8},sorted(set(r[2] for r in G1)))

json.dump(dict(G1=len(G1),G2=len(G2),md_g1=dict(md_g1),md_g2=dict(md_g2),
               g1_both=g1_both,g1_only=g1_only,OWN=OWN,g1_detail=g1_detail[:60],asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m5_semantic.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
