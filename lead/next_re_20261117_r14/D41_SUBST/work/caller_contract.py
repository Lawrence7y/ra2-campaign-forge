# -*- coding: utf-8 -*-
"""For each no-vtable candidate: find direct call sites, map to caller functions (via atlas),
   and report caller coverage grades. Determines channel-2 eligibility."""
import os, json, sys, struct
sys.path.insert(0, os.path.dirname(__file__))
from common import DATA, IB, SECS, find_dword, md32, va2off, where_va
from capstone.x86 import X86_OP_IMM

WORK = os.path.dirname(__file__)
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"

# load atlas: entry+size sorted
atlas = []
for line in open(ATLAS, encoding="utf-8", errors="replace"):
    f = line.rstrip("\n").split("\t")
    if len(f) < 2 or f[0] == "entry":
        continue
    try:
        atlas.append((int(f[0], 16), int(f[1])))
    except ValueError:
        pass
atlas.sort()

def caller_of(site_va):
    # find atlas function whose [entry, entry+size) contains site
    lo, hi = 0, len(atlas) - 1
    best = None
    # linear ok (12k) but do binary by entry
    while lo <= hi:
        mid = (lo + hi) // 2
        e, sz = atlas[mid]
        if e <= site_va:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if best is not None:
        e, sz = atlas[best]
        if e <= site_va < e + sz:
            return e
    return None

# coverage grade/name by entry
cov = {}
for line in open(COV, encoding="utf-8", errors="replace"):
    f = line.rstrip("\n").split("\t")
    if len(f) < 5 or f[0] == "entry":
        continue
    cov[f[0].upper()] = (f[1], f[4], f[2])  # subsystem, grade, name

# full text direct call sweep
text = [s for s in SECS if s[0] == ".text"][0]
name, tva, tvs, trs, tra = text
blob = DATA[tra:tra+trs]
md = md32()
direct_targets = {}
for ins in md.disasm(blob, IB + tva):
    if ins.mnemonic == "call" and ins.bytes and ins.bytes[0] == 0xE8 and ins.operands and ins.operands[0].type == X86_OP_IMM:
        tgt = ins.operands[0].imm & 0xffffffff
        direct_targets.setdefault(tgt, []).append(ins.address)

cand = json.load(open(os.path.join(WORK, "cand_scan.json"), encoding="utf-8"))
res = []
for r in cand:
    if r["vaocc"] != 0:
        continue
    va = int(r["entry"], 16)
    sites = direct_targets.get(va, [])
    callers = []
    for s in sites:
        ce = caller_of(s)
        if ce is None:
            callers.append({"site": "%08X" % s, "caller": None, "grade": None, "name": None})
        else:
            key = "%08X" % ce
            info = cov.get(key, (None, None, None))
            callers.append({"site": "%08X" % s, "caller": key, "sub": info[0], "grade": info[1], "name": info[2]})
    proven = [c for c in callers if c["grade"] == "[已证]"]
    r2 = dict(r)
    r2["callers"] = callers
    r2["proven_caller_set"] = sorted(set(c["caller"] for c in proven))
    r2["proven_caller_n"] = len(r2["proven_caller_set"])
    res.append(r2)

with open(os.path.join(WORK, "caller_contract.json"), "w", encoding="utf-8") as fh:
    json.dump(res, fh, ensure_ascii=False, indent=1)

for sub in ("S02", "S19"):
    print("=== %s no-vtable candidates: channel-2 (proven callers>=2) ===" % sub)
    for r in res:
        if r["sub"] != sub:
            continue
        if r["proven_caller_n"] >= 2:
            print("  %s %-28s proven=%d %s" % (r["entry"], r["name"], r["proven_caller_n"], ",".join(r["proven_caller_set"][:8])))
    print("  --- all %s no-vtable with proven counts ---" % sub)
    for r in res:
        if r["sub"] == sub:
            print("   %s %-28s direct=%d proven=%d" % (r["entry"], r["name"], r["direct_n"], r["proven_caller_n"]))
print("wrote work/caller_contract.json")
