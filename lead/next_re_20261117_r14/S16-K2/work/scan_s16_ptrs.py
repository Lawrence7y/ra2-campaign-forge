#!/usr/bin/env python3
"""S16-K2: scan all .rdata/.data for pointers to S16 addresses; identify vtable slots."""
import sys, os, struct, csv, collections
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S16-K2\work")
import re_lib as R

ROOT = r"D:\Project\ra2-campaign-forge"
b = R.Bin()

# load S16 rows from coverage
cov = list(csv.DictReader(open(os.path.join(ROOT, r"lead\next_re_20261117_r14\COVERAGE\coverage.tsv"), encoding="utf-8"), delimiter="\t"))
s16 = [r for r in cov if r["subsystem"].strip()=="S16"]
addr_to_row = {int(r["entry"],16): r for r in s16}
s16addrs = set(addr_to_row)

# scan .rdata and .data for 4-byte pointers to S16 addresses
ptrs = collections.defaultdict(list)  # target -> [ptr_location]
for secname in (".rdata", ".data"):
    s = b.sec(secname)
    buf = b.data[s['raw']:s['raw']+s['rawsize']]
    for i in range(0, len(buf)-3, 4):
        val = struct.unpack_from('<I', buf, i)[0]
        if val in s16addrs:
            ptrs[val].append((s['va']+i, secname))

print("== pointers to S16 addresses in .rdata/.data ==")
for va in sorted(ptrs):
    row = addr_to_row[va]
    locs = ptrs[va]
    print(f"{va:08X}\t{row['name'][:50]:<50}\t" + ", ".join(f"{loc:08X}({sec})" for loc,sec in locs))

# Also collect all pointers to ANY code address in .text to find vtable boundaries
# For each S16 ptr location, read surrounding slots
print("\n== S16 pointer locations with surrounding 8 slots (vtable context) ==")
for va in sorted(ptrs):
    for loc, sec in ptrs[va]:
        row = addr_to_row[va]
        slots=[]
        for k in range(-4,5):
            p = loc+4*k
            try: val=b.u32(p)
            except Exception: val=0
            tag = ""
            if val in s16addrs: tag="*S16"
            elif 0x401000<=val<0x7e1000: tag="CODE"
            elif val==0: tag="zero"
            else: tag="data"
            slots.append(f"{k:+d}:{val:08X}{tag}")
        print(f"\ntarget {va:08X} ({row['name'][:40]}) @ {loc:08X} {sec}")
        print("  " + "  ".join(slots))
