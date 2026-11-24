#!/usr/bin/env python3
"""W130f: merge the string pass into the function atlas and report coverage.

Also records the 8948 vs 8578 discrepancy explicitly instead of hiding it.
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))


def strip_suffix(ln, marker):
    m = re.search(re.escape(marker) + r" (.*)$", ln)
    txt = m.group(1) if m else ln
    # NOTE: must NOT use \s* -- \s eats TAB and destroys empty trailing columns
    return re.sub(r" *\(GhidraScript\) *$", "", txt)


raw = io.open(os.path.join(HERE, "funcstrings.raw.log"), encoding="utf-8",
              errors="replace").read().splitlines()
meta = []
strs = {}
for ln in raw:
    txt = strip_suffix(ln, "FuncStrings.java>")
    if txt.startswith("###"):
        meta.append(txt)
        continue
    if re.match(r"^[0-9a-f]{8}\t", txt):
        p = txt.split("\t")
        strs[int(p[0], 16)] = (int(p[1]), " | ".join(p[2:]))

print("meta:", meta)
print("functions with string data emitted:", len(strs))
n_with = sum(1 for _k, (n, _s) in strs.items() if n > 0)
print("of which with >=1 string:", n_with)

# ---------- merge ----------
src = os.path.join(HERE, "function_atlas.tsv")
out = os.path.join(HERE, "function_atlas.tsv")
rows = []
hdr = None
with io.open(src, encoding="utf-8") as f:
    for i, line in enumerate(f):
        line = line.rstrip("\n")
        if i == 0:
            hdr = line
            continue
        rows.append(line.split("\t"))

print("\nbase rows:", len(rows))
merged = []
for p in rows:
    entry = int(p[0], 16)
    n_s, s = strs.get(entry, (0, ""))
    merged.append([p[0], p[1], p[2], p[3], p[4], p[5], p[6], str(n_s), s])

with io.open(out, "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_instr\tn_callers\tn_callees\tis_fnptr\tfirst_import"
            "\tn_strings\tstrings\n")
    for m in merged:
        f.write("\t".join(m) + "\n")
print("wrote", out)

with_str = sum(1 for m in merged if int(m[7]) > 0)
print("\n=== merged atlas ===")
print("  functions with >=1 string : %d / %d (%.1f%%)"
      % (with_str, len(merged), 100.0 * with_str / len(merged)))

# ---------- top semantic labels ----------
import collections
c = collections.Counter()
for m in merged:
    for s in m[8].split(" | "):
        if s:
            c[s] += 1
print("\n=== most-referenced strings (top 25) ===")
for s, n in c.most_common(25):
    print("  %4d  %s" % (n, s[:90]))

# ---------- the 8948 vs 8578 gap ----------
print("\n=== function-manager discrepancy (recorded, not resolved) ===")
print("  FunctionManager.getFunctionCount()      = 8948")
print("  functions enumerable via getFunctions() = 8578")
print("  difference                              = 370")
print("  Ghidra reported external=0, thunks=44")
print("  => 370 entries have no enumerable body in the default address space;")
print("     NOT yet explained. Atlas covers 8578 (the enumerable set).")
