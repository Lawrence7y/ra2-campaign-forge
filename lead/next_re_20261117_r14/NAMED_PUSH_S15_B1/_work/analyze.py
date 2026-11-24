# -*- coding: utf-8 -*-
"""S15 B1 逐行取证：①入口 / ②RTTI 类身份 / ③b② 合同 / ④活虚表使用见证。
只读 gamemd.exe；只写本批 _work 与 EVIDENCE。
地址一律 int VA，输出 "%08X" 大写无 0x。
"""
import json, os, struct, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from core2 import (_SECS, va_in, va_read, u32, read_cstr, parse_col, parse_td,
                   find_dword_refs, resolve_slot, find_direct_calls,
                   find_vtable_writes, is_atexit_registered,
                   find_containing_atlas_func, ATEXIT_VA)
from capstone.x86 import *

ENTRIES = ["006E3E30", "006E57A0", "006E6470", "0071F930", "0071FA80",
           "00726860", "007268D0", "00726950", "00727BF0", "00727C80"]

# 陷阱③ 参照：主虚表 slot0 常见 00410260；副/成员表 slot0 常见 004105E0/00410580/00410590
MAIN_SLOT0 = {0x00410260}
SUB_SLOT0 = {0x004105E0, 0x00410580, 0x00410590}


def vtable_len(vb, limit=400):
    """从 vb 起数连续落在 .text 的 dword 个数。"""
    n = 0
    while n < limit:
        v = u32(vb + 4 * n)
        if v is None or not R.in_text(v):
            break
        n += 1
    return n


def rtti_chain(col_va):
    """COL: sig@+0, off@+4, cd@+8, td@+0xC, chd@+0x10。返回描述符全貌。"""
    ci = parse_col(col_va)
    if not ci:
        return None
    out = dict(ci)
    out["sig_hex"] = "%08X" % ci["sig"] if ci["sig"] is not None else None
    tdi = parse_td(ci["td"])
    out["td_name"] = tdi["name"] if tdi else None
    out["td_name_va"] = "%08X" % tdi["name_va"] if tdi else None
    # CHD: signature@+0, attributes@+4, numBaseClasses@+8, pBaseClassArray@+0xC
    chd = ci["chd"]
    if chd and va_in(chd):
        attr = u32(chd + 4)
        nbase = u32(chd + 0x8)
        arr = u32(chd + 0xC)
        bases = []
        if arr and nbase and 0 < nbase <= 16 and va_in(arr):
            for i in range(nbase):
                bc = u32(arr + 4 * i)
                if bc and va_in(bc):
                    # BCD: pTypeDescriptor@+0, numContainedBases@+4, PMD@+8(3 dwords), attr@+0x14
                    btd_va = u32(bc)
                    btd = parse_td(btd_va) if btd_va else None
                    bases.append({"col": "%08X" % bc,
                                  "td": "%08X" % btd_va if btd_va else None,
                                  "name": btd["name"] if btd else None,
                                  "mdisp": u32(bc + 8), "pdisp": u32(bc + 0xC),
                                  "vdisp": u32(bc + 0x10), "attr": u32(bc + 0x14)})
        out["chd"] = {"va": "%08X" % chd, "sig": u32(chd), "attr": attr,
                      "nbase": nbase, "arr": "%08X" % arr if arr else None, "bases": bases}
    else:
        out["chd"] = None
    return out


def classify_table(vb):
    n = vtable_len(vb)
    s0 = u32(vb)
    col = u32(vb - 4)
    kind = "unknown"
    if s0 in MAIN_SLOT0:
        kind = "MAIN(主虚表)"
    elif s0 in SUB_SLOT0:
        kind = "SUB(副/成员表)"
    return {"vtable_base": "%08X" % vb, "vlen": n, "slot0": "%08X" % s0 if s0 is not None else None,
            "slot0_kind": kind, "col_at_neg4": "%08X" % col if col is not None else None}


def find_all_dword_refs(target):
    """全镜像（含 .text）所有 dword==target 的位置。"""
    needle = struct.pack("<I", target)
    refs = []
    for nm, v0, sz, data in _SECS:
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0:
                break
            refs.append({"va": "%08X" % (v0 + i), "section": nm})
            st = i + 1
    return refs


def ring1(entry):
    ea = int(entry, 16)
    info = R.ATLAS.get(entry)
    body = R.read_va(ea, info["size"]) if info else b""
    insns = R.disasm(ea, body) if body else []
    skips = sum(1 for i in insns if i.id == 0)
    last = insns[-1].mnemonic if insns else None
    return {
        "in_text": R.in_text(ea),
        "atlas_size": info["size"] if info else None,
        "atlas_n_instr": info["n_instr"] if info else None,
        "n_decoded": len(insns), "n_skipdata": skips,
        "last_mnemonic": last,
        "covered": (insns[-1].address + insns[-1].size - ea) if insns else 0,
        "span_ok": bool(info and insns and (insns[-1].address + insns[-1].size - ea) == info["size"]),
        "ends_ok": last in ("ret", "jmp", "retf") or (last is not None and last.startswith("j")),
    }, insns


