# -*- coding: utf-8 -*-
import os, sys, collections
sys.stdout.reconfigure(encoding="utf-8")
PROJ = r"D:\Project\ra2-campaign-forge"
ROOT = os.path.join(PROJ, "lead", "next_re_20261117_r14")
COV = os.path.join(ROOT, "COVERAGE", "coverage.tsv")
DELTA = os.path.join(ROOT, "R16_SLOTN_B1", "delta.tsv")
ATLAS = os.path.join(PROJ, "lead", "next_re_20261112_r10", "W130_atlas", "function_atlas.tsv")

def ne(e):
    e=e.strip().upper()
    if e.startswith("0X"): e=e[2:]
    try: return "%08X"%int(e,16)
    except: return e

cov_lines = open(COV, encoding="utf-8").read().splitlines()
delta_lines = open(DELTA, encoding="utf-8-sig").read().splitlines()
atlas=set()
for i,l in enumerate(open(ATLAS, encoding="utf-8-sig")):
    if i==0: continue
    p=l.rstrip("\r\n").split("\t")
    if p and p[0].strip(): atlas.add(ne(p[0]))

# build cov map (exactly as precheck)
cov_by_entry={}
for ln in cov_lines[1:]:
    c=ln.split("\t")
    if len(c)>=8: cov_by_entry.setdefault(ne(c[0]),[]).append(c)

drows=[l.split("\t") for l in delta_lines[1:]]

# print 15 rows: does before col4 contain ④
print("=== 15 rows before-col4 ④ check ===")
for i,d in enumerate(drows,1):
    e=ne(d[0]); cand=cov_by_entry[e]; cov4=cand[0][3]
    print("ROW %2d %s has字符④=%s has'④ 活表槽位见证'=%s has'④升级句'=%s" % (
        i,e,("④" in cov4),("④ 活表槽位见证" in cov4),("④升级句" in cov4)))

# simulate after: replace col4 for 15 entries
after_map={}
for e,c in cov_by_entry.items():
    after_map[e]=[list(x) for x in c]
for d in drows:
    e=ne(d[0]); after_map[e][0][3]=d[3].replace("R14_COMMON §12.4","R14_COMMON §12.6")

def count(mode):
    before={"含字符④":0,"含见证短语":0,"含升级句":0}
    after={"含字符④":0,"含见证短语":0,"含升级句":0}
    for e,c in cov_by_entry.items():
        if len(c[0])<8: continue
        if c[0][4].strip()!="[已证]": continue
        b=c[0][3]; a=after_map[e][0][3]
        before["含字符④"]+=("④" in b)
        before["含见证短语"]+=("④ 活表槽位见证" in b)
        before["含升级句"]+=("④升级句" in b)
        after["含字符④"]+=("④" in a)
        after["含见证短语"]+=("④ 活表槽位见证" in a)
        after["含升级句"]+=("④升级句" in a)
    return before,after

b,a=count(None)
print("=== counts ===")
print("BEFORE",b)
print("AFTER ",a)
