#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m6：对 R202 自己的函数入口网格做「污染自检」——用 R201 批评 R200 的同一把尺子量 E3。
J1 每个 686 store 所在 E3 段内的 ret/int3 区间数分布（p50/mean/max）；
J2 双重归属（同时要求：同 ret/int3 区间 且 同 E3 段）下的三分类；
J3 与 R201 窗口口径同尺对照（窗口内区间数 p50=5）；
J4 结论稳健性：只有 both 数随口径变动，only_sub/none 在 686 口径下恒 0。"""
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
S686=[r for r in vts if 1<=r[2]<=9 and MD[r[3]]!=0]
S11 =[r for r in vts if 1<=r[2]<=9 and MD[r[3]]==0]
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
REGION=[];st=LO;BEND=[]
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); BEND.append(a+sz); st=a+sz
if st<HI: REGION.append((st,HI))
RL=[r[0] for r in REGION]
BENDs=sorted(BEND)
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
afterint3=set()
ENDMN=[]
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3': ENDMN.append(mn)
E3=sorted(TGT|PATS|afterint3)
def seg(va):
    i=bisect.bisect_right(E3,va)-1
    if i<0: return None
    return (E3[i], E3[i+1] if i+1<len(E3) else HI)
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
# ---- J1 自污染：686 store 所在 E3 段内 ret/int3 区间数 ----
pol=[]
for r in S686:
    a,b=seg(r[0])
    pol.append(bisect.bisect_left(BENDs,b)-bisect.bisect_left(BENDs,a))
ck('J1a 段内区间数分布已算', len(pol)==686, len(pol))
n1=sum(1 for x in pol if x==1)
print('   J1: 686 store 所在 E3 段内 ret/int3 区间数 p50=%d mean=%.2f max=%d；恰 1 个 %d(%.1f%%)'%(
    statistics.median(pol),sum(pol)/len(pol),max(pol),n1,100.0*n1/len(pol)))
ck('J1b 与 R201 窗口口径 p50=5 的对照已给出', True, 'E3 p50=%d vs R200窗口 p50=5'%statistics.median(pol))
# ---- J2 双重归属 ----
bm=collections.defaultdict(int); bs=collections.defaultdict(int)
bm2=collections.defaultdict(int); bs2=collections.defaultdict(int)
for r in mainall:
    bm[reg_of(r[0])]+=1; bm2[seg(r[0])]+=1
for r in suball:
    bs[reg_of(r[0])]+=1; bs2[seg(r[0])]+=1
c=collections.Counter()
for r in S686:
    rg=reg_of(r[0]); sg=seg(r[0])
    ok_main = (bm[rg]>0) or (bm2[sg]>0)
    ok_sub  = (bs[rg]>0) or (bs2[sg]>0)
    if ok_main and ok_sub: c['both']+=1
    elif ok_sub: c['only_sub']+=1
    else: c['none']+=1
ck('J2a 双重归属 686 both==686', c['both']==686, dict(c))
ck('J2b 双重归属 only_sub==0 / none==0', (c['only_sub'],c['none'])==(0,0), dict(c))
# 更严：要求同一 ret/int3 区间内同时有主表和次表（=R201 E5 口径）+ 同 E3 段
c2=collections.Counter()
for r in S686:
    rg=reg_of(r[0]); sg=seg(r[0])
    if bm[rg]>0 and bs[rg]>0 and bm2[sg]>0 and bs2[sg]>0: c2['both']+=1
    elif bs[rg]>0 and bs2[sg]>0: c2['only_sub']+=1
    else: c2['none']+=1
ck('J2c 最严（同区间且同段）686 结果', True, dict(c2))
print('   J2: 最严双重归属 686 -> both=%d only_sub=%d none=%d'%(c2['both'],c2['only_sub'],c2['none']))
# ---- J3 11 条主表 store 在 E3 口径下的归属 ----
c11=collections.Counter()
for r in S11:
    rg=reg_of(r[0]); sg=seg(r[0])
    if bm[rg]>0 and bs[rg]>0: c11['both']+=1
    elif bs[rg]>0: c11['only_sub']+=1
    else: c11['none']+=1
ck('J3a 11 条主表 store 在 R201 区间口径下 8 none / 3 both', (c11['none'],c11['both'])==(8,3), dict(c11))
c11b=collections.Counter()
for r in S11:
    sg=seg(r[0])
    if bm2[sg]>0 and bs2[sg]>0: c11b['both']+=1
    elif bs2[sg]>0: c11b['only_sub']+=1
    else: c11b['none']+=1
ck('J3b 11 条在 E3 段口径下 none 数 <= 8', c11b['none']<=8, dict(c11b))
print('   J3: 11 条主表 store：R201 区间口径 none=%d both=%d；E3 段口径 none=%d both=%d'%(
    c11['none'],c11['both'],c11b['none'],c11b['both']))
# ---- J4 稳健性总表 ----
rows=[]
for nm,fn in [('R201区间',reg_of),('E3段',seg)]:
    bmm=bm if nm=='R201区间' else bm2
    bss=bs if nm=='R201区间' else bs2
    cc=collections.Counter()
    for r in S686:
        k=fn(r[0])
        if bmm[k]>0 and bss[k]>0: cc['both']+=1
        elif bss[k]>0: cc['only_sub']+=1
        else: cc['none']+=1
    rows.append((nm,dict(cc)))
ck('J4a 两口径下 686 都是 both=686/only_sub=0/none=0',
   all(r[1].get('both')==686 and not r[1].get('only_sub') and not r[1].get('none') for r in rows),
   rows)
OUT=dict(pol=dict(n=len(pol),p50=statistics.median(pol),mean=sum(pol)/len(pol),max=max(pol),n1=n1),
  dual=dict(c),strict=dict(c2),s11_r201=dict(c11),s11_E3=dict(c11b),stab=rows,
  E3=len(E3),asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m6_selfpollute.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
