#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第十七刀：ncb 语义的**字节锚点表**（供 FACT_INDEX 与后续轮次直接复算）。
输出三段可直接照抄复算的锚点：
 W1 AbstractClass（0x7E1F50）完整链：COL / CHD / BaseClassArray 8 个元素 / 每元素 6 个 dword 原始值。
 W2 最深链（n=18 的 CHD 0x7FB4B0）完整解析：ncb 数组、子树区间、直接子结点、深度。
 W3 一个「非 trifling」链（有分枝点）：给出完整树形与 ncb 对应。
 W4 把上述三段的全部数字打成一份 sha256 清单，供下一轮重钉校验。
"""
import sys,struct,hashlib,json,collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
out=[]
def W(s=''):
    out.append(s); print(s)
def dumpchain(chd,title):
    n=P.dw(chd+8); arr=P.dw(chd+12)
    W('== %s =='%title)
    W('CHD %08X : +0=%08X +4=%08X n=%d arr=%08X'%(chd,P.dw(chd),P.dw(chd+4),n,arr))
    for j in range(n):
        b=P.dw(arr+4*j)
        td=P.dw(b)
        nm=P.cstr(td+8,120)
        nm=nm.decode('latin1') if nm else '?'
        W('  [%2d] BCD %08X : pTD=%08X ncb=%2d d=%4d +12=%2d +16=%2d attrs=%d  %s'%(
          j,b,td,P.dw(b+4),s32(P.dw(b+8)),s32(P.dw(b+12)),s32(P.dw(b+16)),P.dw(b+20),nm))
    ncb=[P.dw(P.dw(arr+4*j)+4) for j in range(n)]
    W('  ncb 数组 = %s'%ncb)
    # 树
    kids={i:[] for i in range(n)};par={}
    for i in range(n):
        end=i+ncb[i];k=i+1
        while k<=end:
            par[k]=i;k=k+ncb[k]+1
    for c,p in par.items(): kids[p].append(c)
    for i in range(n):
        W('  node %2d ncb=%2d subtree=[%2d..%2d] kids=%s'%(i,ncb[i],i,i+ncb[i],kids[i]))
    W()
dumpchain(0x7FB108,'AbstractClass 链（0x7E1F50 槽 0）')
dumpchain(0x7FB4B0,'最深链 n=18')
# 找一个有分枝点的链
COL={}
def wv(sn):
    s=P.B[sn]; nn=s['rawsize']//4
    return s['lo'],struct.unpack_from('<%dI'%nn,P.RAW,s['rawptr']),nn
for sn in ('.rdata','.data'):
    base,w,nn=wv(sn)
    for i in range(nn-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,200)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4])
br=None
for c,cc in sorted(COL.items()):
    v=cc['pchd']
    if P.dw(v+8)>=8:
        n=P.dw(v+8);arr=P.dw(v+12)
        ncb=[P.dw(P.dw(arr+4*j)+4) for j in range(n)]
        kids={i:[] for i in range(n)};par={}
        for i in range(n):
            end=i+ncb[i];k=i+1
            while k<=end:
                par[k]=i;k=k+ncb[k]+1
        for cc2,p in par.items(): kids[p].append(cc2)
        if sum(1 for i in range(n) if len(kids[i])>=2)>=2: br=v;break
dumpchain(br,'有分枝点的链 n=%d'%P.dw(br+8))
h=hashlib.sha256('\n'.join(out).encode()).hexdigest()
W('== 锚点清单 sha256 ==')
W('anchor_text_sha256 = %s'%h)
W('anchor_bytes = %d'%len('\n'.join(out).encode()))
json.dump(dict(sha256=h,bytes=len('\n'.join(out).encode()),
  chains=['0x7FB108','0x7FB4B0',hex(br)]),open('_r196/m17_anchor.json','w'),indent=1)
open('_r196/m17_anchor.txt','w').write('\n'.join(out)+'\n')
