#!/usr/bin/env python3
"""W130g: mine Westwood SOURCE FILE names from the binary and attribute functions.

The engine was built with assert() style macros that embed __FILE__, so .rdata
contains strings like `D:\ra2mdpost\\Scenario.CPP`. Those are ground-truth
module labels: a function that references one is (very likely) from that
translation unit.

This produces:
  source_files.tsv      every D:\\ra2mdpost\\* / *.cpp|.h string found in the image
  module_attribution.tsv function -> module(s), with evidence
and prints the module histogram -- the first real subsystem map grounded in
binary evidence rather than address clustering.
"""
import collections
import os
import re

import pefile

HERE = os.path.dirname(os.path.abspath(__file__))
EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

pe = pefile.PE(EXE)
ib = pe.OPTIONAL_HEADER.ImageBase
img = pe.get_memory_mapped_image()

# ---------- 1. all source-file-looking strings anywhere in the image ----------
PAT = re.compile(rb"[A-Za-z]:\\[^\x00\"<>|]{2,120}\.(?:cpp|CPP|c|h|H|hpp)")
seen = collections.OrderedDict()
for m in PAT.finditer(img):
    s = m.group().decode("latin-1")
    if s not in seen:
        seen[s] = m.start() + ib
print("source-file strings in image: %d" % len(seen))

by_dir = collections.Counter()
for s in seen:
    d = s.rsplit("\\", 1)[0]
    by_dir[d] += 1
print("\n=== by directory ===")
for d, n in by_dir.most_common(12):
    print("  %-46s %d" % (d[:46], n))

with open(os.path.join(HERE, "source_files.tsv"), "w", encoding="utf-8") as f:
    f.write("string_va\tsource_file\n")
    for s, va in sorted(seen.items(), key=lambda kv: kv[1]):
        f.write("0x%08X\t%s\n" % (va, s))
print("\nwrote source_files.tsv")

# ---------- 2. attribute functions via the atlas' string column ----------
rows = []
with open(os.path.join(HERE, "function_atlas.tsv"), encoding="utf-8") as f:
    hdr = f.readline().rstrip("\n").split("\t")
    for line in f:
        rows.append(dict(zip(hdr, line.rstrip("\n").split("\t"))))
print("\natlas rows: %d" % len(rows))

mod_of_func = {}
mod_counts = collections.Counter()
for r in rows:
    mods = []
    for s in (r.get("strings") or "").split(" | "):
        m = PAT.match(s.encode("latin-1")) if s else None
        if m:
            mods.append(m.group().decode("latin-1"))
    if mods:
        uniq = sorted(set(mods))
        mod_of_func[int(r["entry"], 16)] = uniq
        for u in uniq:
            mod_counts[u] += 1

print("functions attributable to a source module: %d" % len(mod_of_func))

with open(os.path.join(HERE, "module_attribution.tsv"), "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_callers\tmodules\n")
    for r in rows:
        e = int(r["entry"], 16)
        if e in mod_of_func:
            f.write("%s\t%s\t%s\t%s\n" % (r["entry"], r["size"], r["n_callers"],
                                          ",".join(mod_of_func[e])))
print("wrote module_attribution.tsv")

print("\n=== top modules by attributed function count ===")
for m, n in mod_counts.most_common(40):
    print("  %4d  %s" % (n, m))

# ---------- 3. how much of the code do those cover? ----------
cov = sum(int(r["size"]) for r in rows if int(r["entry"], 16) in mod_of_func)
tot = sum(int(r["size"]) for r in rows)
print("\ncoverage: %d / %d bytes = %.1f%% of enumerated code"
      % (cov, tot, 100.0 * cov / tot))
print("NOTE: only functions whose *first 4* strings include a source path are")
print("      attributed; raising the string cap would raise coverage.")
