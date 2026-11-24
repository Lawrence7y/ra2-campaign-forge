# -*- coding: utf-8 -*-
"""pass1: 7 个候选的 ①②③④ 机械预筛（只报事实，不下结论）。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core
from np_core import *
from capstone import *

HERE = os.path.dirname(os.path.abspath(__file__))
CANDS = json.load(open(os.path.join(HERE, "candidates.json"), encoding="utf-8"))

print("SHA=%s  TEXT=[%08X,%08X)" % (sha256_exe(), TEXT_VA, TEXT_VA + TEXT_SIZE))

for c in CANDS:
    e = int(c["entry"], 16); nm = c["name"]
    print("\n" + "=" * 100)
    print("### %s  %s  %s  size=%s" % (hx(e), c["subsystem"], nm, c["size"]))
    # ---- ① entry ----
    inb = in_text(e)
    af = containing_atlas_func(e)
    if af:
        ea, es, esz = af
        data = va_read(e, esz - (e - ea))
        insns = list(np_core._md.disasm(data, e)) if data else []
    else:
        insns = disasm_body(e, 400)
    print("① in_text=%s atlas=%s insns=%d" % (inb, ("%s size=%d" % (af[1], af[2])) if af else "NONE", len(insns)))
    sk = [i for i in insns if i.id == 0]
    print("   skipdata_holes=%d  first=%s  last=%s" % (len(sk),
          ("%s %s" % (insns[0].mnemonic, insns[0].op_str)) if insns else "-",
          ("%s %s" % (insns[-1].mnemonic, insns[-1].op_str)) if insns else "-"))
    if af:
        end = af[0] + af[2]
        print("   atlas_end=%s  max_insn_end=%s  fit=%s" % (hx(end),
              hx(max(i.address + i.size for i in insns)) if insns else "-",
              (max(i.address + i.size for i in insns) <= end) if insns else "-"))

    # ---- ② vtable slot ----
    refs = find_dword_refs(e)
    print("② dword_refs(outside .text)=%d" % len(refs))
    for rva, sec in refs[:12]:
        rs = resolve_slot(rva)
        if rs:
            print("   slot@%s(%s) -> vt=%s slot#%d COL=%s TD=%s rtti=%r"
                  % (hx(rva), sec, hx(rs["vtable_base"]), rs["slot_idx"],
                     hx(rs["col"]), hx(rs["td"]), rs["rtti_name"]))
        else:
            print("   slot@%s(%s) -> no RTTI (unresolved)" % (hx(rva), sec))

    # ---- ④ direct callers + vtable writes ----
    dcs = find_direct_calls(e)
    print("④ direct_callers=%d %s" % (len(dcs), " ".join(hx(x) for x in dcs[:14])))
    seen_vt = set()
    for rva, sec in refs:
        rs = resolve_slot(rva)
        if rs and rs["vtable_base"] not in seen_vt:
            seen_vt.add(rs["vtable_base"])
            w = find_vtable_writes(rs["vtable_base"])
            print("   vt=%s writes: global=%d regdisp=%d imm_load=%d"
                  % (hx(rs["vtable_base"]), len(w["global"]), len(w["regdisp"]), len(w["imm_load"])))
            for g in w["global"]:
                print("      write@%s -> global %s" % (g["write_va"], g["global"]))
            for g in w["regdisp"][:10]:
                print("      regdisp@%s" % g)
            for g in w["imm_load"][:10]:
                print("      immload@%s" % g)

    # ---- ③ ③b② ----
    sites = channel_A(insns)
    print("③ channel_A sites=%d" % len(sites))
    for s in sites[:10]:
        print("   call=%s test=%s(%s imm=%s) jcc=%s->%s falsy=%s"
              % (s["call_addr"], s["test_addr"], s["test_kind"], s["test_imm"],
                 s["jcc"], s["jcc_target"], s["falsy"]))
        print("      taken   : calls=%s rets=%s has_ret=%s eax=%s"
              % (s["sig_taken"]["calls"], s["sig_taken"]["rets"],
                 s["sig_taken"]["has_ret"], s["sig_taken"]["end_eax"]))
        print("      fallthru: calls=%s rets=%s has_ret=%s eax=%s"
              % (s["sig_fallthrough"]["calls"], s["sig_fallthrough"]["rets"],
                 s["sig_fallthrough"]["has_ret"], s["sig_fallthrough"]["end_eax"]))
