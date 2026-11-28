# -*- coding: utf-8 -*-
"""R220 m30：0x879b30 89 块生成律二轮（累积/斜率口径）。"""
import sys,struct,json
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge')
import _r185.pe185 as P
R=P.RAW
IMA=list(struct.unpack_from('<89H',R,P.r2o(0x8758e4)))
vals=list(struct.unpack_from('<'+str(16*89)+'i',R,P.r2o(0x879b30)))
blk=[vals[i*16:(i+1)*16] for i in range(89)]
RULES={
 'A floor(i*s/4)+floor(s/8)': lambda s:[ (i*s)//4 + s//8 for i in range(8)],
 'B floor((i*s + s/2)/4)':    lambda s:[ (2*i*s + s)//8 for i in range(8)],
 'C floor(s/8)+round_half(i*s/4)': lambda s:[ s//8 + (2*i*s + 4)//8 for i in range(8)],
 'D floor(s*(2i+1)/8)':       lambda s:[ (s*(2*i+1))//8 for i in range(8)],
 'E ceil(s*(2i+1)/8)':        lambda s:[ -((-(s*(2*i+1)))//8) for i in range(8)],
 'F floor(s/8)+floor(i*s/4+0.5*?)': lambda s:[ s//8 + (i*s*2+ (0 if i%2==0 else s))//8 for i in range(8)],
}
out={}
for nm,f in RULES.items():
    hit=[k for k in range(89) if f(IMA[k])==blk[k][:8]]
    out[nm]=len(hit)
    print("%-32s %d/89"%(nm,len(hit)), "miss first:", [k for k in range(89) if k not in hit][:6])
# 组合：每块取最优 rule
best=[any(f(IMA[k])==blk[k][:8] for f in RULES.values()) for k in range(89)]
print("任一口径可生成块数:",sum(best),"/89")
print("不可生成块:",[k for k in range(89) if not best[k]][:10])
json.dump({'per_rule':out,'any':sum(best),'unmatched':[k for k in range(89) if not best[k]]},open('_r220/m30.json','w'),indent=1)
