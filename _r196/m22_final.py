#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第二十二刀（分歧终裁）：三条分歧的最终字节裁决。
m21 自错一条：S26 D1d 判据写成「pTD+0 == 0x7F9594」（即 P.dw(td)==0x7F9594），
   实测 pTD 指向的 TypeDescriptor 的 +0 是 vftable 指针（0x7F9594 是**它自己的 vftable**），
   所以「td 的 +0 == 0x7F9594」把全部 2615 槽位都算成命中 —— 判据必须是「td 本身是哪个地址」。

终裁（每条都带原始字节）：
D1 占位 TypeDescriptor 的**真身**：一个 **1 dword 宽**的 TypeDescriptor，即 td+0 = 0x7F9594
   （vftable），td+4 = 0，但**没有** .?A 名字（名字字段被 td+8 的 .?A 串占位，
   而 0x7F9594 指向的是 "Access violation - no RTTI data!" 的字节中段）。
   ⇒ 审计 #482 说「0 个 BCD 指向它」是**对的**（指向 0x7F9590 的 0 个）；
   主会话说的「11 个占位 pTD」指的是 td+0 == 0x7F9594 的 11 个**不同 td 地址**，
   这些 td 各自有正常的 .?A 名字 —— 两者的锚点差 4 字节，都可复算但描述不同东西。
D2 已终裁：1663（对齐）/ 5908（任意偏移）。
D3 已终裁：递减 1480 / 递增 181 / 恰 -24 只有 973（58.6%）⇒「恒 -24」作废。
D4 递归判别力：真 954/954；c-1 → 433/1380；c+1 → 91/1380（都比审计报的更弱）。
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
# D1 终裁
ph_td=set();ph_pos=0
for v,d in CHD.items():
    for b in d['bcds']:
        td=P.dw(b)
        if P.dw(td)==0x7F9594: ph_td.add(td); ph_pos+=1
print('   D1 占位判定「td+0 == 0x7F9594」：不同 td 地址 %d 个 / BCD 槽位 %d 个'%(len(ph_td),ph_pos))
ck('D1a 占位 td 地址 11 个 / 槽位 14 个（主会话 m3-m7 读数）',(len(ph_td),ph_pos)==(11,14),(len(ph_td),ph_pos))
ck('D1b 这 11 个 td 的 +8 都是正常 .?A 名字',all((P.cstr(t+8,200) or b'').startswith(b'.?A') for t in ph_td),len(ph_td))
ck('D1c 这 11 个 td 的 +0 都等于同一个值 0x7F9594',all(P.dw(t)==0x7F9594 for t in ph_td),len(ph_td))
# 0x7F9594 本身是什么：它是 .rdata 里的 dword，值是 0x7C8AB7（.text 内的函数）
v9594=P.dw(0x7F9594)
print('   D1 0x7F9594 处的 dword = %08X (%s)'%(v9594,P.where(v9594)))
ck('D1d 0x7F9594 是 .text 内的函数指针（= 一个 vftable 的槽）',P.where(v9594)=='.text',hex(v9594))
s16=P.cstr(0x7F9590,40); s12b=P.cstr(0x7F959C,40)
print('   0x7F9590 = %r ; 0x7F959C = %r'%(s16,s12b))
ck('D1e 审计 #482 的「Access violation」串不在 0x7F9590（那里是函数指针）',not (s16 or b'').startswith(b'Access'))
ck('D1f 「ss violation - no RTTI data!」在 0x7F959C',(s12b or b'').startswith(b'ss violation'),s12b)
n9590=sum(1 for v,d in CHD.items() for b in d['bcds'] if P.dw(b)==0x7F9590)
ck('D1g 指向「0x7F9590 这个 td 地址」的 BCD = 0（审计 #482 的数成立）',n9590==0,n9590)
# 「ss violation」串的全部出现位置
hits=[]
for sn in ('.rdata','.data'):
    s=P.B[sn]; buf=P.RAW[s['rawptr']:s['rawptr']+s['rawsize']]
    i=buf.find(b'ss violation - no RTTI data!')
    while i>=0:
        hits.append(s['lo']+i); i=buf.find(b'ss violation - no RTTI data!',i+1)
print('   D1h 该串出现位置:',[hex(x) for x in hits])
ck('D1h 该串在整镜像里只出现 1 次',len(hits)==1,len(hits))
json.dump(dict(d1=dict(ph_td=len(ph_td),ph_pos=ph_pos,td_vft=v9594,
  ptr9590=n9590,str_hits=[hex(x) for x in hits]),d2=dict(al4=1663,anyoff=5908),
  d3=dict(dec=1480,inc=181,ex24=973),d4=dict(real=954,m1=(433,1380),p1=(91,1380))),
  open('_r196/m22_final.json','w'),ensure_ascii=False,indent=1)
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
