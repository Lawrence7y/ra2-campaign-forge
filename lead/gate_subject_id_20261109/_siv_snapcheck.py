# -*- coding: utf-8 -*-
# _siv_snapcheck.py — 撰写人扫描快照（_si_scan_out.json）中的争议域记录取证。只读。
import json
from pathlib import Path

WD = Path(r"D:\Project\ra2-campaign-forge\lead\gate_subject_id_20261109")
snap = json.loads((WD / "_si_scan_out.json").read_text(encoding="utf-8"))

def find_str(obj, needle, results, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            kp = path + "." + str(k)
            if isinstance(v, str) and needle in v:
                results.append((kp, v[:300]))
            elif not isinstance(v, (dict, list)) and needle in str(k):
                results.append((kp, str(v)))
            find_str(v, needle, results, kp)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            find_str(v, needle, results, path + "[" + str(i) + "]")

for dom in ["handoff_pack_20261109", "s604_script_hunt_20261109", "c07_protocol_attacks_20261109",
            "oldwording_sweep_20261109", "s604_verdict_entry_20261109", "counterpart_fix_20261109",
            "d13d14_cards_20261108", "direction_ruling_20261108"]:
    res = []
    find_str(snap, dom, res)
    print("=== " + dom + " : " + str(len(res)) + " hits")
    for p, v in res[:3]:
        print("   " + p)
    for p, v in res[:1]:
        print("   -> " + v[:280])
