# -*- coding: utf-8 -*-
"""R208 m1：追查 0x7f9594 语义（TD+0 恒等值）。只读 .rdata/.data 结构 + 极小范围 .text 字节核验。
正反控：
  +  TD 数、TD+0 取值数、TD+4 取值数
  +  0x7f9594 所在 COL（vftable[-1]）全字段
  +  该 COL 的 HEAD（+0/+4/+8/+12）与 BCA 内容
  +  vftable 槽数与每槽落点段
  -  反控：随机 .rdata dword 的「被 .data 引用次数」分布
"""
import sys, struct, collections, json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
def s32(v): return struct.unpack('<i',struct.pack('<I',v))[0]
def s8(v): return struct.unpack('b',struct.pack('B',v))[0]

# --- 1. COL 全表 ---
COL={}
for sn in ('.rdata','.data'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i in range(n-4):
        if w[i] not in (0,1,2) or w[i+2]!=0: continue
        if P.where(w[i+3])!='.data' or P.where(w[i+4])!='.rdata': continue
        nm=P.cstr(w[i+3]+8,400)
        if not (nm and nm.startswith(b'.?A') and nm.endswith(b'@@')): continue
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),pTD=w[i+3],pCHD=w[i+4],name=nm.decode('latin1'))
print('COL total', len(COL))

# --- 2. TD 集合（BCD 引用 + COL 引用）---
G=collections.defaultdict(list)
for c,v in COL.items(): G[v['pCHD']].append(c)
CHD=sorted(G)
NB={a:P.dw(a+8) for a in CHD}
pBCA={a:P.dw(a+12) for a in CHD}
ATTR={a:P.dw(a+4) for a in CHD}
BCA={a:[P.dw(pBCA[a]+4*j) for j in range(NB[a])] for a in CHD}
own_td={a:COL[a+16]['pTD'] for a in CHD}
td2c={v:k for k,v in own_td.items()}
phys=sorted({x for a in CHD for x in BCA[a]})
TD=set(own_td.values())|{P.dw(b) for b in phys}
print('HEAD',len(CHD),'physBCD',len(phys),'TD',len(TD))

# --- 3. TD 头两字段分布 ---
c0=collections.Counter(P.dw(t) for t in TD)
c4=collections.Counter(P.dw(t+4) for t in TD)
print('TD+0 取值分布', [(hex(k),v) for k,v in c0.most_common(6)])
print('TD+4 取值分布', [(hex(k),v) for k,v in c4.most_common(6)])

# --- 4. 0x7f9594 处的 COL 与 HEAD ---
V=0x7f9594; COLVA=V-4
print('=== V=0x%x, COLVA=0x%x 在 COL 表中? %s' % (V,COLVA,COLVA in COL))
if COLVA in COL:
    d=COL[COLVA]; print(' COL 字段', {k:(hex(v) if isinstance(v,int) else v) for k,v in d.items()})
    H=d['pCHD']
    print(' HEAD 0x%x : +0=0x%x +4(attrs)=0x%x +8(NB)=%d +12(pBCA)=0x%x' %
          (H,P.dw(H),ATTR[H],NB[H],pBCA[H]))
    print(' HEAD 内嵌 COL (+16) =', COL.get(H+16))
    print(' 该类所有 COL:', [(hex(c),COL[c]['mdisp'],COL[c]['name']) for c in G[H]])
    print(' BCA 项:', [(hex(b),hex(P.dw(b)),P.dw(b+4),s32(P.dw(b+8)),s32(P.dw(b+12)),s32(P.dw(b+16)),P.dw(b+20)) for b in BCA[H]])
    print(' BCA 项 pTD 名:', [P.cstr(P.dw(b)+8,200) for b in BCA[H]])

# --- 5. vftable 槽数（严格 .text 连续）---
def slots(v):
    out=[]; a=v
    while P.where(a)=='.text':
        out.append(P.dw(a)); a+=4
        if len(out)>4000: break
    return out
V2=slots(V)
print('vftable@0x%x 槽数=%d' % (V,len(V2)), [hex(x) for x in V2])

# --- 6. 0x7f9594 的引用者（dword 等于它的位置）---
refs=[]
for sn in ('.rdata','.data','.text'):
    s=P.B[sn]; n=s['rawsize']//4; base=s['lo']
    w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
    for i,x in enumerate(w):
        if x==V: refs.append(base+4*i)
rc=collections.Counter(P.where(a) for a in refs)
print('refs to V:',len(refs),rc)
dataRefs=[a for a in refs if P.where(a)=='.data']
print('其中 .data 引用者是否恰为 TD 头(+0)？', all(a in TD for a in dataRefs), 'TD 数',len(TD),'引用数',len(dataRefs))
textRefs=[a for a in refs if P.where(a)=='.text']
print('.text 内 imm32 直接引用:', [hex(a) for a in textRefs])

# --- 7. 反控：随机 .rdata dword 的 .data 引用计数分布 ---
import random
random.seed(208)
cnt=[]
for _ in range(200):
    a=0x7e1000+4*random.randrange((0x812000-0x7e1000)//4)
    cnt.append(sum(1 for x in dataRefs if False))  # placeholder
# 真正反控：统计 .data 里所有 dword 值在 .rdata 范围内的落点分布
s=P.B['.data']; n=s['rawsize']//4
w=struct.unpack_from('<%dI'%n,P.RAW,s['rawptr'])
hit=collections.Counter(x for x in w if 0x7e1000<=x<0x812000)
print('反控：.data 中指向 .rdata 的 dword 共 %d 个，指向不同目标 %d 个；目标被引用次数 top6 %s' %
      (sum(hit.values()),len(hit),[(hex(k),v) for k,v in hit.most_common(6)]))
print('V 的引用次数 %d 在全部 .rdata 目标中的排名：' % len(dataRefs),
      sorted(hit.values(),reverse=True).index(len(dataRefs))+1 if len(dataRefs) in hit.values() else 'n/a')
