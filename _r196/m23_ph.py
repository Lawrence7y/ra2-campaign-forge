#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第二十三刀（自错 S27 收口）：m3-m7 的「11 个占位 pTD」到底是什么。
m22 已证：全部 988 个 TypeDescriptor 的 +0 都等于 0x7F9594（= TypeDescriptor 类的 vftable），
所以 m3 的判据 `P.dw(td) == 0x7F9594` 对全体成立、零鉴别力（m7 V0 的 11 才是对的，
它用的是 `cstr(td+8) 不以 .?A 开头`）。
本刀给出这 11 个 td 的真实名字形态，判定它们是**模板类名**而不是「无 RTTI 占位」。
"""
import sys,struct,collections,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
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
nonstd=collections.Counter();pos=0
for v,d in CHD.items():
    for b in d['bcds']:
        td=P.dw(b); nm=P.cstr(td+8,220)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')):
            nonstd[td]+=1; pos+=1
print('=== 不以 .?A..@@ 结尾的 TypeDescriptor ===')
for td,c in nonstd.items():
    nm=P.cstr(td+8,220)
    print('  td=%08X 出现 %d 次  name=%r'%(td,c,nm))
print('  合计 %d 个 td / %d 个槽位'%(len(nonstd),pos))
# 它们的共同点
print('  +0 值:',{hex(P.dw(t)) for t in nonstd})
print('  +4 值:',{hex(P.dw(t+4)) for t in nonstd})
# 名字形态
kinds=collections.Counter()
for td in nonstd:
    nm=P.cstr(td+8,220)
    if b'?$' in nm: kinds['模板特化（含 ?$）']+=1
    elif nm.endswith(b'@@'): kinds['.?A..@@']+=1
    else: kinds['其它']+=1
print('  名字形态:',dict(kinds))
# 是否存在真正的「无 RTTI」串被引用
s=b'no RTTI data'
cnt=0
for sn in ('.rdata','.data'):
    x=P.B[sn]; cnt+=P.RAW[x['rawptr']:x['rawptr']+x['rawsize']].count(s)
print('  「no RTTI data」在 .rdata/.data 出现 %d 次'%cnt)
json.dump(dict(nonstd={hex(k):v for k,v in nonstd.items()},pos=pos,
  names={hex(k):(P.cstr(k+8,200) or b'').decode('latin1') for k in nonstd},
  kinds=dict(kinds),nortti=cnt),open('_r196/m23_ph.json','w'),ensure_ascii=False,indent=1)
