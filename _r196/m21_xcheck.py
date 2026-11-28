#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第二十一刀：对三个子代理的**三条分歧**做主会话复算（规则 D 要求）。
D1 审计 #482 说「ss violation - no RTTI data!」这个 TD 不存在，真串是
   "Access violation - no RTTI data!" 且 0 个 BCD 指向它。主会话 m3-m7 却报 11 个占位 pTD、
   14 个 BCD 位置。必须用原始字节裁决。
D2 执行员 #483 报 1214 个 vtable 地址作为 4 对齐 dword 在 .text 出现 5908 次；
   主会话 m20 报 1663 次。必须裁决。
D3 审计 #482 报相邻 BCD 指针差「递减 1480 / 递增 181」，主会话 C1a 报「-24 有 973 / +24 有 0」。
   两者可能是不同谓词，必须同时给出并说明。
D4 审计 #482 的递归判别力：单点 c-1 后 895/1380 通过、c+1 后 175/2615 通过。复算。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c:fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def wv(sn):
    s=P.B[sn]; n=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%n,P.RAW,s['rawptr']),n
print('=== D1 占位 TD 的原始字节裁决 ===')
for va in range(0x7F9588,0x7F95D0,8):
    print('  %08X : %08X %08X  %r'%(va,P.dw(va),P.dw(va+4),P.RAW[P.r2o(va):P.r2o(va)+32]))
print('  --- 我 m7 报的 11 个占位 pTD 的原始字节 ---')
PH=[0x822640,0x8226B0,0x8241D8,0x824EC0,0x824F40,0x839438,0x842E90,0x842F10,0x848200,0x848FC8,0x8484D0]
for td in PH[:4]:
    print('  TD %08X : +0=%08X +4=%08X +8..=%r'%(td,P.dw(td),P.dw(td+4),P.RAW[P.r2o(td+8):P.r2o(td+8)+40]))
ck('D1a 0x7F9594 处的 dword 是 0x80EE30（审计说的 vftable）',P.dw(0x7F9594)==0x80EE30,hex(P.dw(0x7F9594) or 0))
s1=P.cstr(0x7F9590,60); s2=P.cstr(0x7F959C,60)
print('  0x7F9590 串 = %r'%s1); print('  0x7F959C 串 = %r'%s2)
ck('D1b 0x7F9590 起是 "Access violation - no RTTI data!"',(s1 or b'').startswith(b'Access violation'),s1)
ck('D1c 0x7F959C 起是 "ss violation..."（即我 cstr 从 +0xC 起读，差 4 字节）',(s2 or b'').startswith(b'ss violation'),s2)
# 重新枚举: 全部 CHD 的 BCD，其 pTD 的 +0 是否等于 0x7F9594
COL={}
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4])
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
n_ptr=0;n_td9594=0;samp=[]
for v,d in CHD.items():
    for b in d['bcds']:
        td=P.dw(b)
        if td==0x7F9590: n_ptr+=1
        if P.dw(td)==0x7F9594: n_td9594+=1; samp.append((b,td))
print('  D1 指向 0x7F9590 的 BCD 槽位 = %d ; pTD 的 +0 == 0x7F9594 的槽位 = %d'%(n_ptr,n_td9594))
print('  D1 样本前 6:',[(hex(a),hex(b2)) for a,b2 in samp[:6]])
ck('D1d 存在 14 个 BCD，其 pTD+0 是 0x7F9594（主会话读数）',n_td9594==14,n_td9594)
ck('D1e 审计说的「指向 0x7F9590 的 BCD = 0」也成立（两个不同锚点）',n_ptr==0,n_ptr)
print('=== D2 .text 内 vtable 地址出现次数裁决 ===')
TL=P.B['.text']; TLO=TL['lo']; THI=TL['hi_file']; TRP=TL['rawptr']; TRS=TL['rawsize']
VT=set()
for sn in ('.rdata','.data'):
    base,w,n=wv(sn)
    for i in range(n):
        if TLO<=w[i]<THI and P.dw(base+4*i-4) in COL: VT.add(base+4*i)
