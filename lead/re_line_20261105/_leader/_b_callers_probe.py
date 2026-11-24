# -*- coding: utf-8 -*-
"""D-20 步骤 B（收尾）：全镜像普查 call 0x5F4B10，找可见性判定的真实调用点，
并检查各调用点附近是否有计数累加。只读 gamemd.exe。"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()

print("=== 全镜像 call 0x5F4B10（DrawIfVisible）===")
hits = [i.address for i in e.stream
        if i.mnemonic == "call" and i.operands
        and i.operands[0].type == 2 and i.operands[0].imm == 0x5F4B10]
print("count =", len(hits))
for a in hits:
    print("  %08X" % a)

print("\n=== 全镜像 call 0x6D2140（IsVisible）===")
h2 = [i.address for i in e.stream
      if i.mnemonic == "call" and i.operands
      and i.operands[0].type == 2 and i.operands[0].imm == 0x6D2140]
print("count =", len(h2))
for a in h2:
    print("  %08X" % a)

print("\n=== 各 DrawIfVisible 调用点前 12 条 / 后 12 条上下文 ===")
by = e.by()
stream = e.stream
idx = {ins.address: k for k, ins in enumerate(stream)}
for a in hits:
    k = idx[a]
    print("\n--- caller @ %08X ---" % a)
    for j in range(max(0, k - 12), min(len(stream), k + 13)):
        ins = stream[j]
        mark = " <==" if ins.address == a else ""
        print("  %08X %-18s %s %s%s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str, mark))
