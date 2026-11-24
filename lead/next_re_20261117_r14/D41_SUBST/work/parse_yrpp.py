# -*- coding: utf-8 -*-
"""Parse YRpp CALL/JMP_THIS/JMP_STD bindings with file:line; map candidate VAs -> bindings."""
import os, re, json, sys
sys.path.insert(0, os.path.dirname(__file__))
from common import IB

YRPP = r"D:\Project\ra2-campaign-forge\YRpp"
WORK = os.path.dirname(__file__)

bindings = []  # dict: kind, va, file, line, text
pat = re.compile(r'\b(CALL|JMP_THIS|JMP_STD|THISCALL)\s*\(\s*0x([0-9A-Fa-f]+)\s*\)')
for root, dirs, files in os.walk(YRPP):
    for fn in files:
        if not fn.lower().endswith((".h", ".cpp", ".c")):
            continue
        p = os.path.join(root, fn)
        try:
            lines = open(p, encoding="utf-8", errors="replace").read().splitlines()
        except Exception:
            continue
        rel = os.path.relpath(p, r"D:\Project\ra2-campaign-forge")
        for i, line in enumerate(lines, 1):
            for m in pat.finditer(line):
                kind = m.group(1)
                va = int(m.group(2), 16) & 0xffffffff
                bindings.append({"kind": kind, "va": "%08X" % va, "file": rel.replace("\\", "/"),
                                 "line": i, "text": line.strip()[:160]})

with open(os.path.join(WORK, "yrpp_bindings.json"), "w", encoding="utf-8") as fh:
    json.dump(bindings, fh, ensure_ascii=False, indent=1)
print("total bindings parsed:", len(bindings))
from collections import Counter
print("by kind:", dict(Counter(b["kind"] for b in bindings)))

# map candidate VAs
cand = json.load(open(os.path.join(WORK, "cand_scan.json"), encoding="utf-8"))
byva = {}
for b in bindings:
    byva.setdefault(b["va"], []).append(b)
print("\n=== candidate bindings (CALL/JMP_THIS only = channel-1 eligible) ===")
for r in cand:
    if r["vaocc"] != 0:
        continue
    bs = byva.get(r["entry"], [])
    c1 = [b for b in bs if b["kind"] in ("CALL", "JMP_THIS", "THISCALL")]
    js = [b for b in bs if b["kind"] == "JMP_STD"]
    if c1 or js:
        print("%s %-30s c1=%d jmpstd=%d" % (r["entry"], r["name"], len(c1), len(js)))
        for b in c1:
            print("    C1 %s %s:%d  %s" % (b["kind"], b["file"], b["line"], b["text"]))
        for b in js:
            print("    STD %s:%d  %s" % (b["file"], b["line"], b["text"]))
print("\nwrote work/yrpp_bindings.json")
