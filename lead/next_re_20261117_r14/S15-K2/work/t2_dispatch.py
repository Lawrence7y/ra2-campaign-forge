#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Extract S15 dispatch tables from raw bytes and cross-reference with S15 sub_ rows.
Byte channel independent of function_atlas. Uses audit_lib.Bin (capstone skipdata only for sweep).
"""
import sys, os, csv, re, struct
ROOT = r"D:\Project\ra2-campaign-forge"
sys.path.insert(0, os.path.join(ROOT, r"lead\next_re_20261116_r12\_lead_audit"))
import audit_lib as A

COV = os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv")
CARD = os.path.join(ROOT, r"lead\next_re_20261117_r14\S15-K2")
b = A.Bin()

def norm(e): return e.strip().upper().zfill(8)

def read_s15():
    with open(COV,"r",encoding="utf-8-sig",newline="") as f:
        return [r for r in csv.DictReader(f,delimiter="\t") if r["subsystem"].strip()=="S15"]

s15 = read_s15()
sub_rows = {norm(r["entry"]):r for r in s15 if r["name"].strip().startswith("sub_")}
all_s15 = {norm(r["entry"]):r for r in s15}

# --- dispatch tables (absolute dword arrays) ---
tables = {
    "ACTION_145": (0x6DFDEC, 145),
    "TEAM_65":    (0x6E9F74, 65),
    "EVENT_L1_12":(0x71F218, 12),
    "EVENT_L2_2": (0x71F27C, 2),
    "EVENT_L3_14":(0x71F2C0, 14),
    "EVENT_L4_10":(0x71F328, 10),
}
target_owner = {}  # VA -> list of table names
lines = []
for tname,(base,n) in tables.items():
    vals=[b.u32(base+4*i) for i in range(n)]
    intext=sum(1 for v in vals if 0x401000<=v<0x7E1000)
    uniq=len(set(vals))
    lines.append(f"{tname}: base={base:#x} n={n} in_text={intext}/{n} unique={uniq}")
    for v in vals:
        target_owner.setdefault(v, []).append(tname)

# --- cross-reference S15 sub_ rows with dispatch targets ---
print("\n".join(lines))
print("\n=== S15 sub_ rows that are dispatch-table targets ===")
hits=[]
for e,r in sorted(sub_rows.items()):
    va=int(e,16)
    own=target_owner.get(va,[])
    if own:
        hits.append((e,own,r["one_line_semantics"],r["grade"]))
        print(f"  {e}  tables={own}  grade={r['grade']}")
print(f"  total sub_ rows hitting a dispatch table = {len(hits)} / {len(sub_rows)}")

# --- all S15 rows (incl slot) that are dispatch targets ---
print("\n=== ALL S15 rows that are dispatch-table targets ===")
allhits=[]
for e,r in sorted(all_s15.items()):
    va=int(e,16); own=target_owner.get(va,[])
    if own:
        allhits.append((e,own,r["name"],r["grade"]))
        print(f"  {e} {r['name']:<40} {r['grade']} {own}")
print(f"  total = {len(allhits)}")

# save
with open(os.path.join(CARD,"EVIDENCE","T2_dispatch_tables.txt"),"w",encoding="utf-8") as f:
    f.write("\n".join(lines)+"\n\n")
    f.write("=== S15 sub_ rows hitting dispatch tables ===\n")
    for e,own,sem,g in hits: f.write(f"{e}\t{','.join(own)}\t{g}\t{sem}\n")
    f.write("\n=== ALL S15 rows hitting dispatch tables ===\n")
    for e,own,nm,g in allhits: f.write(f"{e}\t{nm}\t{g}\t{','.join(own)}\n")
    f.write("\n=== raw table dwords ===\n")
    for tname,(base,n) in tables.items():
        vals=[b.u32(base+4*i) for i in range(n)]
        f.write(f"{tname} base={base:#x}\n")
        for i,v in enumerate(vals): f.write(f"  [{i:3d}] {v:#010x}\n")
print("\nWrote EVIDENCE/T2_dispatch_tables.txt")
