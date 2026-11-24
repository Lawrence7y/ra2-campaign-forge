#!/usr/bin/env python3
"""Print census addresses/classes, examine duplicates, reconcile with C08 (9) / C09 (15)."""
import json, os
D = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\N_FIX\EVIDENCE"
data = json.load(open(os.path.join(D,'census_detailed.json'),encoding='utf-8'))
census = data['census']

from collections import defaultdict
byaddr = defaultdict(list)
for c in census:
    byaddr[c['addr']].append(c)

print("=== ALL 99 census instances ===")
for c in sorted(census, key=lambda x:(x['addr'],x['file'])):
    print(f"0x{c['addr']:08X} | real={c['real_cls']:<28} | deleg={c['deleg_cls']:<26} | {c['misjudged_name']:<36} | {c['file']}:{c['noinit_line']} | sig={c['sig_text'][:55]}")

print("\n=== DUPLICATE ADDRESSES ===")
for a,items in byaddr.items():
    if len(items)>1:
        print(f"0x{a:08X}:")
        for c in items:
            print(f"    {c['file']}:{c['noinit_line']} deleg={c['deleg_cls']} real_cls={c['real_cls']} sig={c['sig_text'][:55]}")

c08 = [0x6CAF90,0x6CE5B0,0x6E4DE0,0x6E7E80,0x6E8A90,0x6F06E0,0x6F2B40,0x710AF0,0x718000]
c09 = [0x71A4E0,0x71BB90,0x71DA80,0x71E6A0,0x7216C0,0x725FA0,0x726C80,0x7353C0,0x7470D0,0x7493B0,0x74AD80,0x75CEC0,0x75E950,0x763810,0x771C70]
addrset = set(byaddr)
print("\n=== RECONCILE C08 (9) ===")
for a in c08:
    print(f"  0x{a:08X} in census={a in addrset}")
print("C08 all present:", all(a in addrset for a in c08))
print("\n=== RECONCILE C09 (15) ===")
for a in c09:
    print(f"  0x{a:08X} in census={a in addrset}")
print("C09 all present:", all(a in addrset for a in c09))
