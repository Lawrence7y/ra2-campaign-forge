# -*- coding: utf-8 -*-
"""S05 B2 通用 RTTI/虚表解析：对每行 entry 在非 .text 段找它作为 4B VA 的槽引用，
扩展回扫(kmax=600) 找 COL(sig=0)->TD->名串，算 vtable_base / slot_off / slot#，
并与名字线索槽号比对。输出 resolve_out.txt 且落 rtti_map.json。"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import recore as R
from witness_core import u32, parse_col, parse_td, find_dword_refs

WORK = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))

def resolve_slot_ext(refva, kmax=600):
    for k in range(0, kmax + 1):
        vb = refva - 4 * k
        c = u32(vb - 4)
        if not c:
            continue
        ci = parse_col(c)
        if not ci or ci["sig"] != 0:
            continue
        tdi = parse_td(ci["td"])
        if tdi and tdi["name"] and ".?AV" in tdi["name"]:
            return {"vtable_base": vb, "slot_off": 4 * k, "col": ci["col"],
                    "td": ci["td"], "name_va": tdi["name_va"], "rtti_name": tdi["name"]}
    return None

def clue_class(name):
    # 名字 "BuildingClass::slot282" -> "BuildingClass"
    return name.split("::")[0] if "::" in name else None

def clue_slot(name):
    m = re.search(r"(?:v?slot)(\d+)$", name)
    return int(m.group(1)) if m else None

rtti_map = {}
lines = []
for row in rows:
    e = row["entry"]
    ea = int(e, 16)
    cs = clue_slot(row["name"])
    cc = clue_class(row["name"])
    refs = find_dword_refs(ea)
    lines.append("=" * 96)
    lines.append("%s  %-32s clue_slot=%s  dword refs(non-text)=%s" % (
        e, row["name"], cs, ["%08X@%s" % (v, s) for v, s in refs]))
    best = None
    for refva, sec in refs:
        ext = resolve_slot_ext(refva)
        if not ext:
            lines.append("  ref=%08X[%s]: no COL in kmax=600" % (refva, sec))
            continue
        off = ext["slot_off"]
        slotno = off // 4
        tag = ""
        if cs is not None and slotno == cs:
            tag = "  <<< MATCH clue slot"
        lines.append("  ref=%08X[%s]: vt=%08X off=%d slot#=%d col=%08X td=%08X name=%s%s" % (
            refva, sec, ext["vtable_base"], off, slotno, ext["col"], ext["td"],
            ext["rtti_name"], tag))
        cand = dict(ext)
        cand["slot_va"] = "%08X" % refva
        cand["slot_off"] = off
        cand["slotno"] = slotno
        cand["section"] = sec
        cand["clue_slot"] = cs
        cand["clue_class"] = cc
        name_match = (cc is not None and cc in ext["rtti_name"])
        cand["class_match"] = name_match
        cand["match"] = (cs is not None and slotno == cs and name_match)
        # 优先级：类名+槽号都匹配 > 槽号匹配但类名不符 > 任一
        if cand["match"] or (best is None) or (best and not best.get("match") and slotno == cs):
            best = cand
    rtti_map[e] = best
    if best:
        lines.append("  BEST: vt=%08X slot_va=%s slot#=%d col=%08X td=%08X name=%s match=%s" % (
            best["vtable_base"], best["slot_va"], best["slotno"], best["col"],
            best["td"], best["rtti_name"], best["match"]))
    else:
        lines.append("  BEST: NONE (② 无法钉死)")

txt = "\n".join(lines) + "\n"
with open(os.path.join(WORK, "resolve_out.txt"), "w", encoding="utf-8") as f:
    f.write(txt)
with open(os.path.join(WORK, "rtti_map.json"), "w", encoding="utf-8") as f:
    json.dump(rtti_map, f, ensure_ascii=False, indent=1)
print(txt)
print("wrote resolve_out.txt and rtti_map.json")
