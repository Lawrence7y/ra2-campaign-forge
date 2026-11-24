#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Find lepton->cell conversions: 'sar reg,8' / '>>8' patterns and nearby cellIdx (shl 9) in cached disasm."""
import re, sys
from core_disasm import get_insns
D=get_insns(); INS=D["insns"]

def find(pattern, limit=400):
    rx=re.compile(pattern, re.I)
    out=[]
    for (a,s,m,o) in INS:
        if rx.search((m+" "+o)):
            out.append((a,s,m,o))
    return out

if __name__=="__main__":
    mode=sys.argv[1] if len(sys.argv)>1 else "sar8"
    if mode=="sar8":
        # capstone prints shift counts in DECIMAL: "sar eax, 8"
        rows=[(a,s,m,o) for (a,s,m,o) in INS if m=='sar' and o.strip().endswith(', 8')]
        print("=== sar reg,8 count=%d ==="%len(rows))
        for (a,s,m,o) in rows[:200]:
            print("%08X %s %s"%(a,m,o))
    elif mode=="shl9":
        rows=[(a,s,m,o) for (a,s,m,o) in INS if m=='shl' and o.strip().endswith(', 9')]
        print("=== shl reg,9 (Y*512) count=%d ==="%len(rows))
        for (a,s,m,o) in rows[:250]:
            print("%08X %s %s"%(a,m,o))
