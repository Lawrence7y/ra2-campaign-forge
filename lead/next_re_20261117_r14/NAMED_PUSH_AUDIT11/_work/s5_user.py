import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]

def refs(val):
    out = []
    needle = val.to_bytes(4, "little")
    pos = blob.find(needle)
    while pos >= 0:
        out.append(sva + pos)
        pos = blob.find(needle, pos + 1)
    return out

for v in (0xB0BC8C, 0xB0BC90, 0xB0BC98, 0xB0BC9C):
    hs = refs(v)
    print(f"### refs to {v:#x}: {len(hs)}")
    for h in hs:
        ins_list = dis(h - 10, 12)
        cont = [i for i in ins_list if i.address <= h < i.address + i.size]
        pre = f"{cont[0].address:08X} {cont[0].mnemonic} {cont[0].op_str}" if cont else "?"
        nxt = dis((cont[0].address + cont[0].size) if cont else h, 48)
        print(f"  {h:08X} in [{pre}]  then: " + " | ".join(f"{j.mnemonic} {j.op_str}" for j in nxt[:8]))
    print()
