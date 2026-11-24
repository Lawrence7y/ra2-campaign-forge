# -*- coding: utf-8 -*-
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
MD=Cs(CS_ARCH_X86,CS_MODE_32); MD.detail=True; MD.skipdata=True
for e in ['775940','7B54B0','7C8D20','7B5340','7B4940','79D110']:
    ea=int(e,16); sz=R.ATLAS.get(e,{}).get('size',100)
    print("="*90)
    print("CALLEE %s size=%s profile=%s" % (e,sz,R.callee_return_profile(ea)))
    code=R.read_va(ea,sz or 100)
    for i in MD.disasm(code,ea):
        if i.mnemonic in ('ret','xor') or 'eax' in i.op_str or i.mnemonic in ('mov','call'):
            print("  %08X %-7s %s | %s" % (i.address,i.mnemonic,i.op_str,i.bytes.hex()))
