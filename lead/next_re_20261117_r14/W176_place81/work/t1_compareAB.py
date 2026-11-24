import json, capstone, os
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W176_place81\EVIDENCE"
A = json.load(open(os.path.join(OUT, "T1_byte81_all.json"), encoding="utf-8"))["hits"]
aset = {x["va"] for x in A}
B = []
for line in open(os.path.join(OUT, "T1_byte81_channelB_addrs.txt"), encoding="utf-8"):
    p = line.split(None, 1)
    B.append((int(p[0], 16), p[1].strip()))
bset = {va for va, _ in B}
print("A", len(aset), "B", len(bset), "A∩B", len(aset & bset), "onlyB", len(bset-aset), "onlyA", len(aset-bset))
print("onlyB sample:")
for va, text in B:
    if va not in aset:
        print(" ", hex(va), text)
