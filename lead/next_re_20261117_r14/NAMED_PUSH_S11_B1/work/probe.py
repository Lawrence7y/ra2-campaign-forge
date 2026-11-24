# -*- coding: utf-8 -*-
"""18 行总探针：dword 引用 / 虚表+RTTI / 槽号 / 安装点 / direct callers。"""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core import *

ROWS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "b1_rows.json"), encoding="utf-8"))

out = []
for r in ROWS:
    ea = int(r["entry"], 16)
    refs = dword_refs(ea)
    nontext = [x for x in refs if not in_text(x)]
    vts = []
    seen = set()
    for rv in nontext:
        si = resolve_slot(rv)
        if not si:
            vts.append({"slot_va": hx(rv), "sec": sec_name(rv), "rtti": None})
            continue
        if si["vtable"] in seen:
            continue
        seen.add(si["vtable"])
        lay = vtable_layout(si["vtable"], 6)
        inst = [i for i in install_sites(si["vtable"]) if is_vptr_store(i, si["vtable"])]
        vts.append({
            "slot_va": hx(rv), "sec": sec_name(rv), "vtable": hx(si["vtable"]),
            "slot_index": si["slot_index"], "col": hx(si["col"]), "td": hx(si["td"]),
            "rtti": si["name"], "slot0": hx(lay[0]), "layout6": [hx(x) for x in lay],
            "installs": [(hx(i.address), i.op_str) for i in inst],
        })
    rec = {
        "entry": r["entry"], "name": r["name"],
        "n_refs_all": len(refs), "n_refs_text": len(refs) - len(nontext),
        "refs_nontext": [(hx(x), sec_name(x)) for x in nontext],
        "vtables": vts,
    }
    out.append(rec)
    print("=" * 100)
    print(r["entry"], r["name"], " refs(total/text)=%d/%d" % (len(refs), len(refs) - len(nontext)))
    for v in vts:
        print("   slot %s vtable=%s slot#%s slot0=%s rtti=%s" % (
            v.get("slot_va"), v.get("vtable"), v.get("slot_index"), v.get("slot0"), v.get("rtti")))
        print("      layout[:6] =", v.get("layout6"))
        print("      installs   =", v.get("installs"))

json.dump(out, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nwritten probe.json")
