#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m10（收口定稿）：本轮四条可复算结论的最终核算。
K1 R200 only_main 命名/判据不一致 + 11 宿主 6/5 划分
K2 R200 窗口跨函数污染（中位数 5 个体）
K3 697 条 = 686 次表(mdisp==0? no, mdisp>0) + 11 主表(disp!=mdisp)；两者语义不同
K4 主表装填面：8 代表类两口径交集一致，每类 4..6 处，分布在同一类的多个函数
所有数字与 m1..m9 对齐；正反控同命令。"""
import sys, struct, json, bisect, collections, statistics
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
# R200 原口径（不含 mod0）—— 用于 K1/K2 复现
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
ck('K1a R200 口径 697 复现', len(sub)==697, len(sub))
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
INS.sort();ADDRS=[a for a,_,_,_ in INS]
BEND=sorted(a+sz for a,sz,mn,op in INS if mn.startswith('ret') or mn=='int3')
SORT=sorted(set(t for _,t in CALLAT))
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def next_entry(c):
    i=bisect.bisect_right(SORT,c)
    return SORT[i] if i<len(SORT) else HI
def span(va):
    i=bisect.bisect_right(ADDRS,va)-1
    if i<0: return None
    j=i
    while j<len(INS) and not (INS[j][2].startswith('ret') or INS[j][2]=='int3'): j+=1
    hi=INS[j][0]+INS[j][1] if j<len(INS) else HI
    k=bisect.bisect_left(BEND,va)-1
    return (BEND[k] if k>=0 else LO),hi

# ---- K1：R200 三分类 + 6/5 划分 ----
byhost=collections.defaultdict(list)
for r in sub: byhost[host_of(r[0])].append(r)
cat=collections.Counter(); om_detail=[]
for h,rs in byhost.items():
    if h is None: continue
    hi=min(next_entry(h),h+4096); o=P.r2o(h)
    hm=hs=False
    for i in md.disasm(RAW[o:o+(hi-h)],h):
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv=int(i.op_str.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv not in VT: continue
            if MD[iv]==0: hm=True
            else: hs=True
    k='both' if (hm and hs) else ('only_sub' if hs else 'only_main')
    cat[k]+=1
    if k=='only_main': om_detail.append((h,hm,hs,hi-h))
ck('K1b R200 三分类 251/0/11', (cat['both'],cat['only_sub'],cat['only_main'])==(251,0,11), dict(cat))
hm6=sum(1 for _,hm,_,_ in om_detail if hm); zero=sum(1 for _,hm,hs,_ in om_detail if not hm and not hs)
ck('K1c only_main 里装主表 6 / 零装填 5', (hm6,zero)==(6,5), (hm6,zero))
print('   K1: only_main 11 宿主 -> 装主表 %d / 零装填 %d；命名 only_main 与判据 not(has_main and has_sub) 不符'%(hm6,zero))

# ---- K2：窗口跨函数污染 ----
pol=[]
for h in byhost: 
    if h is None: continue
    hi=min(next_entry(h),h+4096)
    pol.append(bisect.bisect_left(BEND,hi)-bisect.bisect_left(BEND,h))
ck('K2a 窗口内 ret 体中位数 >=2', statistics.median(pol)>=2,
   'p50=%s p90=%s max=%s'%(statistics.median(pol),sorted(pol)[int(len(pol)*.9)],max(pol)))
n1=sum(1 for x in pol if x==1)
print('   K2: 262 窗口内 ret 体 p50=%d mean=%.2f max=%d；恰含 1 个函数的窗口 %d 个(%.1f%%)'%(
    statistics.median(pol),sum(pol)/len(pol),max(pol),n1,100.0*n1/len(pol)))
ck('K2b 恰含 1 函数的窗口不足一半', n1<len(pol)/2, '%d/%d'%(n1,len(pol)))

# ---- K3：697 二分 + 语义 ----
G1=[r for r in sub if r[2]==MD[r[3]]]; G2=[r for r in sub if r[2]!=MD[r[3]]]
ck('K3a 686 / 11', (len(G1),len(G2))==(686,11), (len(G1),len(G2)))
ck('K3b G1 的 mdisp 全 >0', all(MD[r[3]]>0 for r in G1), dict(collections.Counter(MD[r[3]] for r in G1)))
ck('K3c G2 的 mdisp 全 ==0', all(MD[r[3]]==0 for r in G2), dict(collections.Counter(MD[r[3]] for r in G2)))
ck('K3d G1 只含 disp 4/8', set(r[2] for r in G1)=={4,8}, sorted(set(r[2] for r in G1)))
ck('K3e G2 只含 disp 4/8', set(r[2] for r in G2)=={4,8}, sorted(set(r[2] for r in G2)))
# G1 体内是否同装本类主表（用 ret 体）
same=0
for r in G1:
    lo,hi=span(r[0])
    cn=CLS[r[3]]
    hit=False
    o=P.r2o(lo)
    for i in md.disasm(RAW[o:o+(hi-lo)],lo):
        if i.mnemonic=='mov' and i.op_str.startswith('dword ptr [') and ', 0x' in i.op_str:
            try: iv=int(i.op_str.rsplit(', ',1)[1],16)
            except Exception: continue
            if iv in VT and MD[iv]==0 and CLS[iv]==cn: hit=True;break
    if hit: same+=1
ck('K3f G1 体内同装本类主表占比 <5%', same<len(G1)*0.05, '%d/%d = %.1f%%'%(same,len(G1),100.0*same/len(G1)))
print('   K3: 697 = 686 次表(disp8==mdisp, mdisp 4/8) + 11 主表(disp8!=mdisp, mdisp==0)；G1 体内同装本类主表 %d 条'%same)

# ---- K4：主表装填面 ----
rep=['.?AVAirstrikeClass@@','.?AVAlphaShapeClass@@','.?AVBombClass@@','.?AVLightSourceClass@@',
     '.?AVWaveClass@@','.?AVWalkLocomotionClass@@','.?AVVoxelAnimTypeClass@@','.?AVCellClass@@']
OWN={}
for cn in rep:
    sites=[]
    o=None
    # 用字节扫描 mod0 直接取（简化：在 G1 所属类的体内找主表装填）
    found=[]
    pos=T['rawptr']
    while pos<end-4:
        if RAW[pos]==0x66:
            if pos+2<end and RAW[pos+1]==0xC7:
                mo=RAW[pos+2]>>6
                pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
            pos+=1; continue
        if RAW[pos]!=0xC7: pos+=1;continue
        modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
        if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
        if mod==1:
            im=struct.unpack_from('<I',RAW,pos+3)[0]
            if im in VT and MD[im]==0 and CLS[im]==cn: found.append(LO+(pos-T['rawptr']))
            pos+=7
        elif mod==2:
            im=struct.unpack_from('<I',RAW,pos+6)[0]
            if im in VT and MD[im]==0 and CLS[im]==cn: found.append(LO+(pos-T['rawptr']))
            pos+=10
        else:
            im=struct.unpack_from('<I',RAW,pos+2)[0]
            if im in VT and MD[im]==0 and CLS[im]==cn: found.append(LO+(pos-T['rawptr']))
            pos+=6
    fs=set()
    for s0 in found:
        sp=span(s0)
        if sp: fs.add(sp[0])
    OWN[cn]=dict(n=len(found),funcs=len(fs),sites=[hex(x) for x in found[:6]])
    print('   %-34s 主表装填 %2d 处，分布 %d 个函数 %s'%(cn,len(found),len(fs),OWN[cn]['sites'][:3]))
ck('K4a 8 个代表类主表装填数在 4..6', all(4<=OWN[c]['n']<=6 for c in rep), {c:OWN[c]['n'] for c in rep})
ck('K4b 每类主表装填分布 >=2 个函数', all(OWN[c]['funcs']>=2 for c in rep), {c:OWN[c]['funcs'] for c in rep})
ck('K4c 装填处数 == 函数数（每函数装一次）', all(OWN[c]['n']==OWN[c]['funcs'] for c in rep), {c:(OWN[c]['n'],OWN[c]['funcs']) for c in rep})

json.dump(dict(K1=dict(cat=dict(cat),om_has_main=hm6,om_zero=zero),
               K2=dict(p50=statistics.median(pol),mean=sum(pol)/len(pol),max=max(pol),n1=n1,n=len(pol)),
               K3=dict(G1=len(G1),G2=len(G2),g1_same_main=same),
               K4=OWN,asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m10_verdict.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
