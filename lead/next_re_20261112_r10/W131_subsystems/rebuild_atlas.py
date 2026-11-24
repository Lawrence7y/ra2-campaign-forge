#!/usr/bin/env python3
"""W131d: rebuild the COMPLETE function atlas (after adding vtable-target functions)
and report the before/after delta.

Inputs : funcatlas2.raw.log (sizes/callers/imports) + funcstrings_new.raw.log (strings)
Output : function_atlas.tsv (overwritten, complete) + atlas_delta.log
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(os.path.dirname(HERE), "W130_atlas")


def strip_sfx(ln, marker):
    m = re.search(re.escape(marker) + r" (.*)$", ln)
    txt = m.group(1) if m else ln
    # never use \s* here: it eats TAB and destroys empty trailing columns
    return re.sub(r" *\(GhidraScript\) *$", "", txt)


def parse(path, marker):
    rows = []
    meta = []
    for ln in io.open(path, encoding="utf-8", errors="replace").read().splitlines():
        t = strip_sfx(ln, marker)
        if t.startswith("###"):
            meta.append(t)
            continue
        if re.match(r"^[0-9a-f]{8}\t", t):
            rows.append(t.split("\t"))
    return rows, meta


base, meta1 = parse(os.path.join(ATLAS, "funcatlas2.raw.log"), "FuncAtlas.java>")
strs, meta2 = parse(os.path.join(ATLAS, "funcstrings_new.raw.log"), "FuncStrings.java>")
print("pack1:", meta1[0] if meta1 else None, "|", meta1[-1] if meta1 else None)
print("pack2:", meta2[0] if meta2 else None, "|", meta2[-1] if meta2 else None)
print("base rows:", len(base), " string rows:", len(strs))

smap = {}
for p in strs:
    smap[int(p[0], 16)] = (int(p[1]), " | ".join(p[2:]) if len(p) > 2 else "")

out = os.path.join(ATLAS, "function_atlas.tsv")
n = 0
with io.open(out, "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_instr\tn_callers\tn_callees\tis_fnptr\tfirst_import"
            "\tn_strings\tstrings\n")
    for p in base:
        entry = int(p[0], 16)
        ns, s = smap.get(entry, (0, ""))
        f.write("%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n"
                % (p[0], p[1], p[2], p[3], p[4], p[5], p[6], ns, s))
        n += 1
print("wrote", out, "rows:", n)

# delta vs the previous (incomplete) atlas numbers recorded in ledger §847
tot_bytes = sum(int(p[1]) for p in base)
with_str = sum(1 for p in base if smap.get(int(p[0], 16), (0, ""))[0] > 0)
with_imp = sum(1 for p in base if p[6])
fnptr = sum(1 for p in base if p[5] == "1")
print("\n=== complete atlas stats ===")
print("  functions (enumerable) : %d   (was 8578)" % len(base))
print("  total code bytes       : %d   (was 2589221)" % tot_bytes)
print("  appears as fn pointer  : %d   (was 1966)" % fnptr)
print("  with >=1 string        : %d" % with_str)
print("  with an import         : %d   (was 754)" % with_imp)
print("  .text coverage         : %.1f%% of 4060045 bytes"
      % (100.0 * tot_bytes / 4060045))
