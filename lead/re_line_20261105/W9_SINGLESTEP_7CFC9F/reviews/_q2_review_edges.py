# -*- coding: utf-8 -*-
"""独立复核 Q2 · 边界反例：外部 call/jmp 落入函数体内部？间接跳转？"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

e = Engine()
by = e.by()
LO, HI = 0x7CFB13, 0x7CFE1C

# 外部指令的直接分支目标落在 (LO,HI) 内（排除函数自身内部的条件跳转）
incoming = []
for a, ins in by.items():
    if LO <= a < HI:
        continue
    if ins.mnemonic.startswith("j") or ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2:
                t = ins.operands[0].imm
                if LO < t < HI:
                    incoming.append((a, ins.mnemonic, ins.op_str, hex(t)))
        except Exception:
            pass
print("[INCOMING] external branch/call targets INSIDE (0x7CFB13,0x7CFE1C) =",
      len(incoming))
for x in sorted(incoming)[:30]:
    print("   ", hex(x[0]), x[1], x[2], "->", x[3])

# 直接分支目标 == LO 的全部（已知 3 个 call），复核有无 jmp
to_lo = []
for a, ins in by.items():
    if ins.mnemonic.startswith("j") or ins.mnemonic == "call":
        try:
            if ins.operands and ins.operands[0].type == 2 and ins.operands[0].imm == LO:
                to_lo.append((a, ins.mnemonic, ins.op_str))
        except Exception:
            pass
print("[INCOMING] branches to HEAD =", len(to_lo), [(hex(a), m, o) for a, m, o in sorted(to_lo)])

# 间接 call/jmp 数量（无法静态判定落点，Q2 未列）
ind = [(a, ins.mnemonic, ins.op_str) for a, ins in by.items()
       if LO <= a < HI and (ins.mnemonic.startswith("j") or ins.mnemonic == "call")
       and any(op.type != 2 for op in ins.operands)]
print("[INDIRECT] indirect call/jmp inside window =", len(ind), ind[:10])

# 检查 0x7CFB13 到 0x7CFE1C 之间是否有 55 8B EC 序列（嵌套序言反例）
nested = []
for a in range(LO, HI - 2):
    if e.rd(a, 3) == b"\x55\x8B\xEC":
        nested.append((hex(a), "in_by", a in by))
print("[NESTED] 55 8B EC byte triples in window =", nested)
