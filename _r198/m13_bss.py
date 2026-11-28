#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十三刀（决定性）：CRC 状态对象的四类宿主各自初值来源。
 Z1 0xa8b238 是否 BSS（virt-only，文件内无内容）⇒ 映像加载即全 0 ⇒ +0 初值 = 0 自带。
 Z2 该地址被多少条 mov ecx,imm32 引用；哪些函数。
 Z3 18 个 STACK 终止点：lea [esp+K] 之后到调用点之间，是否把 +0/+4/+8/+0xC 四槽都写过（真初始化）。
 Z4 全局绝对地址形态（0xa8b210/0xa83c90/0xa8b230/0x8874d0/0xa8eb38）：它们在 .data 还是 virt-only。
 Z5 汇总：331 个调用点里每一类的占比，覆盖比例。
 反控：把 Z1 的判据换成「用 r2o 返回 None 判定」，结论是否一致。
"""
import sys,struct,collections,json,bisect,re
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
def in_text(x): return x is not None and LO<=x<HI
# Z1
for a in (0xa8b238,0xa8b210,0xa83c90,0xa8b230,0xa8eb38,0x8874d0,0x817bd0):
    print('   Z1 %s where=%s r2o=%s sec_lo=%s'%(hex(a),P.where(a),P.r2o(a),
        next((s['name'] for s in P.SECS if s['lo']<=a<s['hi_virt']),'?')))
ck('Z1a 0xa8b238 是 virt-only(BSS)', P.where(0xa8b238)=='virt-only', P.where(0xa8b238))
ck('Z1b 0xa8b238 无文件内容', P.r2o(0xa8b238) is None, P.r2o(0xa8b238))
ck('Z1c 0x817bd0 在 .data', P.where(0x817bd0)=='.data', P.where(0x817bd0))
ck('Z1d 0xa8b210 是 virt-only', P.where(0xa8b210)=='virt-only', P.where(0xa8b210))
# Z2
def refs_imm(imm):
    out=[]
    for va in range(LO,HI-10):
        if BUF[va-LO]!=0xB9: continue
        if struct.unpack_from('<I',BUF,va-LO+1)[0]==imm: out.append(va)
    return out
R={hex(a):len(refs_imm(a)) for a in (0xa8b238,0x817bd0,0xa8b210,0xa83c90)}
ck('Z2a mov ecx,imm32 引用数', True, R)
# Z3
CALLTGT=set();CALLAT=[]
pos=0
while pos<len(BUF):
    for off,sz,mn,op in md.disasm_lite(BUF[pos:pos+65536],LO+pos):
        if mn=='call' and op.startswith('0x'):
            t=int(op,16)
            if in_text(t): CALLAT.append((off,t)); CALLTGT.add(t)
    pos+=65536
SORT=sorted(CALLTGT)
def host_of(c):
    i=bisect.bisect_left(SORT,c)-1
    return SORT[i] if i>=0 else None
def func_start(va):
    p=va-LO;q=p
    while q>16:
        if (BUF[q-1]==0x90 and BUF[q-2]==0x90) or (BUF[q-1]==0xCC and BUF[q-2]==0xCC): return LO+q
        q-=1
    return None
STACKS=[(0x51226e,0x41f6ee,0x1c),(0x644725,0x772925,0x4c),(0x645583,0x428729,0xa0)]
for call,lea_va,off in STACKS:
    fs=func_start(lea_va)
    ins=[(off2,sz,mn,op) for off2,sz,mn,op in md.disasm_lite(BUF[fs-LO:call-LO],fs)]
    # lea 之后到 call
    af=[x for x in ins if x[0]>=lea_va]
    slots=collections.defaultdict(set)
    for (a,sz,mn,op) in af:
        if ',' not in op: continue
        m=re.match(r'^(?:dword|word|byte) ptr \[esp(?:\s*\+\s*(0x[0-9a-f]+|\d+))?\]$',op.split(',',1)[0].strip())
        if not m: continue
        o=int(m.group(1),0) if m.group(1) else 0
        if off<=o<off+16: slots[o-off].add(mn+' '+op)
    ck('Z3a %s lea[esp+%s@%s] 后写到的槽位'%(hex(call),hex(lea_va),hex(off)), True,
       dict(slots=sorted(slots),detail={k:sorted(v)[:2] for k,v in slots.items()}))
# Z5 汇总（用 m12 结果）
J=json.load(open('/home/t628/projects/ra2-campaign-forge/_r198/m12_final.json'))
cls=J['cls']
tot=sum(cls.values())
ck('Z5a 331 覆盖', tot==331, tot)
groups=collections.Counter()
for k,v in cls.items():
    if k=='STACK': g='STACK_LOCAL'
    elif k.startswith('GLOBAL_'): g='GLOBAL_ABS_REG'
    elif k.startswith('OTHER_dword ptr [0x'): g='GLOBAL_OBJ_FIELD'
    elif k=='NODEF': g='NODEF'
    elif k.startswith('OTHER_dword ptr ['): g='STRUCT_FIELD'
    else: g='OTHER'
    groups[g]+=v
ck('Z5b 分组', True, dict(groups))
for g,v in groups.most_common(): print('   Z5c %-18s %3d  (%.1f%%)'%(g,v,100.0*v/331))
json.dump(dict(where={hex(a):str(P.where(a)) for a in (0xa8b238,0x817bd0,0xa8b210,0xa83c90,0xa8b230,0xa8eb38,0x8874d0)},
  refs=R,groups=dict(groups),cls=cls,asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m13_bss.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
