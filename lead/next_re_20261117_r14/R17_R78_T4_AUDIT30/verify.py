#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R43-T4 AUDIT30 verification — read-only, computes from on-disk manifests."""
import re, os

BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
A = os.path.join(BASE, "files_tier_A_snap2.tsv")
C = os.path.join(BASE, "files_tier_C.tsv")

def load(p):
    rows=[]
    with open(p, encoding="utf-8") as fh:
        hdr=fh.readline().rstrip("\n").split("\t")
        for line in fh:
            f=line.rstrip("\n").split("\t")
            rows.append((f[0], int(f[2]), f[4] if len(f)>4 else ""))
    return hdr, rows

hA, RA = load(A)
hC, RC = load(C)
setA = {r for r,_,_ in RA}
setC = {r for r,_,_ in RC}
print("A rows/bytes:", len(RA), sum(b for _,b,_ in RA))
print("C rows/bytes:", len(RC), sum(b for _,b,_ in RC))

RX_BAND = re.compile(r"(_before_|\.before|before_|_bak|backup/)", re.I)
RX_WIDE = re.compile(r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)", re.I)

def show(name, rows, rx):
    hit=[(r,b) for r,b,_ in rows if rx.search(r)]
    print(f"  {name}: {len(hit)} / {sum(b for _,b in hit)}")

print("\n-- rollback regexes --")
show("band on A", RA, RX_BAND)
show("band on C", RC, RX_BAND)
show("wide on A", RA, RX_WIDE)
show("wide on C", RC, RX_WIDE)

# lead 375 / 184,618,279 ; auditor 333 / 184,506,382
# Try variations on C to hunt 375
print("\n-- hunt lead 375 on C --")
variants = {
 "band": r"(_before_|\.before|before_|_bak|backup/)",
 "band-noI": r"(_before_|\.before|before_|_bak|backup/)",
 "band+_backup": r"(_before_|\.before|before_|_bak|backup/|_backup)",
 "band+bakword": r"(_before_|\.before|before_|_bak|\bbak\b|backup/)",
 "wide": r"(_before_|\.before|before_|_bak|\bbak\b|backup/|_backup)",
 "before_any": r"(before|bak|backup)",
 "before_bak_backup": r"(before|bak|backup|bad)",
}
for name,pat in variants.items():
    flags = 0 if name=="band-noI" else re.I
    rx=re.compile(pat, flags)
    hit=[(r,b) for r,b,_ in RC if rx.search(r)]
    print(f"  C {name}: {len(hit)} / {sum(b for _,b in hit)}")

# specific families (on A and C)
def base_has(r, sub): return sub in r.rsplit("/",1)[-1].lower()
print("\n-- specific families --")
for label, pred in [
 ("LEDGER.before_*", lambda r: base_has(r,"ledger.before_")),
 ("*_out.txt", lambda r: base_has(r,"_out.txt")),
 ("*_out.json", lambda r: base_has(r,"_out.json")),
 ("stdout/stderr in basename", lambda r: ("stdout" in base_has.__self__ if False else ("stdout" in r.rsplit('/',1)[-1].lower() or "stderr" in r.rsplit('/',1)[-1].lower()))),
 ("REPORT.md exact", lambda r: r.rsplit("/",1)[-1]=="REPORT.md"),
 ("*_report.md", lambda r: r.rsplit("/",1)[-1].lower().endswith("_report.md")),
 ("EVIDENCE dir", lambda r: any(s=="EVIDENCE" for s in r.split("/")[:-1])),
]:
    ha=[(r,b) for r,b,_ in RA if pred(r)]
    hc=[(r,b) for r,b,_ in RC if pred(r)]
    print(f"  {label}: A={len(ha)}/{sum(b for _,b in ha)}  C={len(hc)}/{sum(b for _,b in hc)}")

# 97% / 2.7% drift
print("\n-- drift ratio --")
x, z = 3441605, 95965
print(f"  X/(X+Z)={x/(x+z)*100:.4f}%  Z/(X+Z)={z/(x+z)*100:.4f}%")
print(f"  x+z={x+z}, 3525160+12410={3525160+12410}")
