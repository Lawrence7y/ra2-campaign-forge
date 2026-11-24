# -*- coding: utf-8 -*-
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R, core2 as C2

def show(a,b):
    for ins in R.disasm(a, R.read_va(a,b-a)):
        print("    %08X  %-20s %s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("### 0075E510 tail (destructor? look for base dtor / free)")
show(0x0075E578, 0x0075E610)
print("\n### all .text immediates == 0x007F6B30 (install sites of WarheadTypeClass vt)")
needle=struct.pack("<I",0x007F6B30)
T=R.TEXT_DATA; B=R.TEXT_VA; st=0
while True:
    i=T.find(needle,st)
    if i<0: break
    print("  imm@%08X bytes_before=%s" % (B+i, T[max(0,i-6):i].hex()))
    st=i+1
print("\n### 0046C730 - callee 0x5F9950 full profile check")
p=R.callee_return_profile(0x5F9950); print("  profile:",p)
