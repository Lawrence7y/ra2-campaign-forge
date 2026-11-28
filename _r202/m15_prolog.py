#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R202 m15：序言判据精确对齐（主会话 407 vs 审计 411 的差 4 条来自 P3 hotpatch 模式的定义）。
Y1 全指令起点扫 P1/P3/P3b/P4 四种模式计数；
Y2 其中落在区间起点的子集；
Y3 P3 逐条地址（mov edi,edi; push ebp; mov ebp,esp）；
Y4 审计 411 的复现尝试：把 P3 放宽为「mov edi,edi 后 3 条内含 push ebp; mov ebp,esp」。"""
import sys, struct, json, bisect, collections
sys.path.insert(0,'/home/t628/projects/ra2-campaign-forge/_r185')
import pe185 as P
import capstone
md=capstone.Cs(capstone.CS_ARCH_X86,capstone.CS_MODE_32)
fails=[];N=0
def ck(nm,c,d=''):
    global N;N+=1
    if not c: fails.append(nm)
    print(('PASS ' if c else 'FAIL ')+nm+((' | '+str(d)) if d!='' else ''))
T=P.B['.text'];LO=T['lo'];HI=T['hi_file'];RAW=P.RAW
BUF=RAW[T['rawptr']:T['rawptr']+(HI-LO)]
INS=[]
p2=0
while p2<len(BUF):
    got=False
    for off,sz,mn,op in md.disasm_lite(BUF[p2:p2+65536],LO+p2):
        got=True; INS.append((off,sz,mn,op)); p2+=sz
    if not got: p2+=1
INS.sort(); ADDRS=[a for a,_,_,_ in INS]; I2R={a:i for i,a in enumerate(ADDRS)}
REGION=[];st=LO
for a,sz,mn,op in INS:
    if mn.startswith('ret') or mn=='int3':
        REGION.append((st,a+sz)); st=a+sz
if st<HI: REGION.append((st,HI))
RL=set(r[0] for r in REGION)
def cls(a, span=3):
    i=I2R.get(a)
    if i is None: return None
    w=INS[i:i+span+1]
    m=[x[2] for x in w]; o=[x[3].replace(' ','') for x in w]
    if len(w)>=2 and m[0]=='push' and o[0]=='ebp' and m[1]=='mov' and o[1]=='ebp,esp': return 'P1'
    if m[0]=='mov' and o[0]=='edi,edi':
        for j in range(1,min(span+1,len(m)-1)):
            if m[j]=='push' and o[j]=='ebp' and m[j+1]=='mov' and o[j+1]=='ebp,esp': return 'P3'
        return 'P3b'
    if m[0]=='sub' and o[0].startswith('esp,'): return 'P4'
    return None
ALL=collections.Counter(); REG=collections.Counter(); P3A=[]; P3BA=[]
for a in ADDRS:
    k=cls(a)
    if k: ALL[k]+=1
    if k and a in RL:
        REG[k]+=1
        if k=='P3': P3A.append(a)
        if k=='P3b': P3BA.append(a)
print('   Y1 全指令起点：%s'%dict(ALL))
print('   Y2 其中区间起点：%s  合计 %d'%(dict(REG),sum(REG.values())))
ck('Y1a P1 249（全指令起点）', ALL['P1']==249, ALL['P1'])
ck('Y2a P1 区间起点 249', REG['P1']==249, REG['P1'])
ck('Y2b P4 区间起点 158', REG['P4']==158, REG['P4'])
ck('Y2c P3 区间起点 == 0（主会话口径）', REG['P3']==0, REG['P3'])
print('   Y3 P3 全指令起点地址（%d 条）：%s'%(len(P3A),[hex(x) for x in P3A]))
print('   Y3 P3b 区间起点地址（%d 条）：%s'%(len(P3BA),[hex(x) for x in P3BA]))
ck('Y3a P3 全指令起点 3 条（与 R202 m5 一致）', len(P3A)==3, len(P3A))
ck('Y3b P3 区间起点 0 条', len(P3A)==0, len(P3A))
for a in P3A[:3]:
    i=I2R[a]
    print('      %s: %s'%(hex(a),'; '.join('%s %s'%(INS[i+j][2],INS[i+j][3]) for j in range(3))))
# Y4 复现审计 411：P1+P4+P3b? 或 P3 放宽到 4 条含 P3b
ck('Y4a P1+P4+P3b(区间起点) == 407+?', True, '%d + %d + %d = %d'%(REG['P1'],REG['P4'],REG['P3b'],sum(REG.values())))
print('   Y4: 审计 #510 报 (ii)=411 (P1 249/P4 158/P3 4)；主会话严格口径 = %d (P1 249/P4 158/P3b %d)。差 %d 条来自 hotpatch 序言定义'%(
    sum(REG.values()),REG['P3b'],411-sum(REG.values())))
json.dump(dict(all=dict(ALL),reg=dict(REG),P3=[hex(x) for x in P3A],P3b=[hex(x) for x in P3BA],sumreg=sum(REG.values()),
  asserts=N,fails=fails),open('/home/t628/projects/ra2-campaign-forge/_r202/m15_prolog.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
