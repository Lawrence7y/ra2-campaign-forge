# -*- coding: utf-8 -*-
"""为 B2 每行做全镜像 dword 引用扫描（含 .text）+ 该 entry 是否安装某张带 RTTI 的虚表。
回答：② 能不能钉住；fn_ 行有没有 vtable/RTTI 入口。"""
import os, sys, json, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
import core2 as C2

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))

SECS = C2._SECS

def all_refs(target):
    needle = struct.pack("<I", target)
    out = []
    for nm, v0, sz, data in SECS:
        st = 0
        while True:
            i = data.find(needle, st)
            if i < 0:
                break
            out.append((v0 + i, nm))
            st = i + 1
    return out

def rtti_name_at_vt(vt):
    """[vt-4]=COL(sig=0) -> [COL+0xC]=TD -> TD+8 名串"""
    c = C2.u32(vt - 4)
    ci = C2.parse_col(c)
    if not ci:
        return None
    tdi = C2.parse_td(ci["td"])
    if not tdi:
        return None
    return {"col": "%08X" % ci["col"], "sig": ci["sig"], "td": "%08X" % ci["td"],
            "name_va": "%08X" % tdi["name_va"], "rtti_name": tdi["name"]}

def vt_installs_by_func(entry):
    """该函数体内是否有 `mov dword ptr [x], imm32` 且 imm 指向一张带 RTTI 的虚表。"""
    size = R.ATLAS.get(entry, {}).get("size") or 0
    insns = R.disasm(int(entry, 16), R.read_va(int(entry, 16), size))
    res = []
    for ins in insns:
        if ins.id == 0 or ins.mnemonic != "mov" or len(ins.operands) != 2:
            continue
        a, b = ins.operands
        if a.type != 1 or b.type != 2:   # mem <- imm
            continue
        imm = b.imm & 0xFFFFFFFF
        if not (0x400000 <= imm < 0x800000):
            continue
        rn = rtti_name_at_vt(imm)
        if rn and ".?AV" in (rn["rtti_name"] or ""):
            res.append({"va": "%08X" % ins.address, "vt": "%08X" % imm,
                        "op": ins.op_str, **rn})
    return res

out = {}
for r in ROWS:
    e = r["entry"]
    ea = int(e, 16)
    refs = all_refs(ea)
    slots = []
    for refva, sec in refs:
        si = C2.resolve_slot(refva)
        slots.append({"ref_va": "%08X" % refva, "section": sec,
                      "resolved": si and {"vtable": "%08X" % si["vtable_base"],
                                          "slot_off": si["slot_off"],
                                          "slot_no": si["slot_off"] // 4,
                                          "col": "%08X" % si["col"],
                                          "td": "%08X" % si["td"],
                                          "name_va": "%08X" % si["name_va"],
                                          "rtti": si["rtti_name"]}})
    out[e] = {"name": r["name"], "refs_total": len(refs),
              "refs_by_section": {}, "slots": slots,
              "installs_by_self": vt_installs_by_func(e)}
    for _, sec in refs:
        out[e]["refs_by_section"][sec] = out[e]["refs_by_section"].get(sec, 0) + 1

json.dump(out, open(os.path.join(WORK, "refs.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
for e, v in out.items():
    print("%s %-30s refs=%-3d %s" % (e, v["name"], v["refs_total"], v["refs_by_section"]))
    for s in v["slots"]:
        rr = s["resolved"]
        print("    slot@%s %s -> %s" % (s["ref_va"], s["section"],
              ("vt=%s slot#%d %s" % (rr["vtable"], rr["slot_no"], rr["rtti"])) if rr else "*unresolved*"))
    for i in v["installs_by_self"]:
        print("    self-installs %s vt=%s %s rtti=%s" % (i["va"], i["vt"], i["op"], i["rtti_name"]))
print("-> refs.json")
