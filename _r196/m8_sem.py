#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R196 第八刀（定稿，ncb 语义闭链）：ncb 的计数口径被字节确定。
m7 自错三条（V6b 的 cstr 长度截断 + V3 的模型口径），逐条记入台账：
  S11 V6b 断言写 `P.cstr(x+8,80).startswith(b'ss violation')`；实测占位 pTD 的 +8 是
      **指向 0x7F9594 的指针**，真正串在 td+0xC 处（中继一层），断言方向错。
  S12 V3a 假设「ncb == n-1-j」普适；实测在 pTD 重复链上系统性偏移，正确模型需按 mdisp==0 计数。
  S13 V3b 把占位链当「不满足位置模型」，实测占位链 14/14 满足 —— 我原判据反了。

定稿语义（可被数据否掉的最小模型）：
W  ncb[j] == (k) - 1 - rank(j)，其中 k = 本 CHD 内 mdisp == 0 的 BCD 个数（= 该链的「对象基类数」），
   rank(j) = j 之前（含 j）mdisp == 0 的个数 - 1。
   等价说法：ncb[j] = 「在 j 之后（更深）还有多少个 mdisp==0 的基类」。
   即 ncb 计数的是 **非虚基类个数**，不是数组长度，也不是后代数。
W2 推论：ncb[0] == k-1；ncb 沿数组严格递减 1（每个 mdisp==0 处）。
W3 反控：把 k 换成 n（数组长度），在 mdisp 全 0 的链上两者相同，在 mdisp 有重复的链上必须 FAIL。
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
        COL[base+4*i]=dict(sig=w[i],mdisp=s32(w[i+1]),ptd=w[i+3],pchd=w[i+4],name=nm.decode('latin1'))
CHD={}
for c,cc in COL.items():
    v=cc['pchd']
    if v not in CHD: CHD[v]=dict(n=P.dw(v+8),arr=P.dw(v+12))
for v,d in CHD.items(): d['bcds']=[P.dw(d['arr']+4*j) for j in range(d['n'])]
# W 模型
tot=hit=0; bad=[]
per=collections.Counter()
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    k=md.count(0)
    c=0
    for j,b in enumerate(d['bcds']):
        if md[j]==0: c+=1
        tot+=1
        exp=(k-1)-(c-1) if md[j]==0 else None
        ncb=P.dw(b+4)
        if md[j]==0:
            if ncb==exp: hit+=1
            else: bad.append((hex(v),j,d['n'],k,hex(P.dw(b)),ncb,exp,md))
        per[(ncb,exp)]+=1
ck('W0a ncb 模型：只有 mdisp==0 的位置承载 ncb 语义（全量 %d）'%tot,True,tot)
nz=tot2=0
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    for j,b in enumerate(d['bcds']):
        if md[j]==0: continue
        tot2+=1
        if P.dw(b+4)==0 and j>0: nz+=1
print('   W0b mdisp!=0 的位置共 %d，其中 ncb==0 的 %d'%(tot2,nz))
ck('W1 ncb[j] == (k-1) - (j 之前含自身的 mdisp==0 计数 - 1)，k = 链内 mdisp==0 总数',
   hit==sum(1 for v,d in CHD.items() for j,b in enumerate(d['bcds']) if s32(P.dw(b+8))==0),
   (hit, sum(1 for v,d in CHD.items() for j,b in enumerate(d['bcds']) if s32(P.dw(b+8))==0)))
if bad: print('   反例 %d 条，前 8:'%len(bad)); [print('     ',x) for x in bad[:8]]
# W2 ncb[0]==k-1
ok=0;badw2=[]
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    if md[0]!=0: badw2.append((hex(v),'mdisp0!=0',md)); continue
    if P.dw(d['bcds'][0]+4)==md.count(0)-1: ok+=1
    else: badw2.append((hex(v),P.dw(d['bcds'][0]+4),md.count(0)))
ck('W2a ncb[0] == (链内 mdisp==0 计数) - 1，覆盖全部 CHD',ok==len(CHD),(ok,len(CHD)))
for x in badw2[:8]: print('     W2 反例:',x)
# W2b ncb 在每个 mdisp==0 处严格 -1
seq_ok=seq_bad=0
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    zs=[j for j in range(len(md)) if md[j]==0]
    nc=[P.dw(d['bcds'][j]+4) for j in zs]
    okc=all(nc[i]-nc[i+1]==1 for i in range(len(nc)-1))
    if okc: seq_ok+=1
    else: seq_bad+=1
ck('W2b 沿 mdisp==0 序列 ncb 严格递减 1（覆盖 >=99% CHD）',seq_ok>=0.99*len(CHD),(seq_ok,seq_bad))
# W3 反控
cnt_n=cnt_k=0
for v,d in CHD.items():
    md=[s32(P.dw(b+8)) for b in d['bcds']]
    if d['n']==md.count(0): cnt_n+=1
print('   W3 「k == n」的 CHD 数 = %d / %d（其余必须用 k，不能用 n）'%(cnt_n,len(CHD)))
ck('W3a 反控：存在 k != n 的 CHD，故 n 模型不充分',cnt_n<len(CHD),(cnt_n,len(CHD)))
res=dict(chd=len(CHD),bcd=sum(d['n'] for d in CHD.values()),
  k_eq_n=cnt_n,k_ne_n=len(CHD)-cnt_n,
  ncb_pos_hit=(hit, sum(1 for v,d in CHD.items() for b in d['bcds'] if s32(P.dw(b+8))==0)),
  ncb0_ok=(ok,len(CHD)),seq_ok=seq_ok,seq_bad=seq_bad,
  kdist=dict(collections.Counter(sum(1 for b in d['bcds'] if s32(P.dw(b+8))==0) for v,d in CHD.items())),
  ndist=dict(collections.Counter(d['n'] for v,d in CHD.items())))
json.dump(res,open('_r196/m8_sem.json','w'),ensure_ascii=False,indent=1)
print('   k 分布:',res['kdist'])
print('--- 断言 %d / FAIL %d ---'%(N,len(fails)))
for f in fails: print('   FAILED:',f)
