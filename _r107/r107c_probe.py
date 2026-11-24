#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107c_probe.py —— 探索性探针：从每个候选起点线性解码，检验能否"恰好"走到 holder

判据：从 S 起线性解码，若 holder 出现在指令边界上，则 holder 在 S 的函数体内（强证据）。
另统计 S 到 holder 之间的 ret 数（MSVC 函数体内 ret 只应在 case 尾，多 ret 说明是多个函数）。
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
tn,trva,tvs,tra,trs=next(s for s in secs if s[0]=='.text')
TS=IB+trva; TE=TS+tvs
md=Cs(CS_ARCH_X86,CS_MODE_32); md.skipdata=True; md.detail=False

def path(S,H,limit=0x8000):
    """从 S 线性解码，看 H 是否落在指令边界；返回 (hit, n_insn, n_ret, last_addr)"""
    a=S; n=0; nret=0; last=None
    while a<H and a<S+limit:
        buf=raw[off(a):off(a)+16]
        got=None
        for i in md.disasm(buf,a):
            got=i; break
        if got is None: return (False,n,nret,last,'UNDECODABLE')
        if got.address==H: return (True,n,nret,last,'HIT')
        if got.mnemonic.startswith('ret'): nret+=1
        n+=1; last=got.address
        a=got.address+got.size
    return (a==H,n,nret,last,'END')

D=json.load(open('_r106/r106f_switchsem.json'))['tables']
for t in D:
    H=int(t['holder'],16)
    S=int(t['func_by_calltarget'],16)
    hit,n,nret,last,why=path(S,H)
    S2=int(t['func_by_retpad'],16) if t.get('func_by_retpad') else None
    r2=path(S2,H) if S2 else None
    print("%-10s H=%08x R106=%08x hit=%s insn=%d ret=%d why=%s | RETPAD=%s %s" % (
        t['table'],H,S,hit,n,nret,why,
        ("%08x"%S2) if S2 else None, (("hit=%s ret=%d"%(r2[0],r2[2])) if r2 else "-")))
