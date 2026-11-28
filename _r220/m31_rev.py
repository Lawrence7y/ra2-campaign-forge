# -*- coding: utf-8 -*-
"""R220 m31：逐块反解 s（不限 IMA），判定块 k 是否对应某个固定 s 序列。"""
import sys,struct,json
from collections import Counter
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
IMA=list(struct.unpack_from('<89H',R,P.r2o(0x8758e4)))
vals=list(struct.unpack_from('<'+str(16*89)+'i',R,P.r2o(0x879b30)))
blk=[vals[i*16:(i+1)*16] for i in range(89)]
# 对每块，用 s 使 floor(s*(2i+1)/8) == asc 尽可能匹配，给出最小二乘一致度
def fits(s,asc):
    return sum(1 for i in range(8) if (s*(2*i+1))//8==asc[i])
res=[]
for k in range(89):
    asc=blk[k][:8]
    # 解析上界 s <= asc[0]*8 ; s >= asc[7]*8/15
    lo=max(0,(asc[7]*8)//15-2); hi=(asc[0]*8)+8
    cands=[(fits(s,asc),s) for s in range(lo,hi+1)]
    b=max(cands)
    res.append((k,IMA[k],b[0],b[1],asc))
full=sum(1 for r in res if r[2]==8)
print("8/8 完全拟合块数:",full,"/89")
print("k, IMA[k], fit, s*, asc:")
for r in res[:12]: print("  ",r)
print("...")
for r in res[-6:]: print("  ",r)
# s* 与 IMA 的关系
rel=Counter()
for k,ima,fit,s,asc in res:
    if fit==8: rel[s-ima]+=1
print("s* - IMA[k] 分布:",rel.most_common(8))
# 用 s* 递推：s* 是否 == IMA[k] 或 相邻 IMA 项
print("s* 在 IMA 表内的比例:",sum(1 for r in res if r[3] in set(IMA)),"/89")
json.dump({'full':full,'res':[[r[0],r[1],r[2],r[3],r[4]] for r in res]},open('_r220/m31.json','w'),indent=1)
