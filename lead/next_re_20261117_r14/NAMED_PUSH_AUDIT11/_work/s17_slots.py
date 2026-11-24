import sys, json
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

rows = json.load(open("verify3.json", encoding="utf-8"))
name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]

print("### factory vtable slot bodies (row 1: vt 007F3B28)")
for k in range(5):
    fn = u32(0x7F3B28 + 4 * k)
    print(f"-- slot{k} = {fn:08X}")
    for i in list(dis(fn, 60))[:10]:
        print("     " + fmt(i))
    print()

print("### every occurrence of each factory vt imm inside .text (any instruction form)")
for d in rows:
    vt = int(d["vt"], 16)
    needle = vt.to_bytes(4, "little")
    p = blob.find(needle)
    hits = []
    while p >= 0:
        hits.append(sva + p)
        p = blob.find(needle, p + 1)
    print(f"  {d['entry']} vt={d['vt']} .text occurrences={[f'{h:08X}' for h in hits]}")

print()
print("### CLSID imm references inside .text (who consumes the registered CLSIDs)")
for d in rows:
    cid = int(d["clsid"], 16)
    needle = cid.to_bytes(4, "little")
    hits = []
    # text
    p = blob.find(needle)
    while p >= 0:
        hits.append(("text", sva + p))
        p = blob.find(needle, p + 1)
    # data
    for secname in (".data", ".rdata"):
        s = [x for x in SECTIONS if x[0] == secname][0]
        b2 = DATA[s[4]:s[4] + s[3]]
        p = b2.find(needle)
        while p >= 0:
            hits.append((secname, s[1] + p))
            p = b2.find(needle, p + 1)
    print(f"  {d['entry']} {d['expected_class']:<24} CLSID={d['clsid']} refs={[(a, f'{b:08X}') for a, b in hits]}")
