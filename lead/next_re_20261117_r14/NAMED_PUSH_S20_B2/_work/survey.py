# -*- coding: utf-8 -*-
"""S20-B1 全域初筛（v2）：对 18 行逐行产出
 ① body_end_check；② ring2（虚表枚举，取类名匹配那张）；③ channel_a 机械站点 + 被调返回画像；
 ④ 该虚表的全部立即数安装点（含所在函数/atexit/行内）；direct callers。
产物 survey.json + survey.txt。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

WORK = os.path.dirname(os.path.abspath(__file__))
ROWS = json.load(open(os.path.join(WORK, "b2_rows.json"), encoding="utf-8"))


def survey_row(r):
    e = int(r["entry"], 16)
    size = C.ATLAS.get(r["entry"], {}).get("size") or 0
    a = C.body_end_check(e, size)
    hits = C.ring2(e)
    matched = C.match_vt_for_name(hits, r["name"])
    insns = C.disasm_body(e, size)
    sites = C.channel_a(insns)
    for s in sites:
        if s["callee"]:
            p = C.callee_profile(s["callee"])
            s["callee_profile"] = ({"n_rets": p["n_rets"],
                                    "consts": [C.hx(v) for v in p["consts"]],
                                    "falsifiable": [C.hx(v) for v in p["consts"]
                                                    if C.is_falsifiable(v)],
                                    "n_insn": p["n_insn"]} if p else None)
        else:
            s["callee_profile"] = None
    out = {
        "entry": r["entry"], "name": r["name"], "atlas_size": size,
        "ring1": a,
        "ring2": {"n_hits": len(hits),
                  "hits": [{"vt": C.hx(h["vtable_base"]), "slot_no": h["slot_no"],
                            "slot_va": C.hx(h["slot_va"]), "col": C.hx(h["col"]),
                            "td": C.hx(h["td"]), "rtti": h["rtti"],
                            "n_slots": h["n_slots"], "slot_ok": h["slot_value_ok"]}
                           for h in hits],
                  "matched": [{"vt": C.hx(h["vtable_base"]), "slot_no": h["slot_no"],
                               "slot_va": C.hx(h["slot_va"]), "col": C.hx(h["col"]),
                               "td": C.hx(h["td"]), "rtti": h["rtti"]} for h in matched]},
        "direct_callers": [C.hx(x) for x in C.direct_calls(e)],
        "n_insn": len(insns),
        "sites_3b2": [{"call": C.hx(s["call_addr"]),
                       "callee": C.hx(s["callee"]) if s["callee"] else None,
                       "test": C.hx(s["test_addr"]), "test_kind": s["test_kind"],
                       "imm": s["test_imm"],
                       "jcc": "%s@%s->%s" % (s["jcc"], C.hx(s["jcc_addr"]),
                                             C.hx(s["jcc_target"]) if s["jcc_target"] else "?"),
                       "eax_clobber": s["eax_clobber"], "same_action": s["same_action"],
                       "taken": s["sig_taken"], "fall": s["sig_fall"],
                       "callee_profile": s["callee_profile"]}
                      for s in sites],
    }
    if matched:
        m = matched[0]
        vt = m["vtable_base"]
        r4 = C.ring4(e, vt, m["slot_no"] * 4, size)
        r4["vt"] = C.hx(vt)
        r4["slot_no"] = m["slot_no"]
        r4["rtti"] = m["rtti"]
        out["ring4"] = r4
    else:
        out["ring4"] = None
    return out


res = [survey_row(r) for r in ROWS]
json.dump(res, open(os.path.join(WORK, "survey.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)

lines = []
for s in res:
    lines.append("=" * 104)
    lines.append("ROW %s  %-30s size=%d n_insn=%d" % (s["entry"], s["name"], s["atlas_size"], s["n_insn"]))
    r1 = s["ring1"]
    lines.append("  ① last=%-10s @%s skip=%d cov=%d/%d ok=%s" % (
        r1["last"], C.hx(r1["last_va"]), r1["skipdata"], r1["covered"], s["atlas_size"], r1["ok"]))
    r2 = s["ring2"]
    lines.append("  ② 命中表=%d ；类名匹配:" % r2["n_hits"])
    for h in r2["matched"]:
        lines.append("      vt=%s slot#%-3d slot_va=%s COL=%s TD=%s %s slot_ok" % (
            h["vt"], h["slot_no"], h["slot_va"], h["col"], h["td"], h["rtti"]))
    lines.append("  ③b② 站点=%d direct=%d" % (len(s["sites_3b2"]), len(s["direct_callers"])))
    for t in s["sites_3b2"]:
        cp = t["callee_profile"]
        cps = ("ret=%s consts=%s" % (cp["n_rets"], ",".join(cp["consts"]))) if cp else "OUT/N-A"
        lines.append("      %s call %s | %s@%s | %s | same=%s | %s" % (
            t["call"], t["callee"], t["test_kind"], t["test"], t["jcc"],
            t["same_action"], cps))
    r4 = s["ring4"]
    if r4:
        lines.append("  ④ vt=%s slot#%s %s 行外活安装点=%d" % (
            r4["vt"], r4["slot_no"], r4["rtti"], r4["n_live_outside"]))
        for st in r4["stores"]:
            lines.append("      %s %-30s %s in_func=%s atexit=%s in_self=%s" % (
                C.hx(st["va"]), st["op"], st["bytes"], st["in_func"], st["atexit"], st["in_self"]))
    else:
        lines.append("  ④ N/A")
    lines.append("  direct=%s" % ",".join(s["direct_callers"]))

txt = "\n".join(lines) + "\n"
open(os.path.join(WORK, "survey.txt"), "w", encoding="utf-8").write(txt)
print(txt)
