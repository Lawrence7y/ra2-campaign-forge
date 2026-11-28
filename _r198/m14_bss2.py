#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R198 第十四刀（收口关键）：0xa8b238 与 0x4A1CA0 调用面的直接关系。
 W1 331 个调用点里，有多少个其 ecx 直接来自 mov ecx,0xa8b238（同函数内最近一次 def）。
 W2 219 处 mov ecx,0xa8b238 里，有多少个后面 <=64B 内 call 0x4A1CA0（或 0x4A1D50/0x4A1DE0 族）。
 W3 0xa8b238 的 +0/+4/+8/+0xC 四槽在 .text 里是否有任何绝对寻址写入（mov [0xa8b238+K],X）。
 W4 反控：换 0x817bd0（真 .data，有文件初值）做同样统计作对照。
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
CALLAT=[];CALLTGT=set()
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
def calls_byte(fn):
    out=[]
    for va in range(LO,HI-5):
        if BUF[va-LO]!=0xE8: continue
        if struct.unpack_from('<i',BUF,va-LO+1)[0]+va+5==fn: out.append(va)
    return out
CS=calls_byte(0x4A1CA0)
ck('W0a 331', len(CS)==331, len(CS))
def last_ecx(c):
    fs=func_start(c)
    if fs is None: return None
    best=None
    for off,sz,mn,op in md.disasm_lite(BUF[fs-LO:c-LO],fs):
        if ',' in op and op.split(',',1)[0].strip()=='ecx': best=(off,mn,op)
    return best
IMP=collections.Counter()
for c in CS:
    d=last_ecx(c)
    if d is None: IMP['NONE']+=1
    else:
        src=d[2].split(',',1)[1].strip()
        IMP[src if re.match(r'^0x[0-9a-f]+$',src) else 'REG_'+src if re.match(r'^e[a-z]{2}$',src) else 'MEM']+=1
ck('W1a 331 调用点的 ecx 直接来源', True, IMP.most_common(6))
ck('W1b ecx 直接来自 0xa8b238 的调用点数', True, IMP.get('0xa8b238',0))
# W2
def mov_ecx_imm(imm):
    out=[]
    for va in range(LO,HI-10):
        if BUF[va-LO]!=0xB9: continue
        if struct.unpack_from('<I',BUF,va-LO+1)[0]==imm: out.append(va)
    return out
for imm in (0xa8b238,0x817bd0):
    M=mov_ecx_imm(imm)
    near=collections.Counter()
    for m in M:
        fs=m
        for off,sz,mn,op in md.disasm_lite(BUF[m-LO:m-LO+64],m):
            if mn=='call' and op.startswith('0x'):
                t=int(op,16)
                if t in (0x4A1CA0,0x4A1D50,0x4A1DE0): near[hex(t)]+=1
                break
    ck('W2a %s 的 mov ecx,imm 数=%d，后 <=64B 内调 CRC 族'%(hex(imm),len(M)), True, dict(near))
# W3 绝对寻址写入
def writes_to(obj):
    out=[]
    for va in range(LO,HI-10):
        # A3 disp32 / 89 disp32 / C7 disp32
        if BUF[va-LO] not in (0xA3,0x89,0xC7): continue
        if va+5>HI: continue
        d=struct.unpack_from('<I',BUF,va-LO+1)[0]
        if obj<=d<obj+16: out.append((hex(va),hex(d),BUF[va-LO:va-LO+5].hex()))
    return out
W3=writes_to(0xa8b238)
ck('W3a 对 0xa8b238..+15 的绝对寻址写', True, dict(n=len(W3),hit=W3[:4]))
W4=writes_to(0x817bd0)
ck('W4a 对照 0x817bd0 的绝对寻址写', True, dict(n=len(W4),hit=W4[:4]))
ck('W4b 0x817bd0 文件初值', True, bytes(RAW[P.r2o(0x817bd0):P.r2o(0x817bd0)+16]).hex() if P.r2o(0x817bd0) else None)
json.dump(dict(imp={k:v for k,v in IMP.items()},b238=IMP.get('0xa8b238',0),
  w3=W3[:10],w4=W4[:10],asserts=N,fails=fails),
  open('/home/t628/projects/ra2-campaign-forge/_r198/m14_bss2.json','w'),ensure_ascii=False,indent=1)
print('\nSUMMARY asserts=%d fails=%d %s'%(N,len(fails),fails))
