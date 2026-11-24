#!/usr/bin/env python3
"""W130h: merge the 40-string pass and re-measure module attribution coverage."""
import collections
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
PAT = re.compile(rb"[A-Za-z]:\\[^\x00\"<>|]{2,120}\.(?:cpp|CPP|c|h|H|hpp)")


def strip_suffix(ln):
    m = re.search(r"FuncStrings\.java> (.*)$", ln)
    txt = m.group(1) if m else ln
    return re.sub(r" *\(GhidraScript\) *$", "", txt)


raw = io.open(os.path.join(HERE, "funcstrings40.raw.log"), encoding="utf-8",
              errors="replace").read().splitlines()
strs = {}
for ln in raw:
    txt = strip_suffix(ln)
    if re.match(r"^[0-9a-f]{8}\t", txt):
        p = txt.split("\t")
        strs[int(p[0], 16)] = (int(p[1]), " | ".join(p[2:]))
print("functions:", len(strs))
print("with >=1 string:", sum(1 for n, _ in strs.values() if n > 0))

# rebuild atlas with the richer strings
rows = []
with io.open(os.path.join(HERE, "function_atlas.tsv"), encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        rows.append(line.rstrip("\n").split("\t"))

merged = []
for p in rows:
    e = int(p[0], 16)
    n_s, s = strs.get(e, (0, ""))
    merged.append([p[0], p[1], p[2], p[3], p[4], p[5], p[6], str(n_s), s])

with io.open(os.path.join(HERE, "function_atlas.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_instr\tn_callers\tn_callees\tis_fnptr\tfirst_import"
            "\tn_strings\tstrings\n")
    for m in merged:
        f.write("\t".join(m) + "\n")
print("rewrote function_atlas.tsv with 40-string cap")

# module attribution
mod_of = {}
mod_counts = collections.Counter()
for m in merged:
    mods = []
    for s in (m[8] or "").split(" | "):
        if not s:
            continue
        mm = PAT.match(s.encode("latin-1"))
        if mm:
            mods.append(mm.group().decode("latin-1"))
    if mods:
        u = sorted(set(mods))
        mod_of[int(m[0], 16)] = u
        for x in u:
            mod_counts[x] += 1

cov = sum(int(m[1]) for m in merged if int(m[0], 16) in mod_of)
tot = sum(int(m[1]) for m in merged)
print("\nfunctions attributable: %d / %d (%.1f%%)"
      % (len(mod_of), len(merged), 100.0 * len(mod_of) / len(merged)))
print("byte coverage        : %d / %d = %.1f%%" % (cov, tot, 100.0 * cov / tot))
print("distinct modules seen: %d" % len(mod_counts))

with io.open(os.path.join(HERE, "module_attribution.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_callers\tmodules\n")
    for m in merged:
        e = int(m[0], 16)
        if e in mod_of:
            f.write("%s\t%s\t%s\t%s\n" % (m[0], m[1], m[3], ",".join(mod_of[e])))
print("wrote module_attribution.tsv")

print("\n=== modules by attributed functions (top 45) ===")
for k, v in mod_counts.most_common(45):
    print("  %4d  %s" % (v, k))
