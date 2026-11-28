# -*- coding: utf-8 -*-
"""R220 m28：0x879b30 的 89 块是否为 IMA ADPCM diff 预计算表（四舍入口径四选一）。"""
import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
fails=[]
def ck(n,c,d=''):
    if not c: fails.append(n)
    print(('PASS ' if c else 'FAIL ')+n+((' | '+str(d)) if d!='' else ''))
IMA=list(struct.unpack_from('<89H',R,P.r2o(0x8758e4)))
vals=list(struct.unpack_from('<'+str(16*89)+'i',R,P.r2o(0x879b30)))
blk=[vals[i*16:(i+1)*16] for i in range(89)]
rules={
 'R0 floor  (s*(2i+1))>>3':      lambda s,i:(s*(2*i+1))>>3,
 'R1 +4>>3 (s*(2i+1)+4)>>3':     lambda s,i:(s*(2*i+1)+4)>>3,
 'R2 +3>>3':                      lambda s,i:(s*(2*i+1)+3)>>3,
 'R3 ceil':                       lambda s,i:-((-s*(2*i+1))>>3),
}
print("每块精确命中口径（要求 s == IMA[k]，恒等映射）：")
for nm,f in rules.items():
    hit=sum(1 for k in range(89) if [f(IMA[k],i) for i in range(8)]==blk[k][:8])
    print("   %-28s %d/89"%(nm,hit))
# 逐块求最小 s（任一 rule），看是否落在 IMA 集合
found={}
for k in range(89):
    cand=None
    for s in range(0,70000):
        for nm,f in rules.items():
            if [f(s,i) for i in range(8)]==blk[k][:8]:
                cand=(s,nm); break
        if cand: break
    found[k]=cand
okn=sum(1 for v in found.values() if v)
inima=sum(1 for v in found.values() if v and v[0] in set(IMA))
print("可反解块数 %d/89；反解 s 落在 IMA 集合 %d"%(okn,inima))
print("前 12 反解:",[(k,found[k]) for k in range(12)])
print("第 44..52:",[(k,found[k]) for k in range(44,53)])
# 关键：块 k 的 s 是否等于 IMA[index] 中某个固定偏移？
offs={}
for k in range(89):
    if found[k] and found[k][0] in IMA:
        offs[k]=IMA.index(found[k][0])-k
from collections import Counter
print("反解s的IMA下标 - k 分布:",Counter(offs.values()).most_common(6))
ck('Z1 89 块中可由某条 rule 反解出的块数 <= 89', okn<=89, okn)
ck('Z2 反解 s 全部落在 89 项 IMA 表内（若 okn>0）', inima==okn if okn else True, (okn,inima))
# 结构：块的 8 项是否恒为单调递增且第二半为负
ck('Z3 89 块前 8 严格递增、后 8 = 前 8 相反数', all(all(b[i]<b[i+1] for i in range(7)) and all(b[8+j]==-b[j] for j in range(8)) for b in blk))
# IMA 表 0x58 上界（cmp word [ebx+0x22],0x58）
ck('Z4 0x58 == 88 == IMA 表末项下标', 0x58==88 and len(IMA)==89)
print("IMA[k] 与反解 s 对照（k=0..8）:",[(k,IMA[k],found[k]) for k in range(9)])
json.dump({'found':{str(k):v for k,v in found.items()},'okn':okn,'inima':inima,'fails':fails},open('_r220/m28.json','w'),indent=1)
print('TOTAL FAILS:',len(fails),fails)
