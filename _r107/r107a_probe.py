#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r107a_probe.py —— 探索性探针（不带断言机制）：19 张 switch 表的判界寄存器定义点

只做一件事：打印每张表 cmp reg,BOUND 之前、写判界寄存器的指令，以及它前 6 条指令。
用来在写正式脚本前看清形态。全段扫描用 disasm_lite + 64KB 分块（防 OOM 硬红线）。
"""
import struct, json, re, os
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

ROOT='/home/t628/projects/ra2-campaign-forge'
os.chdir(ROOT)
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
def u32(va):
    o=off(va); return struct.unpack_from('<I',raw,o)[0]
tn,trva,tvs,tra,trs=next(s for s in secs if s[0]=='.text')
TS=IB+trva; TE=TS+tvs
md=Cs(CS_ARCH_X86,CS_MODE_32); md.detail=True; md.skipdata=True
ml=Cs(CS_ARCH_X86,CS_MODE_32); ml.detail=False; ml.skipdata=True
CH=64*1024
starts=[]
pos=TS
while pos<TE:
    hi=min(pos+CH,TE); buf=raw[off(pos):off(hi)+16]; last=pos
    for a,sz,m,o in ml.disasm_lite(buf,pos):
        if a>=hi: break
        last=a+sz; starts.append(a)
    if last<=pos: last=pos+1
    pos=last
print("insns",len(starts))
D=json.load(open('_r106/r106f_switchsem.json'))['tables']
import bisect
for t in D:
    s=t['selector']; cmp_at=int(s['cmp_at'],16); creg=s['cmp_reg']
    i=bisect.bisect_left(starts,cmp_at)-1
    print("=== table",t['table'],"shape",s['shape'],"cmp",creg,"bound",s['cmp_bound'],"func",t.get('func_by_calltarget'))
    k=i
    shown=0
    while k>=0 and shown<10:
        a=starts[k]
        for ins in md.disasm(raw[off(a):off(a)+16],a):
            print("   %08x %-22s %s %s"%(a,ins.bytes.hex(),ins.mnemonic,ins.op_str))
            break
        k-=1; shown+=1
