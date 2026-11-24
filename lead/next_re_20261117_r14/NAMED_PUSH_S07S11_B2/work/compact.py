# -*- coding: utf-8 -*-
"""从 facts.json 生成紧凑决策摘要。"""
import json, os, sys, re
WORK = os.path.dirname(os.path.abspath(__file__))
facts = json.load(open(os.path.join(WORK, "facts.json"), encoding="utf-8"))
CAND = json.load(open(os.path.join(WORK, "candidates.json"), encoding="utf-8"))
ORDER = [r["entry"] for sub in ("S07", "S11") for r in CAND[sub]]

for e in ORDER:
    d = facts[e]
    print("=" * 78)
    print("%s  %-42s text=%s atlas=%s sz=%s insns=%s" %
          (e, d["name"], d["in_text"], d["atlas"], (d["atlas"][1] if d["atlas"] else "?"), d["insn_count"]))
    print("  refs(%d): %s" % (d["dword_ref_count"], d["dword_refs"]))
    for s in d["slots"]:
        print("  SLOT idx=%-2d vt=%s off=%-4s col=%s name=%s" %
              (s["slot_index"], s["vtable"], str(s["col_offset"]), s["col"], s["name"]))
    for ft in d["family_tables"]:
        print("  FAM  vt=%s off=%-4s slot0=%s bytes=%s" %
              (ft["vtable"], str(ft["col_offset"]), ft["slot0"], ft["slot0_bytes"]))
    print("  direct_callers: %s" % d["direct_callers"])
    for st in d["sites"]:
        print("  SITE @%s %s -> callee=%s | %s | %s gap=%s" %
              (st["call"], st["call_op"], st["callee"], st["test_op"], st["jcc_op"], st["gap"]))
    for c, r in d["callee_returns"].items():
        cs = ", ".join("%s=%s[%s]" % (a, v, n[:30]) for a, v, n in r["consts"])
        print("  RET  %s: %s" % (c, cs))
    # installs: 只列 CTOR/DTOR 且落在 [this+0]([esi]/[edi]/[eax]/[ecx]) 的
    nins = len(d["installs"])
    kinds = {}
    for ins in d["installs"]:
        kinds[ins["kind"]] = kinds.get(ins["kind"], 0) + 1
    print("  installs=%d kinds=%s" % (nins, kinds))
    for ins in d["installs"]:
        if ins["kind"] == "CTOR" and re.search(r"\[(esi|edi|eax|ecx|ebx)\]", ins["ins"]):
            print("    CTOR@%s vt=%s off=%s func=%s sz=%s ins=%s" %
                  (ins["site"], ins["vtable"], ins["col_offset"], ins["func"], ins["func_size"], ins["ins"]))
    if d["self_vptr_writes_in_func"]:
        print("  SELF-WRITES(㉓): %s" % d["self_vptr_writes_in_func"])
