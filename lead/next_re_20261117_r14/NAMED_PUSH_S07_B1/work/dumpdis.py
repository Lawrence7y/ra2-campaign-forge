# -*- coding: utf-8 -*-
"""Dump full annotated disassembly for selected entries from analysis.json."""
import os, sys, json
WORK = os.path.dirname(os.path.abspath(__file__))
ana = {r["entry"]: r for r in json.load(open(os.path.join(WORK, "analysis.json"), encoding="utf-8"))}
sel = sys.argv[1:] if len(sys.argv) > 1 else list(ana.keys())
for e in sel:
    r = ana[e]
    print("=" * 90)
    print("ENTRY %s  %s  size=%d" % (e, r["hint_name"], r["atlas"].get("size", 0)))
    for ln in r["all_insns"]:
        print("  " + ln)
