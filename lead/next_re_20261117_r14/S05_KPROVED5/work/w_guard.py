# -*- coding: utf-8 -*-
"""w-guard: 精确 extent 内提取 jcc 门控 + 各闸动作(callee)，用于 D-42 细则#1 判定。
不依赖 atlas entry+size；字节来自 ax_lib。"""
import os, sys, json
sys.path.insert(0, os.path.dirname(__file__))
import ax_lib
from capstone import *
from capstone.x86 import *
import csv

CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
CAND = ["0040BA50","0040CDC0","00410220","00410230","00410BE0","0050EA00","00512D30",
        "00513100","005134D0","005F9720","006F3F40","006F4A70","006F6CA0","00708D70",
        "00709A30","00709A40","0070C250","0070E280","0070E2B0","00711EB0","00711F00","007171A0"]
ext={}
for r in csv.DictReader(open(CLS,encoding='utf-8'),delimiter='\t'):
    if r['entry'].upper() in CAND:
        ext[r['entry'].upper()]=(int(r['ext_lo'],16),int(r['ext_hi'],16))

pe=ax_lib.load(); MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True

def callee_str(i):
    if i.mnemonic=='call':
        return ('direct:'+i.op_str) if not i.op_str.startswith('dword') else ('virt:'+i.op_str)
    return None

for e in CAND:
    lo,hi=ext[e]; ins=list(MD.disasm(pe.buf[pe.off(lo):pe.off(lo)+(hi-lo)],lo))
    calls=[(i.address-lo,callee_str(i)) for i in ins if i.mnemonic=='call']
    jcc=[(i.address-lo,i.mnemonic,i.op_str) for i in ins if i.mnemonic.startswith('j') and i.mnemonic!='jmp']
    distinct_callees=sorted(set(c for _,c in calls))
    print("\n== %s  ncall=%d njcc=%d distinct_callee=%d" % (e,len(calls),len(jcc),len(distinct_callees)))
    print("   CALLS:", "; ".join("%+0x:%s"%(a,c) for a,c in calls))
    print("   JCC  :", "; ".join("%+0x:%s %s"%(a,m,t) for a,m,t in jcc))
