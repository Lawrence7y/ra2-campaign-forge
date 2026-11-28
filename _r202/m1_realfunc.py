#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m1：把 R201 的 ret/int3 区间口径收紧为「真函数入口」口径，重算 697 条小位移装表的三分类。
R1 区间与边界数复算；R2 真函数入口三条判据 (i)CALLAT目标 (ii)序言 (iii)区间内有 ret；
R3 真函数口径下三分类 + nonfunc；R4 反控：错误过滤 / 关掉区间切分；R5 store 细节。
防 OOM：全段用 disasm_lite + 64KB 分块；仅目标地址单独 detail。"""
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
REGNAME=['eax','ecx','edx','ebx','esp','ebp','esi','edi']

# ---------- COL / VT ----------
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
print('VT=%d COL=%d'%(len(VT),len(COL)))

# ---------- 装表 store 提取（含 0x66 前缀分支）----------
def extract(strict_smalldisp=True):
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
sub=[r for r in vts if 1<=r[2]<=9 and MD[r[3]]!=0]
ck('R1a 小位移次表类 store == 697', len(sub)==697, len(sub))
ck('R1b 装 VT 总 %d / 主表 %d / 次表 %d'%(len(vts),len(mainall),len(suball)),
   len(vts)==len(mainall)+len(suball), (len(vts),len(mainall),len(suball)))

# ---------- 全段反汇编 ----------
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
INS.sort()
ADDRS=[a for a,_,_,_ in INS]
ck('R2a 全段指令数', len(INS)>500000, len(INS))
SORT=sorted(set(t for _,t in CALLAT)); TGT=set(SORT)
ck('R2b CALLAT 记录 %d / 去重目标 %d'%(len(CALLAT),len(SORT)), len(CALLAT)>60000, (len(CALLAT),len(SORT)))

# 区间
REGION=[];st=LO;nb=0;ENDRET=[]
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); ENDRET.append(mn.startswith('ret')); st=a+sz; nb+=1
if st<HI: REGION.append((st,HI)); ENDRET.append(False)
RL=[r[0] for r in REGION]
ck('R3a ret/int3 边界数 == 31967', nb==31967, nb)
ck('R3b 区间数 == 31968', len(REGION)==31968, len(REGION))

# ---------- 真函数入口判据 ----------
I2REG={}; 
for i,(a,sz,mn,op) in enumerate(INS): I2REG[a]=i
def first3(start):
    i=I2REG.get(start)
    if i is None: return []
    return INS[i:i+4]
def has_prologue(start):
    w=first3(start)
    if not w: return False
    m=[x[2] for x in w]; op=[x[3] for x in w]
    # push ebp; mov ebp,esp
    for k in range(min(3,len(m)-1)):
        if m[k]=='push' and op[k]=='ebp' and m[k+1]=='mov' and op[k+1].replace(' ','')=='ebp,esp': return True
        # mov edi,edi; push ebp; mov ebp,esp
        if m[k]=='mov' and op[k].replace(' ','')=='edi,edi':
            for j in range(k+1,min(k+3,len(m)-1)):
                if m[j]=='push' and op[j]=='ebp' and m[j+1]=='mov' and op[j+1].replace(' ','')=='ebp,esp': return True
    # sub esp,imm 作为首指令
    if m[0]=='sub' and op[0].startswith('esp, '): return True
    # push <reg> 作为首指令（frameless 参数保存）
    if m[0]=='push' and op[0] in ('ebx','esi','edi','ecx','edx','eax','ebp'): return True
    return False
REGINFO=[]
for i,(a,b) in enumerate(REGION):
    inT=a in TGT; pr=has_prologue(a)
    REGINFO.append(dict(a=a,b=b,inT=inT,pr=pr,hasret=ENDRET[i],len=b-a))
c1=sum(1 for r in REGINFO if r['inT']); c2=sum(1 for r in REGINFO if r['pr'])
c3=sum(1 for r in REGINFO if r['inT'] or r['pr']); c4=len(REGINFO)-c3
ck('R4a 判据(i) CALLAT 目标区间数 > 0 且 < 区间总数', 0<c1<len(REGINFO), c1)
ck('R4b 判据(ii) 序言区间数 > 0', 0<c2<len(REGINFO), c2)
ck('R4c (i)或(ii) 区间数', 0<c3<len(REGINFO), c3)
print('   R4: 区间 %d；(i)=%d (ii)=%d (i|ii)=%d 两者皆非=%d'%(len(REGINFO),c1,c2,c3,c4))
nol=[r['len'] for r in REGINFO if not(r['inT'] or r['pr'])]
print('   两者皆非的长度 p50=%d p90=%d max=%d 例地址 %s'%(
    statistics.median(nol),sorted(nol)[int(len(nol)*.9)],max(nol),[hex(r['a']) for r in REGINFO if not(r['inT'] or r['pr'])][:12]))
# hasret 单独：区间内是否有 ret（vs 以 int3 结束）
eh=sum(1 for r in REGINFO if r['hasret'])
ck('R4d 区间内有 ret 的区间数', 0<eh<len(REGINFO), eh)

# ---------- 归属 ----------
def reg_of(va):
    i=bisect.bisect_right(RL,va)-1
    return REGION[i] if i>=0 else None
RIDX={}
for i,r in enumerate(REGION): RIDX[r[0]]=i
brm=collections.defaultdict(int); brs=collections.defaultdict(int)
for r in mainall: brm[reg_of(r[0])]+=1
for r in suball:  brs[reg_of(r[0])]+=1
def classify(pred):
    c=collections.Counter()
    for r in sub:
        rg=reg_of(r[0])
        if rg is None: c['noreg']+=1; continue
        if not pred(rg): c['nonfunc']+=1; continue
        if brm[rg]>0 and brs[rg]>0: c['both']+=1
        elif brs[rg]>0: c['only_sub']+=1
        else: c['none']+=1
    return c
cALL=classify(lambda rg: True)
nALL=sum(cALL.values())
ck('R5a 无过滤（=R201 口径）689/0/8', (cALL['both'],cALL['only_sub'],cALL['none'])==(689,0,8), dict(cALL))
for nm,pred in [('i_CALLAT',lambda rg: rg[0] in TGT),
                ('ii_prolog',lambda rg: has_prologue(rg[0])),
                ('i_or_ii',lambda rg: rg[0] in TGT or has_prologue(rg[0])),
                ('i_and_ii',lambda rg: rg[0] in TGT and has_prologue(rg[0])),
                ('hasret',None)]:
    if pred is None: continue
    c=classify(pred); t=sum(c.values())
    ck('R5b %s 四数相加==%d'%(nm,t), c['both']+c['only_sub']+c['none']+c['nonfunc']+c['noreg']==697, dict(c))
    print('   R5 %-10s both=%-4d only_sub=%-3d none=%-3d nonfunc=%-4d noreg=%d'%(
        nm,c['both'],c['only_sub'],c['none'],c['nonfunc'],c['noreg']))
# 反控：错误过滤（起点任意相近 0xC3 字节）
def bad_pred(rg):
    o=P.r2o(rg[0]); 
    return o is not None and 0xC3 in RAW[o:o+4]
cb=classify(bad_pred)
ck('R6a 错误过滤三分类与正确过滤不同', (cb['both'],cb['only_sub'],cb['none'])!=(cALL['both'],cALL['only_sub'],cALL['none']), dict(cb))
# 反控：关掉区间切分（整段一个区间）
cN=collections.Counter()
for r in sub:
    if len(mainall)>0 and len(suball)>0: cN['both']+=1
ck('R6b 不切区间 both==697 / none==0', (cN['both'],cN['none'])==(697,0), dict(cN))
# ---------- store 细节：重装 / 段分布 ----------
byreg=collections.defaultdict(list)
for r in vts: byreg[(reg_of(r[0]),r[1])].append(r)
dup=[]
for r in sub:
    k=(reg_of(r[0]),r[1])
    same=[x for x in byreg[k] if x[3]==r[3]]
    if len(same)>1: dup.append(r[0])
ck('R7a 同区间同基址同 imm 重复装表 > 0', len(dup)>0, len(dup))
seg=collections.Counter(P.sec_of(r[3]) for r in sub)
ck('R7b 697 条 imm 落段分布', sum(seg.values())==697, dict(seg))
dist=collections.Counter(P.dw(r[3]-4)-r[3] for r in sub)
print('   R7c imm 到 COL 记录的距离分布 %s'%dict(sorted(dist.items())))
ck('R7d 距离为常数', len(dist)==1, dict(dist))
OUT=dict(nb=nb,nreg=len(REGION),c1=c1,c2=c2,c3=c3,c4=c4,
   nol_p50=statistics.median(nol),nol_p90=sorted(nol)[int(len(nol)*.9)],nol_max=max(nol),
   hasret=eh,catALL=dict(cALL),dupN=len(dup),dupAddrs=[hex(x) for x in dup[:10]],seg=dict(seg),
   dist={str(k):v for k,v in dist.items()},asserts=N,fails=fails)
json.dump(OUT,open('/home/t628/projects/ra2-campaign-forge/_r202/m1_realfunc.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
