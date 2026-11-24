from base import BUF, IB, u32, s32
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
md = Cs(CS_ARCH_X86, CS_MODE_32)
md.skipdata = True
code = bytes(BUF[0x00401000-IB: 0x00500000-IB])
# record decode stream so we can map address -> (is instruction boundary)
boundaries = set()
insns = {}
for ins in md.disasm(code, 0x00401000):
    boundaries.add(ins.address)
    insns[ins.address] = ins
print("decoded", len(insns), "insns; 0x4F8F82 is a boundary?", 0x004F8F82 in boundaries)
# walk backwards from 0x4F8F82 to find the last 'prologue after ret+pad'
a = 0x004F8F82
best = None
while a > 0x00401000:
    if a in insns:
        ins = insns[a]
        if ins.mnemonic.startswith("ret"):
            # candidate function start = next instr after padding
            nxt = a + ins.size
            while nxt in insns and insns[nxt].mnemonic == "nop":
                nxt += insns[nxt].size
            best = nxt
            print("  ret @%08X -> next function likely starts at %08X %s %s" %
                  (a, best, insns[best].mnemonic if best in insns else "?",
                   insns[best].op_str if best in insns else ""))
            break
    a -= 1
print()
print("=== disasm from that start to 0x4F9000 ===")
if best:
    cnt = 0
    for ins in md.disasm(bytes(BUF[best-IB: 0x004F9000-IB]), best):
        print("%08X  %-16s %-9s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))
        cnt += 1
        if cnt > 40: break
