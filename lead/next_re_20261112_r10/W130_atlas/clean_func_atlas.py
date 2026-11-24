#!/usr/bin/env python3
"""W130e: clean + validate the function atlas.

Two things to settle:
  1. strip the " (GhidraScript)" suffix the headless log added to every line
  2. explain funcs=8948 vs 8578 printed rows

Validation = spot-check known function sizes against independently established
facts already in the ledger (§834/§838 for 0x724730=385, 0x6F3F40=953,
0x724580=430, and the six hook targets).
"""
import io
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

raw = io.open(os.path.join(HERE, "funcatlas.raw.log"), encoding="utf-8",
              errors="replace").read().splitlines()

rows = []
meta = []
header = None
for ln in raw:
    m = re.search(r"FuncAtlas\.java> (.*)$", ln)
    txt = m.group(1) if m else ln
    # strip ONLY the headless suffix and trailing spaces -- NEVER tabs, because
    # empty trailing columns (no import / no strings) are significant.
    # NOTE: do NOT use \s* here -- \s matches TAB and would eat empty trailing columns
    txt = re.sub(r" *\(GhidraScript\) *$", "", txt)
    if txt.startswith("###"):
        meta.append(txt)
        continue
    if txt.startswith("entry\t"):
        header = txt
        continue
    if re.match(r"^[0-9a-f]{8}\t", txt):
        rows.append(txt)

print("meta:", meta[0] if meta else None)
print("last:", meta[-1] if meta else None)
print("data rows:", len(rows))

# parse
recs = []
bad = 0
for r in rows:
    p = r.split("\t")
    if len(p) < 7:
        bad += 1
        continue
    recs.append({
        "entry": int(p[0], 16), "size": int(p[1]), "n_instr": int(p[2]),
        "n_callers": int(p[3]), "n_callees": int(p[4]), "is_fnptr": int(p[5]),
        "import": p[6], "strings": ("\t".join(p[7:]) if len(p) > 7 else ""),
    })
print("parsed: %d   unparsable: %d" % (len(recs), bad))

out = os.path.join(HERE, "function_atlas.tsv")
with io.open(out, "w", encoding="utf-8") as f:
    f.write("entry\tsize\tn_instr\tn_callers\tn_callees\tis_fnptr\tfirst_import\tstrings\n")
    for r in recs:
        f.write("%08x\t%d\t%d\t%d\t%d\t%d\t%s\t%s\n"
                % (r["entry"], r["size"], r["n_instr"], r["n_callers"],
                   r["n_callees"], r["is_fnptr"], r["import"], r["strings"]))
print("wrote", out)

# ---------------- validation against known facts ----------------
KNOWN = {
    0x00724730: 385,   # ledger §834 / §824-1
    0x00724580: 430,   # ledger §834 (Stubs6)
    0x007241A0: 87,
    0x006F3F40: 953,   # ledger §831 (Fn6F40A2)
    0x006D1660: 270,   # ledger §826
    0x004FC0B0: 1559,  # ledger §826 (Reach20 printed size=1559)
}
by = {r["entry"]: r for r in recs}
print("\n=== spot-check sizes against ledger-stated values ===")
ok = True
for va, want in KNOWN.items():
    got = by.get(va)
    good = got is not None and got["size"] == want
    ok &= good
    print("  0x%08X expect size=%-5d got=%s  %s"
          % (va, want, "Absent" if got is None else got["size"],
             "OK" if good else "MISMATCH"))

# ---------------- stats ----------------
tot = len(recs)
sized = [r for r in recs if r["size"] > 0]
print("\n=== atlas stats ===")
print("  functions           : %d" % tot)
print("  with size>0         : %d" % len(sized))
print("  total bytes         : %d" % sum(r["size"] for r in recs))
print("  appear as fn ptr    : %d" % sum(1 for r in recs if r["is_fnptr"]))
print("  with >=1 caller     : %d" % sum(1 for r in recs if r["n_callers"] > 0))
print("  with 0 callers      : %d (roots or vtable-only)" % sum(1 for r in recs if r["n_callers"] == 0))
print("  with >=1 string     : %d" % sum(1 for r in recs if r["strings"]))
print("  with an import      : %d" % sum(1 for r in recs if r["import"]))
import collections
imp = collections.Counter(r["import"] for r in recs if r["import"])
print("  distinct imports    : %d" % len(imp))
print("  top imports:")
for n, c in imp.most_common(12):
    print("     %-22s %d" % (n, c))

print("\nVALIDATION:", "PASS" if ok else "FAIL")
