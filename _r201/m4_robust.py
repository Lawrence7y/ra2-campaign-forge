#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R201 m4：三种函数体定义下「主表+子表同体双装」的鲁棒性，以及 R200 大窗口的跨函数污染量。
体定义：
 V1 ret/int3 前向终止（m3 口径）
 V2 R200 口径：CALLAT 目标 -> min(下一 CALLAT 目标, +4096)
 V3 ret/int3 + 起点守卫：体起点必须是 CALLAT 目标或前一字节 ∈ {0x90,0xC3,0xCC,0x00,0xFF}
输出：每口径 both/only_sub/none；R200 窗口内跨越的独立 ret 体数量分布；only_sub 体的序言特征。"""
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
ck('R0a 697/391/1068', (len(sub),len(mainall),len(suball))==(697,391,1068),(len(sub),len(mainall),len(suball)))

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
SORT=sorted(set(t for _,t in CALLAT))
def idx_of(va):
    i=bisect.bisect_right(ADDRS,va)-1
    return i if i>=0 and ADDRS[i]<=va else None
BEND=[]  # 边界结束位置（ret/int3 之后）
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3': BEND.append(a+sz)
BEND.sort()
def span_v1(va):
    i=idx_of(va)
    if i is None: return None
    j=i
    while j<len(INS) and not (INS[j][2].startswith('ret') or INS[j][2]=='int3'): j+=1
    hi=INS[j][0]+INS[j][1] if j<len(INS) else HI
    k=bisect.bisect_left(BEND,va)-1
    lo=BEND[k] if k>=0 else LO
    return lo,hi
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def next_entry(c):
    i=bisect.bisect_right(SORT,c)
    return SORT[i] if i<len(SORT) else HI
def span_v2(va):
    h=host_of(va)
    if h is None: return None
    return h, min(next_entry(h),h+4096)
def pred_ok(h):
    o=P.r2o(h)
    if o is None or o==0: return False
    return RAW[o-1] in (0x90,0xC3,0xCC,0x00,0xFF) or h in set(SORT)
POK=set(x for x in SORT)
def span_v3(va):
    sp=span_v1(va)
    if sp is None: return None
    lo,hi=sp
    o=P.r2o(lo)
    ok = (lo in POK) or (o is not None and o>0 and RAW[o-1] in (0x90,0xC3,0xCC,0x00,0xFF))
    if ok: return lo,hi
    # 回退：向后再跨一个 ret 体
    j=idx_of(hi)
    if j is None: return lo,hi
    k=j
    while k<len(INS) and not (INS[k][2].startswith('ret') or INS[k][2]=='int3'): k+=1
    hi2=INS[k][0]+INS[k][1] if k<len(INS) else HI
    return lo,hi2

def classify_span(lo,hi):
    ma=[r for r in mainall if lo<=r[0]<hi]
    su=[r for r in suball if lo<=r[0]<hi]
    return ('both' if (ma and su) else ('only_sub' if su else 'none')),len(ma),len(su)

res={}
for nm,fn in (('V1_ret',span_v1),('V2_callat4096',span_v2),('V3_ret_guard',span_v3)):
    c=collections.Counter(); spans=[]
    for r in sub:
        sp=fn(r[0])
        if sp is None: c['nospan']+=1; continue
        k,nm_,ns=classify_span(*sp); c[k]+=1
        spans.append(sp[1]-sp[0])
    res[nm]=dict(c)
    print('   %-14s both=%3d only_sub=%3d none=%3d nospan=%d  span p50=%d max=%d'%(
        nm,c['both'],c['only_sub'],c['none'],c['nospan'],
        statistics.median(spans) if spans else 0, max(spans) if spans else 0))
    ck('R0b %s both<251（非 R200 的口径产物）'%nm, c['both']<251, c['both'])

# R200 窗口的跨函数污染：每个 CALLAT 窗口内包含几个独立 ret 体
pol=[]
for h in set(host_of(r[0]) for r in sub):
    if h is None: continue
    hi=min(next_entry(h),h+4096)
    # 数窗口内 ret/int3 结束点个数
    i0=bisect.bisect_left(BEND,h); i1=bisect.bisect_left(BEND,hi)
    pol.append(i1-i0)
ck('R0c 窗口内 ret 体数 p50>=2（跨函数污染成立）', statistics.median(pol)>=2,
   'p50=%s p90=%s max=%s'%(statistics.median(pol), sorted(pol)[int(len(pol)*0.9)], max(pol)))
print('   R200 窗口内 ret 体数: n=%d p50=%d mean=%.2f max=%d  ==1 的占比 %.1f%%'%(
    len(pol),statistics.median(pol),sum(pol)/len(pol),max(pol),
    100.0*sum(1 for x in pol if x==1)/len(pol)))

# only_sub 体的序言与是否含 call
pro=collections.Counter(); hascall=collections.Counter(); sizes=[]
for r in sub:
    sp=span_v1(r[0]); lo,hi=sp
    k,nm_,ns=classify_span(lo,hi)
    if k!='only_sub': continue
    i=idx_of(lo)
    if i is None: continue
    mn0=INS[i][2]
    pro[mn0]+=1
    body=[x for x in INS if lo<=x[0]<hi]
    hascall[any(x[2]=='call' for x in body)]+=1
    sizes.append(hi-lo)
print('   only_sub 体首指令 mnemonic Top:', pro.most_common(6))
print('   only_sub 体内是否含 call:', dict(hascall))
print('   only_sub 体长 p10/p50/p90:', sorted(sizes)[int(len(sizes)*.1)], statistics.median(sizes), sorted(sizes)[int(len(sizes)*.9)])
ck('R0d only_sub 体多数含 call（是真函数体非碎片）', hascall[True] > hascall[False], dict(hascall))

json.dump(dict(res=res,polish=dict(n=len(pol),p50=statistics.median(pol),max=max(pol)),
               pro=dict(pro),hascall={str(k):v for k,v in hascall.items()},
               sizes=dict(p10=sorted(sizes)[int(len(sizes)*.1)],p50=statistics.median(sizes),p90=sorted(sizes)[int(len(sizes)*.9)],max=max(sizes)),
               asserts=N,fails=fails),
          open('/home/t628/projects/ra2-campaign-forge/_r201/m4_robust.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
