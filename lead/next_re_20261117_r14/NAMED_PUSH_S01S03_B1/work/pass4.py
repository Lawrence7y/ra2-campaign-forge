# -*- coding: utf-8 -*-
"""第四轮：间接 call 全局指针所指目标 / 关键函数ctor-dtor分类 / 00410260 是什么。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C

def where(va):
    return C.va_in(va)

def show_glob(va, label):
    v = C.u32(va)
    print("  GLOBAL %08X (%s) sec=%s val=%s" % (va, label, where(va), ("%08X" % v) if v is not None else "None"))

print("=== indirect-call globals (0065D240 / 0065D3A0) ===")
for va, lab in [(0x7e1128,"0065D254 call"),(0x7e1130,"0065D26C call"),(0x7e112c,"0065D289 call"),
                (0x7e11e0,"0065D3B7 call"),(0x7e1200,"0065D3C9 call"),(0x7f091c,"0065D3A9 call")]:
    show_glob(va, lab)

print("\n=== 00410260 (main-table slot0 frequently) ===")
for i in R.disasm_body(0x410260, 60):
    if i.id:
        print("   %08X %-18s %s" % (i.address, i.bytes.hex(), i.mnemonic+" "+i.op_str))

print("\n=== installer function classification ===")
def disasm_func(va, size, label):
    print("\nFUNC %08X %s size=%d:" % (va, label, size))
    for i in R.disasm_body(va, size):
        if i.id == 0: 
            continue
        extra=""
        if i.id == R.X86_INS_CALL and i.operands and i.operands[0].type == R.X86_OP_IMM:
            extra=" ; callee=%08X" % (i.operands[0].imm & 0xFFFFFFFF)
        print("   %08X  %-20s %s%s" % (i.address, i.bytes.hex(), i.mnemonic+" "+i.op_str, extra))

# classify by checking callers of the installer + is it slot0/slot# of its vt
for va, sz, lab in [(0x431b20,95,"base called by CDFile ctors"),(0x431b80,64,"base called by CDFile dtor"),
                    (0x65d420,0,"RawFileClass slot6 virtual"),(0x6c9850,0,"called by FileStraw installer"),
                    (0x477770,0,"FileStraw slot0"),(0x6c9890,0,"FileStraw slot1")]:
    if sz>0:
        disasm_func(va, sz, lab)

print("\n=== direct caller context ===")
for callerva in (0x473b07, 0x473f14):
    st = callerva - 32
    print("\n around caller %08X:" % callerva)
    for i in R.disasm_body(st, 64):
        if i.id:
            print("   %08X  %-20s %s%s" % (i.address, i.bytes.hex(), i.mnemonic+" "+i.op_str,
                  "  <== call" if i.address==callerva or (i.id==R.X86_INS_CALL and i.operands and i.operands[0].type==R.X86_OP_IMM and (i.operands[0].imm&0xFFFFFFFF) in (0x432050,0x65d240)) else ""))
