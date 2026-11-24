# -*- coding: utf-8 -*-
"""逐行完整反汇编 + 虚表写点/构造vs析构(㉓)分析。输出 work/detail_<entry>.txt"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import np_core as C

CANDS = [
    ("004A2B60", 360, "CStreamClass::slot3"),
    ("004A2CD0", 302, "CStreamClass::slot4"),
    ("006BEF10", 114, "TClassFactory<CStreamClass>::slot3"),
    ("006BF690", 117, "TClassFactory<SuperClass>::slot3"),
    ("00539AE0", 956, "Load_StreamFields"),
    ("0055AAC0", 122, "Load_SwizzledObject"),
]

def dump_body(entry_hex, size):
    ea = int(entry_hex, 16)
    insns = C.disasm_body(ea, size)
    out = []
    for ins in insns:
        marker = ""
        if ins.id == 0:
            marker = " SKIPDATA"
        out.append("%s: %-10s %-40s ; %s%s" % (
            C.hx(ins.address), ins.mnemonic, ins.op_str,
            ins.bytes.hex(" ").upper(), marker))
    return "\n".join(out)

def analyze_vt(vt_base, entry_hex):
    """枚举虚表全部写点，分 global/regdisp/imm_load，标 atexit/构造器。"""
    out = []
    w = C.find_vtable_writes(vt_base)
    out.append("vtable %s write sites:" % C.hx(vt_base))
    out.append("  imm_load (B8+r): %s" % ", ".join(w["imm_load"]))
    for g in w["global"]:
        f = C.containing_atlas_func(int(g["write_va"], 16))
        ax = C.is_atexit_registered(f[0]) if f else []
        out.append("  global write @%s -> [%s] in_func=%s(%s) atexit=%s" %
                   (g["write_va"], g["global"], f[1] if f else "?", f[2] if f else "?", bool(ax)))
    for rd in w["regdisp"]:
        f = C.containing_atlas_func(int(rd, 16))
        ax = C.is_atexit_registered(f[0]) if f else []
        out.append("  regdisp write @%s in_func=%s(%s) atexit=%s" %
                   (rd, f[1] if f else "?", f[2] if f else "?", bool(ax)))
    # also: scan slot0 value / table extent
    slot0 = C.u32(vt_base)
    out.append("  slot0=[vt+0]=%s (main-table slot0 often 00410260; sub-table 004105E0/00410580/00410590)" %
               (C.hx(slot0) if slot0 is not None else "?"))
    return "\n".join(out)

def main():
    for e, sz, nm in CANDS:
        fn = "detail_%s.txt" % e
        with open(fn, "w", encoding="utf-8") as f:
            f.write("# %s %s\n\n" % (e, nm))
            f.write("## disassembly (size=%d)\n" % sz)
            f.write(dump_body(e, sz))
            f.write("\n\n## dword refs / vtable\n")
            ea = int(e, 16)
            for refva, sec in C.find_dword_refs(ea):
                si = C.resolve_slot(refva, kmax=64)
                f.write(" slot@%s [%s] -> %s\n" % (C.hx(refva), sec, si and si["rtti_name"]))
                if si:
                    f.write(analyze_vt(si["vtable_base"], e) + "\n")
            f.write("\n## direct callers\n")
            for c in C.find_direct_calls(ea):
                f.write(" call@%s\n" % C.hx(c))
        print("wrote", fn)

if __name__ == "__main__":
    main()
