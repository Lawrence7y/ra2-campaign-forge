# M4 independent analysis (read-only) — gathers all baseline + verification data
import os, collections, bisect

R14 = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14"
COV = os.path.join(R14, "COVERAGE", "coverage.tsv")
PROBE = os.path.join(R14, "COVERAGE", "probe_and_data_entries.tsv")
PENDING = os.path.join(R14, "COVERAGE", "PENDING_CORRECTIONS.tsv")
UNS = os.path.join(R14, "COVERAGE", "UNSOURCED_PROVED.tsv")
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
Y = "[\u5df2\u8bc1]"
S = "[\u9759\u6001\u63a8\u65ad]"
W = "[\u672a\u8bc1]"

def rows(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        d = f.read().split("\n")
    d = [l[:-1] if l.endswith("\r") else l for l in d]
    if d and d[-1] == "": d.pop()
    return d

cov = [l.split("\t") for l in rows(COV)[1:]]
probe = [l.split("\t") for l in rows(PROBE)[1:]]
pending = [l.split("\t") for l in rows(PENDING)[1:]]
uns = [l.split("\t") for l in rows(UNS)[1:]]

print("== BASELINE ==")
print("coverage data rows:", len(cov))
print("grade dist:", dict(collections.Counter(r[4] for r in cov)))
print("probe data rows:", len(probe))
print("pending data rows:", len(pending))
print("unsourced data rows:", len(uns))

# atlas function bodies
at = []
for l in rows(ATLAS)[1:]:
    f = l.split("\t")
    at.append((int(f[0],16), int(f[1])))
at.sort()
starts = [a[0] for a in at]

def containing(addr):
    i = bisect.bisect_right(starts, addr) - 1
    if i >= 0:
        s, sz = at[i]
        if s <= addr < s+sz:
            return (hex(s), sz, addr-s)
    return None

by = {r[0].lower(): r for r in cov}
pe = {r[0].lower(): r for r in probe}

TARGETS = ["0043f2ae","0043f218","0043f678","0047c878","005684b1"]
print("\n== TASK1: 5 non-function entries verification ==")
for a in TARGETS:
    r = by.get(a)
    c = containing(int(a,16))
    print(f"  {a.upper()}: coverage={r} | containing={c}")

print("\n== TASK2: probe ∩ coverage ==")
for e in sorted(set(pe) & set(by)):
    p, c = pe[e], by[e]
    print(f"  {e}: probe kind={p[1]} grade={p[4]} card={p[6]} | coverage sub={c[1]} name={c[2]} grade={c[4]}")

# per-S recompute from coverage ∩ atlas, grouped by coverage subsystem
atlas_e = set(l.split("\t")[0].lower() for l in rows(ATLAS)[1:])
def is_L(n): return n != "" and not n.startswith("sub_")
def is_S(n): return is_L(n) and "::sub_" not in n

perS = {}
for r in cov:
    if r[0].lower() not in atlas_e: continue
    d = perS.setdefault(r[1], {"n":0,"L":0,"Sc":0,"P":0})
    d["n"] += 1
    if is_L(r[2]): d["L"] += 1
    if is_S(r[2]): d["Sc"] += 1
    if r[4] == Y: d["P"] += 1

print("\n== TASK4: per-S recompute (coverage ∩ atlas, grouped by coverage subsystem) ==")
print("S\tn(atlas_n)\tnamedL\tnamedS\tproved\tpctL\tpctS\tpctP")
tot = {"n":0,"L":0,"Sc":0,"P":0}
for s in sorted(perS):
    d = perS[s]
    for k in tot: tot[k]+=d[k]
    print(f"{s}\t{d['n']}\t{d['L']}\t{d['Sc']}\t{d['P']}\t{d['L']/d['n']*100:.2f}\t{d['Sc']/d['n']*100:.2f}\t{d['P']/d['n']*100:.2f}")
print(f"TOTAL\t{tot['n']}\t{tot['L']}\t{tot['Sc']}\t{tot['P']}\t{tot['L']/tot['n']*100:.2f}\t{tot['Sc']/tot['n']*100:.2f}\t{tot['P']/tot['n']*100:.2f}")

# atlas grouped by atlas's OWN subsystem (atlas has no sub column! only entry,size,...)
# so atlas_n MUST come from coverage's sub field joined on atlas membership - confirmed

print("\n== TASK3: UNSOURCED reason phrase count ==")
cnt = sum(1 for r in uns if "任何 delta 均未断言 [已证]" in r[4])
print("rows containing phrase:", cnt, "of", len(uns))

print("\n== TASK5: W177-C nonstandard tokens + evidence existence ==")
import re
std = {Y,S,W}
wc = os.path.join(R14, "W177-C", "coverage_delta.tsv")
nonstd = []
for i, l in enumerate(rows(wc)[1:], start=2):
    f = l.split("\t")
    if len(f)>=5 and f[4].startswith("[") and f[4].endswith("]") and f[4] not in std:
        nonstd.append((i,f))
mapping = {"[已证·复用]":Y, "[已证读数]":Y, "[已证·观测]":Y, "[未证·未调用]":W, "[推断·可观测]":S}
for i,f in nonstd:
    ev = f[5]
    full = os.path.join(R14,"W177-C",ev.replace("\\","/"))
    exists = os.path.isfile(full)
    mapped = mapping.get(f[4], "???")
    if mapped==Y and not exists: mapped2 = W  # downgrade if evidence missing
    else: mapped2 = mapped
    print(f"  L{i} {f[0]:>10} tok={f[4]:<12} ev={ev:<40} exists={exists} -> {mapped2}")
print("nonstd count:", len(nonstd))
print("token dist:", dict(collections.Counter(f[4] for i,f in nonstd)))
