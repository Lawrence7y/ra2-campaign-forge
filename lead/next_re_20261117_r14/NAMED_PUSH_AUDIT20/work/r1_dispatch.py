import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\NAMED_PUSH_AUDIT20\work")
from lib import Bin, f, show
import capstone

b = Bin()
print("direct callers of 006DBE00:", [hex(x) for x in b.callers_of(0x6DBE00)])
print("push-imm sites of 006DBE00:", [hex(x) for x in b.push_sites(0x6DBE00)])

print("\n=== refs to global Tactical ptr 00887324 (mov reg,[0x887324]) ===")
hits = []
instrs, _ = b.sweep()
for ins in instrs:
    if ins.mnemonic == "mov" and "0x887324" in ins.op_str and "[" in ins.op_str.split(",")[-1]:
        hits.append(ins.address)
print(len(hits), [hex(h) for h in hits[:25]])

print("\n=== look for 'call [reg+0x18]' near reads of 0x887324 ===")
cand = []
for h in hits:
    for ins in b.dis(h, 14):
        if ins.mnemonic == "call" and "[e" in ins.op_str and "0x18]" in ins.op_str:
            cand.append((h, ins.address, f(ins)))
            break
for c in cand[:15]:
    print(f"  read@{c[0]:08X} -> {c[1]:08X} {c[2]}")
    print(show(b.dis(c[0], 10), "      "))

print("\n=== any 'ff 5x 18' / 'ff 9x' call [reg+0x18] in .text count ===")
n = 0
for ins in instrs:
    if ins.mnemonic == "call" and ins.op_str.endswith("+ 0x18]") and ins.size == 3:
        n += 1
print("3-byte call [reg+0x18] sites:", n)
