# -*- coding: utf-8 -*-
"""虚表结构与全部写点分类：主表 vs 副表、slot0 身份、写点是否为析构器/atexit。"""
import os, sys, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

VTS = [0x007F4090, 0x007F5180, 0x007E4A28]

def slot_target(vt, i):
    return u32(vt + 4 * i)

def dump_vt(vt, nmax=60):
    print("\n--- vtable %s ---" % hx(vt))
    col = u32(vt - 4)
    ci = parse_col(col) if col else None
    td = parse_td(ci["td"]) if ci else None
    print("  [vt-4]=COL %s  pTD=%s (abs VA)  name@%s = %r"
          % (hx(col) if col else "-", hx(ci["td"]) if ci else "-",
             hx(td["name_va"]) if td else "-", td["name"] if td else "-"))
    if ci:
        print("  COL raw: ", va_read(col, 0x18).hex(" "))
    if ci and ci["chd"]:
        ch = ci["chd"]
        print("  pCHD=%s CHD sig=%s attr=%s nbase=%s niface=%s"
              % (hx(ch), hx(u32(ch)) if u32(ch) is not None else "-",
                 hx(u32(ch + 4)) if u32(ch + 4) is not None else "-",
                 u32(ch + 8), u32(ch + 0xC)))
    print("  slots (addr -> target, target_in_text):")
    for i in range(nmax):
        t = slot_target(vt, i)
        if t is None: break
        mark = ""
        if t == 0:
            mark = "  <-- NULL/END"
        elif not in_text(t):
            mark = "  <-- not .text"
        print("    [%2d] off +0x%02X  %s -> %s%s" % (i, 4 * i, hx(vt + 4 * i), hx(t), mark))
        if t == 0:
            break

for vt in VTS:
    dump_vt(vt)

print("\n\n######## 写点分类 ########")
for vt in VTS:
    print("\n=== vt %s ===" % hx(vt))
    w = find_vtable_writes(vt)
    allw = [("global:" + g["write_va"], int(g["write_va"], 16), g["global"]) for g in w["global"]]
    allw += [("regdisp:" + g, int(g, 16), None) for g in w["regdisp"]]
    allw += [("immload:" + g, int(g, 16), None) for g in w["imm_load"]]
    for tag, addr, g in allw:
        af = containing_atlas_func(addr)
        print("\n  %s   func=%s" % (tag, ("%s size=%d" % (af[1], af[2])) if af else "NONE"))
        start = max(addr - 12, (af[0] if af else addr - 12))
        data = va_read(start, 12 + 24)
        for ins in np_core._md.disasm(data, start):
            mark = " <<<" if ins.address == addr else ""
            b = va_read(ins.address, ins.size).hex(" ")
            print("     %s  %-22s %-8s %s%s" % (hx(ins.address), b, ins.mnemonic, ins.op_str, mark))
    # direct callers of each writer function
    print("  -- writer-function callers / atexit --")
    seen = set()
    for tag, addr, g in allw:
        af = containing_atlas_func(addr)
        if not af or af[0] in seen: continue
        seen.add(af[0])
        cs = find_direct_calls(af[0])
        ae = is_atexit_registered(af[0])
        # does it delete memory?
        body = va_read(af[0], af[2])
        dels = [hx(af[0] + o) for o in []]
        has_free = b"\xE8" in body
        print("     func %s(size %d) callers=%d [%s] atexit_sites=%s"
              % (af[1], af[2], len(cs), " ".join(hx(c) for c in cs[:8]), ae))
