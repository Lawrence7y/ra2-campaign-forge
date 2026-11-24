#!/usr/bin/env python3
"""W150: mine EVIDENCE\\w150_sweep.log PART2/PART2b for state-variable candidates.

PART2b lines look like
  P2BI|<global>|<imm>|<fnEntry>|<insnVA>|<insn text>
PART2 aggregates look like
  P2W|<global>|nfn=N| fn:count fn:count ...
  P2R|<global>|nfn=N| fn:count ...

Outputs, per global that receives immediates:
  - the set of distinct immediate values (sorted)
  - writer functions with subsystem tags (joined from fn_subsystem_canonical.tsv)

A global whose distinct immediate set is small (<= 8 values, all <= 0x40) and whose
writer set is small is a *state variable* -- that is the "current dialog / mode id"
shape we are looking for.  Ranking is by (n_distinct_imm ascending, n_readers descending)
because a state variable is written a few ways and read widely.
"""
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.dirname(HERE)
LOG = os.path.join(CARD, "EVIDENCE", "w150_sweep.log")
SUBS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W131_subsystems\fn_subsystem_canonical.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

subs = {}
for line in open(SUBS, encoding="latin-1"):
    p = line.rstrip("\n").split("\t")
    if len(p) < 4:
        continue
    try:
        subs[int(p[0], 16)] = p[2]
    except ValueError:
        pass

strs = {}
for line in open(ATLAS, encoding="latin-1"):
    p = line.rstrip("\n").split("\t")
    if len(p) < 9:
        continue
    try:
        strs[int(p[0], 16)] = p[8][:70]
    except ValueError:
        pass

imm = defaultdict(lambda: defaultdict(set))     # global -> fn -> {imm}
imm_sites = defaultdict(list)                   # global -> [(imm, fn, va)]
nread = {}
nwrite = {}
rfuncs = {}

with open(LOG, encoding="latin-1", errors="replace") as f:
    for line in f:
        if "P2BI|" in line:
            i = line.index("P2BI|")
            parts = line[i:].strip().split("|")
            if len(parts) < 6:
                continue
            g = int(parts[1], 16)
            v = int(parts[2], 16)
            fn = int(parts[3], 16)
            imm[g][fn].add(v)
            imm_sites[g].append((v, fn, parts[4]))
        elif "P2W|" in line:
            i = line.index("P2W|")
            parts = line[i:].strip().split("|")
            if len(parts) < 4:
                continue
            g = int(parts[1], 16)
            n = re.match(r"nfn=(\d+)", parts[2])
            nwrite[g] = int(n.group(1)) if n else -1
        elif "P2R|" in line:
            i = line.index("P2R|")
            parts = line[i:].strip().split("|")
            if len(parts) < 4:
                continue
            g = int(parts[1], 16)
            n = re.match(r"nfn=(\d+)", parts[2])
            nread[g] = int(n.group(1)) if n else -1
            fs = {}
            for tok in parts[3].split():
                if ":" in tok:
                    a, b = tok.split(":")
                    try:
                        fs[int(a, 16)] = int(b)
                    except ValueError:
                        pass
            rfuncs[g] = fs

# candidate ranking: small distinct immediate value set, all values small
cands = []
for g, fnmap in imm.items():
    vals = set()
    for s in fnmap.values():
        vals |= s
    if not vals:
        continue
    if max(vals) > 0x40:
        continue
    nd = len(vals)
    nr = nread.get(g, 0)
    nw = len(fnmap)
    cands.append((nd, -nr, nw, g, vals))

cands.sort()
print("# rank by (n_distinct_imm asc, n_readers desc); values <= 0x40 only")
print("#global    n_imm  n_wfn  n_rfn   distinct_imms                    subsystem_of_writers / readers")
shown = 0
for nd, negnr, nw, g, vals in cands:
    nr = -negnr
    if nr < 1 and nw < 2:
        continue
    vs = ",".join(f"0x{v:x}" for v in sorted(vals))
    wf = sorted(imm[g].keys())
    wsub = ";".join(sorted({f"{f:08x}:{subs.get(f,'-')}" for f in wf}))[:110]
    rf = sorted(rfuncs.get(g, {}).keys())
    if not rf and not wf:
        continue
    print(f"0x{g:08X}  {nd:5d}  {nw:5d}  {nr:5d}  {vs:30s}  W[{wsub}]")
    shown += 1
    if shown >= 90:
        break

print()
print("# ==== explicit lookups ====")
for g in (0x00A8B238, 0x00A8B24C, 0x00A8B554, 0x00A8B570, 0x00A8DB30, 0x00A8D60E,
          0x00A83D48, 0x00A83D49, 0x00A83D4C, 0x00A83CFC, 0x00A83D22, 0x00A8E9A0,
          0x00A8ED84, 0x00A8ED5D, 0x00A8B8B8, 0x00A83CA8, 0x00A83C9C):
    vals = set()
    for s in imm.get(g, {}).values():
        vals |= s
    print(f"0x{g:08X}: imm_writers={len(imm.get(g,{}))} imms={sorted(vals)} "
          f"n_write_fn={nwrite.get(g,'?')} n_read_fn={nread.get(g,'?')}")
    if g in imm_sites:
        for v, fn, va in sorted(imm_sites[g]):
            print(f"     imm=0x{v:x} @{va} in 0x{fn:08x} ({subs.get(fn,'-')})")
    if g in rfuncs:
        top = sorted(rfuncs[g].items(), key=lambda kv: -kv[1])[:8]
        print("     readers: " + " ".join(f"0x{a:08x}x{b}" for a, b in top))
