# -*- coding: utf-8 -*-
"""W101 step9: build report tables from census CSV (read-only)."""
import csv, hashlib, json, os
from collections import defaultdict

OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"
GAME = r"D:\Project\ra2-campaign-forge\ra2youli"
rows = list(csv.DictReader(open(os.path.join(OUTD, "mix_census_entries.csv"), encoding="utf-8")))
PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

P("== per-mix top-level summary ==")
top = defaultdict(list)
for r in rows:
    if r["depth"] == "0":
        top[r["mix"]].append(r)
for mix in sorted(top):
    ents = top[mix]
    kinds = defaultdict(int)
    for r in ents: kinds[r["kind"]] += 1
    named = sum(1 for r in ents if r["names"])
    P(f"{mix:16s} top_entries={len(ents):5d} named={named:4d} kinds={dict(kinds)}")

P("")
P("== expandmd01.mix all 33 entries ==")
for r in top["expandmd01.mix"]:
    P(f"  {r['id']} size={int(r['size']):>9d} kind={r['kind']:6s} names={r['names'] or '-'}")

P("")
P("== ra2md.mix top-level (25) ==")
for r in top["ra2md.mix"]:
    P(f"  {r['id']} size={int(r['size']):>9d} kind={r['kind']:6s} names={r['names'] or '-'}")

P("")
P("== ra2.mix top-level (21) ==")
for r in top["ra2.mix"]:
    P(f"  {r['id']} size={int(r['size']):>9d} kind={r['kind']:6s} names={r['names'] or '-'}")

P("")
P("== LOCALMD.MIX (ra2md:FBE0D09D) INI/named entries ==")
for r in rows:
    if r["path"] == "FBE0D09D" and (r["names"] or r["kind"] in ("ini", "text?", "csf")):
        P(f"  {r['id']} size={int(r['size']):>8d} kind={r['kind']:6s} names={r['names'] or '-'}"
          + (f" markers={r['markers']}" if r["markers"] else ""))

P("")
P("== LOCAL.MIX (ra2:A8548FD9) INI/named entries ==")
for r in rows:
    if r["path"] == "A8548FD9" and (r["names"] or r["kind"] in ("ini", "text?", "csf")):
        P(f"  {r['id']} size={int(r['size']):>8d} kind={r['kind']:6s} names={r['names'] or '-'}"
          + (f" markers={r['markers']}" if r["markers"] else ""))

P("")
P("== art/rules-class INI entries across ALL mixes (Foundation/Image markers) ==")
for r in rows:
    m = r.get("markers") or ""
    if "Foundation=" in m or "Image=" in m and int(r["size"]) > 100000:
        P(f"  {r['mix']}:{r['path']}/{r['id']} size={int(r['size']):>9d} names={r['names'] or '-'} markers={m}")

P("")
P("== loose BATTLEMD.INI vs submix copy ==")
a = open(os.path.join(GAME, "BATTLEMD.INI"), "rb").read()
P("loose  BATTLEMD.INI:", len(a), "B sha256=", hashlib.sha256(a).hexdigest())
for r in rows:
    if r["id"] == "07E280DD":
        P(f"mix entry 07E280DD @ {r['mix']}:{r['path']} size={r['size']}")

P("")
P("== RA2MD.INI first 300 chars (options file proof) ==")
head = open(os.path.join(GAME, "RA2MD.INI"), "rb").read(300).decode("ascii", "replace")
P(head.replace("\r", ""))

open(os.path.join(OUTD, "step9_tables.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step9_tables.txt"))
