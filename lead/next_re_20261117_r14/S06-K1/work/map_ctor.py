from pehelp import *
import struct

# MapClass CHD base array COLs -> TD names
print("=== MapClass base COLs ===")
for bcol in [0x7faa30,0x7faa18,0x7faa00,0x7fa9e8]:
    ptd=u32(bcol+0xc)
    nm=read(ptd+8,40) if ptd else b''
    print(f"  COL {bcol:#x}: offset={u32(bcol+4):#x} pTD={ptd and hex(ptd)} name={nm.split(b'@')[0]!r}")

# Disassemble around 0x565100 to find function prologue and any push <imm> / call new
print("\n=== disasm 0x565120..0x5651a0 ===")
for ins in disasm(0x565120, 0x90, count=60):
    print("   ", fmt(ins))

# search for 'push imm; call' patterns near 0x565000..0x565300
print("\n=== push imm32 instructions 0x565000..0x565400 ===")
for ins in disasm(0x565000, 0x400):
    if ins.mnemonic=='push' and ins.operands and ins.operands[0].type==X86_OP_IMM:
        print(f"   {fmt(ins)}")
