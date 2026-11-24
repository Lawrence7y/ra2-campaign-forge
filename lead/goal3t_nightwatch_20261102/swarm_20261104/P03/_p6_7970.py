# -*- coding: utf-8 -*-
# P06: 0x7970CE 区域结构 + indirect jmp 检查（0x79758C 宿主函数入口之谜）
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
by = eng.by()

print("--- disasm 0x7970B0..0x797120 ---")
for a in sorted(k for k in by if 0x7970B0 <= k < 0x797120):
    ins = by[a]
    print("%#08x  %-20s %s %s" % (a, ins.bytes.hex(), ins.mnemonic, ins.op_str))

print("\n--- indirect jmp/jmp reg / call reg in [0x7970CF, 0x797640) ---")
for a in sorted(k for k in by if 0x7970CF <= k < 0x797640):
    ins = by[a]
    if ins.mnemonic in ("jmp", "call"):
        ops = ins.operands
        if ops and ops[0].type != 2:   # 非立即数目标 = 间接
            print("%#08x  %s %s   bytes=%s" % (a, ins.mnemonic, ins.op_str, ins.bytes.hex()))

print("\n--- [0xa8b550] / [0xa8b554] 家族普查（判定该函数职责） ---")
for disp, tag in ((0xA8B550, "a8b550"), (0xA8B554, "a8b554"), (0xA8B568, "a8b568"), (0xA8B574, "a8b574")):
    hits = eng.disp_hits(disp)
    print("disp %#x: %d hits" % (disp, len(hits)))
    for va, acc, mn, ops in hits[:14]:
        print("   %#08x %s %s %s" % (va, acc, mn, ops))

print("\n--- 谁引用 0x7970D0?（分支入边全镜像搜） ---")
stream = eng.stream
for ins in stream:
    if ins.mnemonic[0] == "j" or ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2 and ins.operands[0].imm in (0x7970CE, 0x7970CF, 0x7970D0):
                print("%#08x %s -> %#x" % (ins.address, ins.mnemonic, ins.operands[0].imm))
        except Exception:
            pass
print("done")
