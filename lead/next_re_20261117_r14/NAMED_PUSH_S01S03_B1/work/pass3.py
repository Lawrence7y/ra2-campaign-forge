# -*- coding: utf-8 -*-
"""第三轮：解析 import thunk（间接 call 目标）、列关键 vtable 槽内容+RTTI、看几个装表函数形态。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pefile
import recore as R
import core2 as C

pe = R._pe
pe.parse_data_directories()
IB = R.IB

# --- import IAT resolve ---
iat_map = {}
for ent in getattr(pe, "DIRECTORY_ENTRY_IMPORT", []):
    dll = ent.dll.decode("latin1") if isinstance(ent.dll, bytes) else str(ent.dll)
    for th in ent.imports:
        if th.address is not None:
            iat_map[IB + th.address] = "%s!%s" % (dll, th.name.decode("latin1") if isinstance(th.name, bytes) else str(th.name))
print("import IAT entries:", len(iat_map))
for va in (0x7e1128, 0x7e1130, 0x7e112c, 0x7f091c, 0x7e11e0, 0x7e1200, 0x7e4d90, 0x7f08bc):
    print("  IAT %08X -> %s" % (va, iat_map.get(va, "(not import)")))

# --- vtable dumps ---
def dump_vt(vt_va, label, n=20):
    print("\nVT %08X (%s):" % (vt_va, label))
    for i in range(n):
        v = C.u32(vt_va + 4 * i)
        if v is None:
            break
        mark = ""
        if v in (0x65d240, 0x65d3a0, 0x432050, 0x7ba530):
            mark = "  <== ENTRY"
        print("   slot#%-2d va=%08X val=%08X%s" % (i, vt_va + 4 * i, v, mark))

dump_vt(0x7f0904, "RawFileClass main?", 16)
dump_vt(0x7f08bc, "base of 0065D3A0 writes", 8)
dump_vt(0x7e1668, "CDFileClass", 18)
dump_vt(0x7e3a2c, "BufferIOFileClass", 18)
dump_vt(0x7e4d90, "FileStraw", 8)

# RTTI of 0x7f08bc -4
print("\nRTTI check for base vt 0x7f08bc:")
c = C.u32(0x7f08bc - 4)
print("  COL@%08X=%s" % (0x7f08bc - 4, ("%08X" % c) if c is not None else "None"))
if c:
    ci = C.parse_col(c)
    print("  col=%s" % ci)
    if ci and ci["td"]:
        print("  TD name=%r" % C.parse_td(ci["td"])["name"])

# --- install functions disasm (④ anchors) ---
def disasm_func(va, size, label):
    print("\nFUNC %08X %s size=%d:" % (va, label, size))
    for i in R.disasm_body(va, size):
        if i.id == 0:
            continue
        extra = ""
        if i.id == R.X86_INS_CALL and i.operands and i.operands[0].type == R.X86_OP_IMM:
            cv = i.operands[0].imm & 0xFFFFFFFF
            extra = " ; callee=%08X %s" % (cv, iat_map.get(cv, ""))
        print("   %08X  %-20s %s%s" % (i.address, i.bytes.hex(), i.mnemonic + " " + i.op_str, extra))

for va, sz, lab in [(0x65ca00, 103, "installer?"), (0x65ca80, 49, "installer?"),
                    (0x401950, 36, "CDFile vt installer"), (0x47a9d0, 36, "CDFile vt installer"),
                    (0x7ba590, 48, "FileStraw installer")]:
    disasm_func(va, sz, lab)
