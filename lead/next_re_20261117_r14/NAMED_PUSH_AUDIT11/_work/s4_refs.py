import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT11\_work")
from pe import *  # noqa

name, sva, vsz, rawsz, raw = sec_of(0x401000)
blob = DATA[raw:raw + rawsz]
needle = (0xB0BC88).to_bytes(4, "little")
hits = []
pos = blob.find(needle)
while pos >= 0:
    hits.append(sva + pos)
    pos = blob.find(needle, pos + 1)
print("total refs to 0xb0bc88 =", len(hits))

# classify by following ~40 bytes of disasm
for h in hits:
    # find instruction start: the ref usually inside 'b9 88 bc b0 00' (mov ecx,imm) or 'c7 05 .. imm'
    ins_list = dis(h - 8, 64)
    # locate the insn containing h
    containing = [i for i in ins_list if i.address <= h < i.address + i.size]
    tag = "?"
    if containing:
        i0 = containing[0]
        nxt = dis(i0.address + i0.size, 40)
        txt = " | ".join(f"{j.mnemonic} {j.op_str}" for j in nxt[:9])
        tag = f"{i0.address:08X} {i0.mnemonic} {i0.op_str}  ->  {txt}"
    print(f"  {h:08X}  {tag}")
