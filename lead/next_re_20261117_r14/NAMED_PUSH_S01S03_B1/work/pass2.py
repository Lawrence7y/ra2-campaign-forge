# -*- coding: utf-8 -*-
"""第二轮：打印 4 个 S03 entry 的完整反汇编 + 每个 vtable 的全部写点（含所在函数/是否 atexit）。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C

ROWS = [
    ("00432050", "CDFileClass::vslot12", 584),
    ("0065D240", "CDFileClass::slot15", 101),
    ("0065D3A0", "RawFileClass::slot0", 124),
    ("007BA530", "FileStraw::slot2", 93),
]

for eh, name, size in ROWS:
    ea = int(eh, 16)
    print("=" * 110)
    print("ENTRY", eh, name, "size=", size)
    print("---- FULL DISASM ----")
    ins = R.disasm_body(ea, size)
    for i in ins:
        if i.id == 0:
            print("  %08X  db %s  (skipdata)" % (i.address, i.bytes.hex()))
        elif i.id == R.X86_INS_CALL:
            op = i.op_str
            callee = ""
            if i.operands and i.operands[0].type == R.X86_OP_IMM:
                cv = i.operands[0].imm & 0xFFFFFFFF
                callee = "  ; callee=%08X" % cv
            print("  %08X  %-24s %-40s%s" % (i.address, i.bytes.hex(), i.mnemonic + " " + i.op_str, callee))
        else:
            print("  %08X  %-24s %s" % (i.address, i.bytes.hex(), i.mnemonic + " " + i.op_str))
    print("---- VTABLES (from refs) + ALL WRITE POINTS ----")
    refs = C.find_dword_refs(ea)
    seen_vt = set()
    for refva, sec in refs:
        si = C.resolve_slot(refva)
        if not si:
            print("  ref %08X@%s : no RTTI chain" % (refva, sec)); continue
        vba = si["vtable_base"]
        if vba in seen_vt:
            continue
        seen_vt.add(vba)
        print("  entry in vt=%08X slot_off=%d col=%08X td=%08X rtti=%s" %
              (vba, si["slot_off"], si["col"], si["td"], si["rtti_name"]))
        w = C.find_vtable_writes(vba)
        print("    global writes:", [("W%08X->G%08X" % (g["write_va"], g["global"])) for g in w["global"]])
        print("    regdisp writes:", ["%08X" % x for x in w["regdisp"]])
        print("    imm loads:", ["%08X" % x for x in w["imm_load"]])
        # classify each global/regdisp write point by containing function
        for g in w["global"]:
            f = C.find_containing_atlas_func(g["write_va"])
            if f:
                ax = C.is_atexit_registered(f[0])
                print("       write@%08X in_func=%08X size=%d atexit=%s" % (g["write_va"], f[0], f[2], ax))
        for rw in w["regdisp"]:
            f = C.find_containing_atlas_func(rw)
            if f:
                ax = C.is_atexit_registered(f[0])
                print("       regdisp write@%08X in_func=%08X size=%d atexit=%s" % (rw, f[0], f[2], ax))
    print()
