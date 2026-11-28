# -*- coding: utf-8 -*-
"""R220 m26：定 0x879b30 89 块与 IMA step 表的确切关系 + 0x87b170 衔接 + 段界口径。"""
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
# A) 逐块求「哪个 IMA 项 + 哪个公式」能精确生成
forms={
 'round(s*(2i+1)/8)': lambda s:[int(round(s*(2*i+1)/8.0)) for i in range(8)],
 'floor(s*(2i+1)/8)': lambda s:[(s*(2*i+1))//8 for i in range(8)],
 'ceil(s*(2i+1)/8)':  lambda s:[-((-s*(2*i+1))//8) for i in range(8)],
 'floor(s*(2i+1)/16)*?': lambda s:[(s*(2*i+1))//16 for i in range(8)],
}
res={}
for nm,f in forms.items():
    ident=sum(1 for k in range(89) if f(IMA[k])==blk[k][:8])
    res[nm]=ident
print("恒等映射(块k <- IMA[k])精确命中:",res)
# B) 每块找最小 |s| 使某公式成立
best={}
for nm,f in forms.items():
    m=0
    for k in range(89):
        if any(f(s)==blk[k][:8] for s in IMA): m+=1
    best[nm]=m
print("块可由任一 IMA 项生成(不要求恒等):",best)
# C) 用块值反解步长：s = 8*blk[7]/15 附近搜索
inv=[]
for k in range(89):
    b=blk[k][:8]
    cand=[s for s in range(0,32768) if [(s*(2*i+1))//8 for i in range(8)]==b]
    inv.append(cand[0] if cand else None)
print("反解步长(floor 公式) 前 12:",inv[:12])
print("反解步长 == IMA 项数:",sum(1 for x in inv if x in set(IMA)),"非 None:",sum(1 for x in inv if x))
ck('B1 89 块跨度 == 89*64 == 5696 B', 89*16*4==5696)
ck('B2 0x879b30 + 5696 == 0x87b170（与第二份 162 记录表零间隙衔接）', 0x879b30+5696==0x87b170)
ck('B3 0x8758e4 + 178 == 0x875996（IMA 表 89*2 B 紧随其后不重叠）', 0x8758e4+178==0x875996)
ck('B4 块表 89 块每块 [升序8 + 相反数8]', all(all(b[i]<b[i+1] for i in range(7)) and all(b[8+j]==-b[j] for j in range(8)) for b in blk))
# D) 段界口径
T=P.B['.text']; print("text vsize=%#x rawsize=%#x lo=%#x hi_virt=%#x hi_file=%#x"%(T['vsize'],T['rawsize'],T['lo'],T['hi_virt'],T['hi_file']))
print("尾部填充 [%#x,%#x) 共 %d B 全 0x00 ="%(T['hi_virt'],T['hi_file'],T['hi_file']-T['hi_virt']),
      all(x==0 for x in R[T['rawptr']+T['vsize']:T['rawptr']+T['rawsize']]))
json.dump({'ident':res,'any_ima':best,'inv_first12':inv[:12],'fails':fails},open('_r220/m26.json','w'),indent=1)
print('TOTAL FAILS:',len(fails),fails)
