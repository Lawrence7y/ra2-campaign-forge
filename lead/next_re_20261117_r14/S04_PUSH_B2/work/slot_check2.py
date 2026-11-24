# -*- coding: utf-8 -*-
"""二次核验：用 witness_core.find_dword_refs + resolve_slot（B1 已审实现）
确认 18 个 entry 在全部数据段是否作为 dword 出现、是否可解析为 RTTI 虚表槽。
只读。"""
import os, sys, json, csv
WORK_B1 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B1\work"
sys.path.insert(0, WORK_B1)
import witness_core as W
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S04_PUSH_B2"

entries = []
with open(os.path.join(OUT, "work", "b2_entries.tsv"), encoding="utf-8") as fh:
    for r in csv.DictReader(fh, delimiter="\t"):
        entries.append(r["entry"])

report = {}
for e in entries:
    ea = int(e, 16)
    refs = W.find_dword_refs(ea)
    slots = []
    for refva, sec in refs:
        si = W.resolve_slot(refva)
        if si:
            slots.append({"refva": "%08X" % refva, "sec": sec, "vt": si["vtable_base"],
                          "slot_off": si["slot_off"], "name": si["rtti_name"]})
        else:
            slots.append({"refva": "%08X" % refva, "sec": sec, "vt": None, "name": None})
    named = [s for s in slots if s["name"]]
    report[e] = {"n_refs": len(refs), "n_named_slots": len(named), "slots": slots}
    print("%s dword_refs=%d named_rtti_slots=%d %s" % (e, len(refs), len(named),
          [s["name"] for s in named[:3]]), flush=True)

json.dump(report, open(os.path.join(OUT, "work", "slot_check2.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("wrote slot_check2.json")