al4=0;al4d=collections.Counter();unal=0
for i in range(TRS//4):
    v=struct.unpack_from('<I',P.RAW,TRP+4*i)[0]
    if v in VT: al4+=1; al4d[v]+=1
for i in range(TRS-3):
    if i%4==0: continue
    v=struct.unpack_from('<I',P.RAW,TRP+i)[0]
    if v in VT: unal+=1
print('  D2 4 字节对齐命中 %d 次 / %d 个不同 ; 非对齐命中 %d 次 ; 合计 %d'%(al4,len(al4d),unal,al4+unal))
ck('D2a 对齐命中 = 1663（主会话 m20）',al4==1663,al4)
print('  D2 exec_b 的 5908 已由 m20 的 H2（任意字节偏移）复现为 5908 ⇒ 那是含非对齐的计数')
ck('D2b 非对齐命中数 = 5908-1663 = 4245',unal==4245,unal)
print('=== D3 相邻 BCD 指针差的两种谓词 ===')
dec=inc=eq=0;ex24=0;pos24=0;other=0
for v,d in CHD.items():
    L=d['bcds']
    for j in range(len(L)-1):
        df=L[j+1]-L[j]
        if L[j]>L[j+1]: dec+=1
        elif L[j]<L[j+1]: inc+=1
        else: eq+=1
        if df==-24: ex24+=1
        elif df==24: pos24+=1
        else: other+=1
tot=dec+inc+eq
print('  D3 相邻对 %d : 递减 %d / 递增 %d / 相等 %d ; 恰 -24 %d ; 恰 +24 %d ; 其它 %d'%(tot,dec,inc,eq,ex24,pos24,other))
ck('D3a 递减 %d 与审计 #482 的 1480 一致'%dec,dec==1480,dec)
ck('D3b 递增 %d 与审计 #482 的 181 一致'%inc,inc==181,inc)
ck('D3c 恰 -24 只有 %d 对（=58.6%%），故「恒 -24」这一说法必须作废'%ex24,ex24==973,ex24)
ck('D3d 恰 +24 的对数 = 0',pos24==0,pos24)
print('=== D4 递归判据的判别力 ===')
def parse_rec(ncb,n):
    kids={i:[] for i in range(n)};par={}
    for i in range(n):
        if ncb[i]<0 or i+ncb[i]>=n: return None
    for i in range(n):
        end=i+ncb[i];k=i+1
        while k<=end:
            par[k]=i;k=k+ncb[k]+1
            if k==0 or k>n: return None
        if k!=end+1: return None
    if not(len(par)==n-1 and 0 not in par): return None
    for c,p in par.items(): kids[p].append(c)
    return kids
r_ok=0
for v,d in CHD.items():
    if parse_rec([P.dw(b+4) for b in d['bcds']],d['n']): r_ok+=1
ck('D4a 真实 ncb 递归建树 954/954',r_ok==954,r_ok)
m1_ok=m1_tot=0;p1_ok=p1_tot=0
for v,d in CHD.items():
    ncb=[P.dw(b+4) for b in d['bcds']];n=d['n']
    for j in range(n):
        if ncb[j]==0: continue
        t=list(ncb);t[j]-=1;m1_tot+=1
        if parse_rec(t,n): m1_ok+=1
        t2=list(ncb);t2[j]+=1;p1_tot+=1
        if parse_rec(t2,n): p1_ok+=1
print('  D4 c-1 后仍建树成功 %d / %d ; c+1 后 %d / %d'%(m1_ok,m1_tot,p1_ok,p1_tot))
ck('D4b c-1 后通过率 < 100%（审计报 895/1380）',m1_ok<m1_tot,(m1_ok,m1_tot))
ck('D4c c+1 后通过率 < 100%（审计报 175/2615）',p1_ok<p1_tot,(p1_ok,p1_tot))
json.dump(dict(d1=dict(ptr9590=n_ptr,td9594=n_td9594),d2=dict(al4=al4,al4d=len(al4d),unal=unal),
  d3=dict(tot=tot,dec=dec,inc=inc,eq=eq,ex24=ex24,pos24=pos24,other=other),
  d4=dict(rec950=r_ok,m1=(m1_ok,m1_tot),p1=(p1_ok,p1_tot))),
  open('_r196/m21_xcheck.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
