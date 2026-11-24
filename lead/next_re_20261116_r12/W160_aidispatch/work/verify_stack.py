import json, os
R=r"D:\Project\ra2-campaign-forge\lead\next_re_20261116_r12\W160_aidispatch\EVIDENCE"
r=json.load(open(os.path.join(R,"W160_Q1_channelA.json"),encoding="utf-8"))
addrs=[int(x["va"],16) for x in r["call_sites"]]
for lo,hi in [(0x55AFB0,0x55B720),(0x55B8F0,0x55BAA0),(0x617600,0x617700),(0x61CC00,0x61CC80),(0x785100,0x785350)]:
    xs=[hex(a) for a in addrs if lo<=a<hi]
    print(f"[{lo:06X},{hi:06X}) n={len(xs)}: {xs}")

# list disasm lines around critical areas
lines=open(os.path.join(R,"W160_whole_text_disasm.tsv"),encoding="utf-8").read().splitlines()
D={int(l.split('\t')[0],16):l for l in lines}
for lo,hi in [(0x55DC80,0x55DCB0),(0x55AFB0,0x55B010),(0x55B5E0,0x55B660),(0x40CB80,0x40CC20),(0x785100,0x785350)]:
    print(f"\n--- {lo:08X}..{hi:08X} ---")
    for a in sorted(k for k in D if lo<=k<hi):
        print(D[a])
