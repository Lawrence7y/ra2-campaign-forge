# -*- coding: utf-8 -*-
"""R220 m25：0x879b30 的 89 块 (16 delta) 与 0x8758e4 的 89 项 IMA step 表逐块比对（三律）。"""
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
blocks=[vals[i*16:(i+1)*16] for i in range(89)]
print("IMA[:8]",IMA[:8]); print("block0",blocks[0][:8]); print("block1",blocks[1][:8]); print("block8",blocks[8][:8])
def score(fn):
    m=0; miss=[]
    for b in range(89):
        pred=fn(IMA[b])
        if pred==blocks[b][:8]: m+=1
        else: miss.append((b,IMA[b],blocks[b][:8],pred))
    return m,miss
tests={
 'L1 round(step*(2i+1)/8)': lambda s:[int(round(s*(2*i+1)/8.0)) for i in range(8)],
 'L2 floor(step*(2i+1)/8)': lambda s:[int(s*(2*i+1)//8) for i in range(8)],
 'L3 step>>3*(2i+1)':       lambda s:[(s>>3)*(2*i+1) for i in range(8)],
 'L4 round(step*(2i+1)/16)':lambda s:[int(round(s*(2*i+1)/16.0)) for i in range(8)],
 'L5 round(step*(i+0.5)/4)':lambda s:[int(round(s*(i+0.5)/4.0)) for i in range(8)],
}
for nm,fn in tests.items():
    m,miss=score(fn); print("%-28s match %d/89"%(nm,m))
    if m<89: print("      first miss:",miss[0])
m,miss=score(tests['L1 round(step*(2i+1)/8)'])
ck('L1 round(step*(2i+1)/8) 逐块 89/89', m==89, m)
# 结构律
asc=all(all(b[i]<b[i+1] for i in range(7)) for b in blocks)
neg=all(b[8+i]==-b[i] for b in blocks for i in range(8))
ck('L6 89 块每块前 8 严格递增', asc)
ck('L7 89 块每块后 8 == 前 8 的相反数', neg)
ck('L8 块数 89 == IMA 表项数 89', len(blocks)==len(IMA)==89)
ck('L9 表跨度 89*16*4 == 5696 B', 89*16*4==5696)
print("after 5696:",R[P.r2o(0x879b30)+5696:P.r2o(0x879b30)+5696+32].hex())
json.dump({'ima':IMA,'block0':blocks[0],'block1':blocks[1],'block8':blocks[8],
 'L1_match':m,'fails':fails},open('_r220/m25.json','w'),indent=1)
print('TOTAL FAILS:',len(fails),fails)
