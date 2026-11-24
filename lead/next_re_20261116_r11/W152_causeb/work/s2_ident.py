"""S2: verify the COL/class identity of vtable 0x7E3EBC and read slot 0 / slot 73
text, plus full disassembly of the chain functions and their primitives.

Run: python s2_ident.py > ..\\EVIDENCE\\s2_ident.log 2>&1
"""
import struct
import w152_core as C


def col_name(col_va):
    """MSVC RTTICompleteObjectLocator: +0xC signature, +0x10 pTypeDescriptor (RVA),
    +0x14 pClassDescriptor (RVA), +0x18 pSelf (RVA).  Version 1 (x86) layout:
    +0x00 signature, +0x04 offset, +0x08 cdOffset, +0x0C pTypeDescriptor,
    +0x10 pClassDescriptor."""
    try:
        sig = C.u32(col_va)
        off = C.u32(col_va + 4)
        cd = C.u32(col_va + 8)
        ptd = C.u32(col_va + 0xC)
        pcd = C.u32(col_va + 0x10)
    except Exception as e:
        return "read-fail %s" % e
    if ptd and ptd < C.IB:
        ptd += C.IB
    out = {"sig": sig, "offset": off, "cdOffset": cd, "pTypeDescriptor": ptd,
           "pClassDescriptor": pcd}
    if 0x400000 <= ptd < 0x400000 + 0x800000:
        raw = C.read(ptd, 128)
        # TypeDescriptor: vtbl ptr(4) spare(4) name[ ]
        nm = raw[8:]
        z = nm.find(b'\0')
        out["name"] = nm[:z].decode('latin1')
    return out


VT = 0x007E3EBC
col = C.u32(VT - 4)
print("vtable %08X  [vt-4]=%08X" % (VT, col))
info = col_name(col)
print("COL:", info)
print("")

print("=== slot 0 (0x%X) ===" % 0)
slot0 = C.u32(VT)
print("target %08X size=%s" % (slot0, C.fn_size(slot0)))
for insn in C.disas_fn(slot0):
    print(C.fmt(insn))
print("")
print("=== slot 73 (0x124) ===")
slot73 = C.u32(VT + 73 * 4)
print("target %08X size=%s" % (slot73, C.fn_size(slot73)))
for insn in C.disas_fn(slot73):
    print(C.fmt(insn))
