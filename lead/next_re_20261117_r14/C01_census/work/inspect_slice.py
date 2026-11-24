"""Inspect C01 slice: data rows 1..1292 of function_atlas.tsv (exclude header)."""
import os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", ".."))
# From work/ up to C01_census -> r14 -> lead -> project root: 5 ups? Let's compute robustly.
here = os.path.dirname(os.path.abspath(__file__))
# scripts live in ...\lead\next_re_20261117_r14\C01_census\work
PROJECT = os.path.abspath(os.path.join(here, "..", "..", "..", ".."))
ATLAS = os.path.join(PROJECT, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")
TAB = chr(9)

def main():
    with open(ATLAS, "r", encoding="utf-8", errors="replace") as f:
        lines = f.read().splitlines()
    hdr = lines[0].split(TAB)
    data = lines[1:]
    sl = data[:1292]
    print("PROJECT", PROJECT)
    print("header:", hdr)
    print("total data rows:", len(data))
    print("slice rows:", len(sl))
    print("first entry:", sl[0].split(TAB)[0], "last entry:", sl[-1].split(TAB)[0])
    entries = [int(r.split(TAB)[0], 16) for r in sl]
    sizes = [int(r.split(TAB)[1]) for r in sl]
    print("min/max entry VA: %08X %08X" % (min(entries), max(entries)))
    print("max end VA: %08X" % max(e+s for e,s in zip(entries,sizes)))
    ns = sum(1 for r in sl if int(r.split(TAB)[7] or 0) > 0)
    fi = sum(1 for r in sl if r.split(TAB)[6].strip())
    nc0 = sum(1 for r in sl if r.split(TAB)[3] == "0")
    print("rows with strings:", ns, "rows with first_import:", fi, "n_callers=0:", nc0)
    # show rows that have strings or imports (evidence candidates)
    for i, r in enumerate(sl, 1):
        p = r.split(TAB)
        if (int(p[7] or 0) > 0) or p[6].strip():
            print("ROW %d | %s | size=%s imp=%s nstr=%s | %s" % (i, p[0], p[1], p[6], p[7], p[8][:120]))

if __name__ == "__main__":
    main()
