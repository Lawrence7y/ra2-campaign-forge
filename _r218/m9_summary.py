# -*- coding: utf-8 -*-
"""R218 m9：把 m8 结果按「父类同槽有效性」重整：只统计父类表内存在的槽（k < len(parent)），
把 oob 单列，避免 103 个 oob 掩盖真实覆盖。
同时给出「增量槽」= 超出父类槽数的部分（真正新增）。
"""
import json,subprocess,sys
# 直接复用 m8 的算式重新算，输出紧凑表
import struct,collections
sys.path.insert(0,'_r185'); import pe185 as P
exec(open('_r218/m8_parent_final.py').read().split("TGT=")[0].replace("print(","(lambda *a,**k:None)("))
TGT=[0x7f5c70,0x7eb058,0x7e22a4,0x7e8c94,0x7e3ebc,0x7f4960]
PAR={0x7f5c70:0x7e8c94,0x7eb058:0x7e8c94,0x7e22a4:0x7e8c94,0x7e8c94:0x7f4960,0x7e3ebc:0x7f4960,0x7f4960:0x7f0508}
print('%-10s %-22s %5s %5s %5s %5s %5s %5s'%('vt','name','n','par_n','cov','diff','oob','new'))
tot=collections.Counter()
for vt in TGT:
    S=slots(vt); pv=PAR[vt]; P2=slots(pv)
    cov=diff=oob=0
    for k in range(256,len(S)):
        if k>=len(P2): oob+=1; continue
        if S[k]==P2[k]: cov+=1
        else: diff+=1
    new=max(0,len(S)-len(P2))
    print('%08x %-22s %5d %5d %5d %5d %5d %5d'%(vt,COL[VT[vt]]['name'],len(S),len(P2),cov,diff,oob,new))
    tot['cov']+=cov; tot['diff']+=diff; tot['oob']+=oob; tot['new']+=new
print('合计 cov=%d diff=%d oob=%d new=%d  (cov+diff+oob=%d 应 464)'%(tot['cov'],tot['diff'],tot['oob'],tot['new'],tot['cov']+tot['diff']+tot['oob']))
print('判定：父类范围内覆盖率 = %d/%d = %.2f%%'%(tot['cov'],tot['cov']+tot['diff'],100.0*tot['cov']/(tot['cov']+tot['diff'])))
print('超父类尾部新增槽 = %d（这些槽无父类可比，必为本类新增）'%tot['new'])
print('注：oob(%d) 与 new(%d) 应相等 —— 校验 %s'%(tot['oob'],tot['new'],'PASS' if tot['oob']==tot['new'] else 'FAIL'))