def ring2(ea):
    """entry 作为 4B VA 出现的所有位置 => 表候选；回扫 COL；钉类名。"""
    out = []
    for ref in find_all_dword_refs(ea):
        refva = int(ref["va"], 16)
        si = resolve_slot(refva)
        rec = {"slot_va": ref["va"], "section": ref["section"]}
        if not si:
            rec["rtti"] = None
            rec["note"] = "no COL within 40 dwords back"
            out.append(rec)
            continue
        vb = si["vtable_base"]
        rec.update({
            "vtable_base": "%08X" % vb,
            "slot_off": si["slot_off"],
            "slot_index": si["slot_off"] // 4,
            "col": "%08X" % si["col"],
            "td": "%08X" % si["td"],
            "name_va": "%08X" % si["name_va"],
            "rtti_name": si["rtti_name"],
            "table": classify_table(vb),
            "rtti": rtti_chain(si["col"]),
        })
        out.append(rec)
    return out


def ring4(ea, vbs):
    """活虚表见证：该虚表在 .text 的全部写点，逐个分类 atexit / 删除析构器 / 构造安装。"""
    res = {}
    for vb in vbs:
        w = find_vtable_writes(vb)
        sites = []
        for kind in ("global", "regdisp"):
            for it in (w["global"] if kind == "global" else
                       [{"write_va": "%08X" % x, "global": None} for x in w["regdisp"]]):
                wva = int(it["write_va"], 16)
                f = find_containing_atlas_func(wva)
                fentry = f[1] if f else None
                ax = is_atexit_registered(f[0]) if f else None
                # 删除析构器识别：所在函数体内含 `call [reg+4]`/operator delete 前兆，
                # 且该函数自身是 sc_b？——这里只做保守标记，人工复核
                sites.append({
                    "write_va": it["write_va"],
                    "global": it["global"],
                    "in_func": fentry,
                    "in_func_va": "%08X" % f[0] if f else None,
                    "atexit_push_sites": [["%08X" % a, "%08X" % b] for a, b in ax] if ax else [],
                    "atexit": bool(ax) if ax is not None else None,
                })
        res["%08X" % vb] = {"imm_loads": ["%08X" % x for x in w["imm_load"]],
                            "sites": sites}
    return res


def main():
    want = sys.argv[1:] if len(sys.argv) > 1 else ENTRIES
    allout = {}
    for entry in want:
        ea = int(entry, 16)
        r1, insns = ring1(entry)
        r2 = ring2(ea)
        vbs = sorted({int(x["vtable_base"], 16) for x in r2 if x.get("vtable_base")})
        r4 = ring4(ea, vbs)
        ch = R.channel_screen_A(insns)
        direct = find_direct_calls(ea)
        allout[entry] = {
            "entry": entry, "ring1": r1, "ring2": r2,
            "ring3b2_screen": ch, "direct_callers": ["%08X" % x for x in direct],
            "ring4": r4,
        }
        print("== %s  atlas=%s size=%s insn=%d skip=%d last=%s span_ok=%s" %
              (entry, r1["atlas_size"] is not None, r1["atlas_size"], r1["n_decoded"],
               r1["n_skipdata"], r1["last_mnemonic"], r1["span_ok"]))
        for x in r2:
            if x.get("rtti_name"):
                print("   表 %s slot#%d %s  RTTI=%s  vlen=%d" %
                      (x["vtable_base"], x["slot_index"], x["table"]["slot0_kind"],
                       x["rtti_name"], x["table"]["vlen"]))
            else:
                print("   ref %s (%s) no-RTTI" % (x["slot_va"], x["section"]))
        print("   direct_callers=%s  chA P1=%d P2=%d P3=%d" %
              (allout[entry]["direct_callers"], ch["p1"], ch["p2"], ch["p3"]))
        for vb, w in r4.items():
            print("   vt %s 写点 %d" % (vb, len(w["sites"])))
            for s in w["sites"]:
                print("      %s in %s atexit=%s" % (s["write_va"], s["in_func"], s["atexit"]))
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "analyze.json"),
              "w", encoding="utf-8") as f:
        json.dump(allout, f, ensure_ascii=False, indent=1)
    print("\nwrote analyze.json")


if __name__ == "__main__":
    main()
