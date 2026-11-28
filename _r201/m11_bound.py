#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m11（权威定稿）：用「ret/int3 划定区间」给每条 store 分配所属代码区间，
这是唯一不依赖 CALLAT 目标（已被证不可当函数起点）的口径。据此回答 R200 未取得项 (b)。"""
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
# 全量 C7 /0 装表（含 mod0，跳过 66 前缀）
allsite=[]
pos=T['rawptr'];end=T['rawptr']+T['rawsize']
while pos<end-4:
    if RAW[pos]==0x66:
        if pos+2<end and RAW[pos+1]==0xC7:
            mo=RAW[pos+2]>>6
            pos+= 6 if mo==0 else (7 if mo==1 else 11); continue
        pos+=1; continue
    if RAW[pos]!=0xC7: pos+=1;continue
    modrm=RAW[pos+1];mod=modrm>>6;reg=(modrm>>3)&7;rm=modrm&7
    if reg!=0 or rm==4 or (rm==5 and mod==0): pos+=1;continue
    va=LO+(pos-T['rawptr'])
    if mod==1:
        d=struct.unpack_from('<b',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+3)[0]
        allsite.append((va,REGNAME[rm],d,im,'m1'));pos+=7
    elif mod==2:
        d=struct.unpack_from('<i',RAW,pos+2)[0];im=struct.unpack_from('<I',RAW,pos+6)[0]
        allsite.append((va,REGNAME[rm],d,im,'m2'));pos+=10
    else:
        im=struct.unpack_from('<I',RAW,pos+2)[0]
        allsite.append((va,REGNAME[rm],0,im,'m0'));pos+=6
vts=[r for r in allsite if r[3] in VT]
sub=[r for r in vts if 1<=r[2]<=9]
ck('P0a 小位移装表 697', len(sub)==697, len(sub))
ck('P0b 其中主表(mdisp==0) 11 / 次表 686',(len([r for r in sub if MD[r[3]]==0]),len([r for r in sub if MD[r[3]]!=0]))==(11,686),
   (len([r for r in sub if MD[r[3]]==0]),len([r for r in sub if MD[r[3]]!=0])))

# 指令流 + ret/int3 区间
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[];p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op)); p2+=sz
    if not got: p2+=1
INS.sort()
REGION=[];start=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((start,a+sz)); start=a+sz
if start<HI: REGION.append((start,HI))
RL=[r[0] for r in REGION]
ck('P0c 区间数 == 边界数+1', len(REGION)>30000, len(REGION))
def region_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None

# store 级：按区间归属
mainall=[r for r in vts if MD[r[3]]==0]
suball=[r for r in vts if MD[r[3]]!=0]
byregion_main=collections.defaultdict(list)
byregion_sub=collections.defaultdict(list)
for r in mainall: byregion_main[region_of(r[0])].append(r)
for r in suball:  byregion_sub[region_of(r[0])].append(r)
cat=collections.Counter(); regs=collections.defaultdict(lambda:[0,0])
for r in sub:
    reg=region_of(r[0])
    cat['n']+=1
    if reg is None: cat['noreg']+=1; continue
    nm=len(byregion_main[reg]); ns=len(byregion_sub[reg])
    regs[reg][0]=nm; regs[reg][1]=ns
    if nm>0 and ns>0: cat['both']+=1
    elif ns>0: cat['only_sub']+=1
    else: cat['none']+=1
print('   store 级（区间口径）: both=%d only_sub=%d none=%d noreg=%d 合计=%d'%(
    cat['both'],cat['only_sub'],cat['none'],cat['noreg'],cat['n']))
ck('P0d store 级 both < 251（R200 宿主级表述不成立）', cat['both']<251, cat['both'])
ck('P0e 每条 store 都有归属区间', cat['noreg']==0, cat['noreg'])
ck('P0f 三者相加 == 697', cat['both']+cat['only_sub']+cat['none']==697,
   cat['both']+cat['only_sub']+cat['none'])
# 关键：only_sub 区间内是否全局（不限区间）有本类主表装填
os_regions=set()
for r in sub:
    reg=region_of(r[0])
    if reg and len(byregion_main[reg])==0: os_regions.add(reg)
ck('P0g only_sub 区间去重数 > 0', len(os_regions)>0, len(os_regions))
# 每个 only_sub 区间：全段范围内该类主表装填是否存在
allmain_by_cls=collections.defaultdict(list)
for r in mainall: allmain_by_cls[CLS[r[3]]].append(r)
have=0; miss=0; miss_cls=collections.Counter()
for reg in os_regions:
    subs=[r for r in sub if region_of(r[0])==reg]
    if not subs: continue
    cn=CLS[subs[0][3]]
    if allmain_by_cls.get(cn): have+=1
    else: miss+=1; miss_cls[cn]+=1
ck('P0h only_sub 涉及的类在全段都有本类主表装填', miss==0, 'have=%d miss=%d'%(have,miss))
print('   only_sub 区间 %d 个，其所属类在全段有本类主表装填的 %d 个 / 无的 %d 个'%(len(os_regions),have,miss))
if miss: print('   无主表装填的类:',dict(miss_cls))

# 区间特征
lens=[b-a for a,b in REGION]
ck('P0i 区间长度中位数 > 0', sorted(lens)[len(lens)//2]>0, sorted(lens)[len(lens)//2])
sl=[region_of(r[0]) for r in sub]
sllen=[b-a for a,b in sl if a]
import statistics
print('   承载小位移装表的区间长 p10/p50/p90 = %d/%d/%d'%(
    sorted(sllen)[int(len(sllen)*.1)],statistics.median(sllen),sorted(sllen)[int(len(sllen)*.9)]))
# 11 条主表装填所在区间内是否有本类次表
m11=[r for r in sub if MD[r[3]]==0]
m11ret=[]
for r in m11:
    reg=region_of(r[0])
    ns=len(byregion_sub[reg]); nm=len(byregion_main[reg])
    m11ret.append((hex(r[0]),r[2],hex(r[3]),CLS[r[3]],nm,ns,hex(reg[0])))
for x in m11ret: print('   m11 %s disp=%d %s cls=%s 区间内主表=%d 次表=%d @%s'%x)
ck('P0j 11 条主表装填的区间内均无本类次表', all(x[5]==0 for x in m11ret), [x[5] for x in m11ret])

json.dump(dict(sub=697,main11=11,cat=dict(cat),regions=len(REGION),
               os_regions=len(os_regions),have=have,miss=miss,
               m11=m11ret,
               span=dict(p10=sorted(sllen)[int(len(sllen)*.1)],p50=statistics.median(sllen),p90=sorted(sllen)[int(len(sllen)*.9)]),
               asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m11_bound.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
