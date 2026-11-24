#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107b_probe.py —— 探索性探针：检验 R106「入口必须被 call 直接引用」是否真的给出"所属函数"

假设 H：R106 交的 17 个入口中，有些其实是"表前面某个无关函数"的入口，
因为「<=holder 的最近 call 直接目标」只保证"是个函数入口"，不保证"是本函数入口"。
判据：若在 (S, holder] 区间内还存在另一个**确定函数起点**（call 目标 ∪ 虚表槽值 ∪
16 字节对齐且前面是 nop/int3/ret 填充的地址），则 S 不是所属函数。
再对每个候选起点做"线性解码能否恰好走到 holder"复核。
"""
import struct, json, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
ROOT='/home/t628/projects/ra2-campaign-forge'; os.chdir(ROOT)
raw=open('ra2bench/gamemd.exe','rb').read()
e=struct.unpack_from('<I',raw,0x3c)[0]
nsec,=struct.unpack_from('<H',raw,e+6); osz,=struct.unpack_from('<H',raw,e+20); opt=e+24
IB=struct.unpack_from('<I',raw,opt+28)[0]
secs=[]
for i in range(nsec):
    o=opt+osz+i*40
    nm=raw[o:o+8].rstrip(b'\0').decode(); vs,rva,rs,ra=struct.unpack_from('<IIII',raw,o+8)
    secs.append((nm,rva,vs,ra,rs))
def off(va):
    r=va-IB
    for nm,srva,vs,ra,rs in secs:
        if srva<=r<srva+max(vs,rs): return ra+(r-srva)
def byte(va):
    o=off(va); return raw[o] if o is not None else None
tn,trva,tvs,tra,trs=next(s for s in secs if s[0]=='.text')
TS=IB+trva; TE=TS+tvs
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=True
ml=Cs(CS_ARCH_X86,CS_MODE_32); ml.skipdata=True; ml.detail=False

# 全段起点 + call 目标
starts=[]; callt=set()
pos=TS; CH=64*1024
while pos<TE:
    hi=min(pos+CH,TE); buf=raw[off(pos):off(hi)+16]; last=pos
    for a,sz,m,o in ml.disasm_lite(buf,pos):
        if a>=hi: break
        last=a+sz; starts.append(a)
        if m=='call' and o.startswith('0x') and o[2:].isalnum():
            try: callt.add(int(o,16))
            except: pass
    if last<=pos: last=pos+1
    pos=last
print("starts",len(starts),"callt",len(callt))
SSET=set(starts)

# 虚表槽值
sym=json.load(open('out/reverse/symbols.json'))['classes']
vslot=set()
for n,c in sym.items():
    for v in (c.get('vfuncs') or []): vslot.add(int(v,16))

def is_pad(b):
    return b in (0x90,0xcc,0x00,0x66)

def is_definite_start(a):
    if a in callt: return 'CALL'
    if a in vslot: return 'VSLOT'
    if a%16==0:
        b1=byte(a-1); b0=byte(a-2)
        if b1 in (0x90,0xcc) or b0 in (0x90,0xcc): return 'ALIGN'
    return None

def containing(holder, span=0x4000):
    lo=holder-span
    cands=[a for a in starts if lo<=a<=holder and is_definite_start(a)]
    return cands

D=json.load(open('_r106/r106f_switchsem.json'))['tables']
for t in D:
    h=int(t['holder'],16); r106=int(t['func_by_calltarget'],16) if t.get('func_by_calltarget') else None
    c=containing(h)
    nearest=c[-1] if c else None
    flag='OK' if nearest==r106 else '**DIFF**'
    print("%-10s holder %08x  R106 %s  nearest_definite %s  %s" % (t['table'],h,hex(r106) if r106 else None,hex(nearest) if nearest else None,flag))
    if flag!='OK':
        print("     cands:", " ".join("%08x(%s)"%(a,is_definite_start(a)) for a in c[-6:]))
