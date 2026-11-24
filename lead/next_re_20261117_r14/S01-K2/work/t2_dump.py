#!/usr/bin/env python3
"""T2 step 1: dump main loop, game entry, and their direct call targets."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import dl

CARD = os.path.join(dl.ROOT, r"lead\next_re_20261117_r14\S01-K2")
EV = os.path.join(CARD, "EVIDENCE")

# 1. main loop region 0x48CCC0 + 0x320 (a bit past 780B=0x30C for the tail)
ml_start, ml_size = 0x48CCC0, 0x320
dl.dump(ml_start, ml_size, os.path.join(EV, "mainloop_disasm.txt"))
print(f"mainloop {ml_start:#x}+{ml_size:#x} -> mainloop_disasm.txt")

# 2. runner-up: inner loop window detail 0x48CE40..0x48CEC0
dl.dump(0x48CE40, 0x90, os.path.join(EV, "mainloop_inner.txt"))

# 3. game entry 0x6BB9A0 + 0x200
dl.dump(0x6BB9A0, 0x200, os.path.join(EV, "entry_6BB9A0_disasm.txt"))

# 4. WinMainCRTStartup 0x7CD80F neighborhood
dl.dump(0x7CD800, 0x80, os.path.join(EV, "crtstartup_disasm.txt"))

# 5. direct call targets in mainloop
print("\n=== direct call/jmp targets in main loop [0x48CCC0,0x48CFE0) ===")
for site, mn, tgt in dl.direct_call_targets(0x48CCC0, 0x320):
    print(f"  {site:#x} {mn:<4} -> {tgt:#x}")

# 6. who calls main loop 0x48CCC0 (scan all .text for e8 rel32 to it)
print("\n=== callers of 0x48CCC0 (scan .text rel32) ===")
target = 0x48CCC0
hits = []
for ins in dl.disasm(0x401000, 0x6BB000 - 0x401000):
    if ins.mnemonic in ("call", "jmp") and ins.operands and ins.operands[0].type == dl.CS_OP_IMM:
        if ins.operands[0].imm == target:
            hits.append((ins.address, ins.mnemonic))
for h in hits:
    print(f"  {h[0]:#x} {h[1]}")
print(f"  count={len(hits)}")
