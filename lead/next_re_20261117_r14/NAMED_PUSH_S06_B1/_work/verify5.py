# -*- coding: utf-8 -*-
"""Refined ctor/dtor classification: destructor = push 0/1; call [reg] with disp in {0,4} (slot0/1 virtual dtor).
Then dump the ambiguous funcs fully."""
import os, sys, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
import recore as R
import core2 as C2
from capstone import *
from capstone.x86 import *

def dump(va,cap,label):
    print("="*90); print("%s %08X cap=%d"%(label,va,cap))
    for ins in R.disasm(va,R.read_va(va,cap)):
        if ins.id==0: continue
        print("  %08X: %-8s %-34s | %s"%(ins.address,ins.mnemonic,ins.op_str,ins.bytes.hex(" ")))
        if ins.address-va>=cap: break

for va in (0x544A70, 0x543990, 0x47BBF0, 0x5FC380):
    dump(va, min(R.ATLAS.get(R.hx(va),{}).get("size") or 120, 0x120), "FUNC")
