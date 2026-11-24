# -*- coding: utf-8 -*-
"""D-20 步骤 B（续）：在 0x6D8DB0 渲染簇内找「可见计数」累加器。

判据：在调用 DrawIfVisible（0x5F4B10 或其内联形态）附近，是否存在
  inc/dec 或 add 到某个栈槽/全局的计数操作。
只读 gamemd.exe。
"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()

# 先找 0x6D8DB0 的函数尾（下一个 ret 后的填充）
end = 0x6D8DB0
seq = [i for i in e.stream if 0x6D8DB0 <= i.address < 0x6DA200]
print("insns in 0x6D8DB0..0x6DA200 : %d" % len(seq))
print("range = %08X..%08X" % (seq[0].address, seq[-1].address))

print("\n=== 该范围内所有 call 0x5F4B10（DrawIfVisible）===")
hits = [i for i in seq if i.mnemonic == "call" and i.operands
        and i.operands[0].type == 2 and i.operands[0].imm == 0x5F4B10]
print("count =", len(hits))
for i in hits:
    print("  %08X" % i.address)

print("\n=== 该范围内所有 inc / dec dword（疑似计数器）===")
cnt = 0
for i in seq:
    if i.mnemonic in ("inc", "dec") and i.operands:
        o = i.operands[0]
        try:
            w = o.size
        except Exception:
            w = 0
        if w == 4:
            cnt += 1
            print("  %08X %-6s %s" % (i.address, i.mnemonic, i.op_str))
print("total 4-byte inc/dec:", cnt)

print("\n=== 该范围内所有写全局 dword 的指令（mov [abs], reg）===")
g = 0
for i in seq:
    if i.mnemonic == "mov" and len(i.operands) >= 2:
        d = i.operands[0]
        if d.type == 3 and d.mem.base == 0 and d.mem.index == 0 and d.mem.disp > 0x400000:
            g += 1
            if g <= 25:
                print("  %08X %-6s %s" % (i.address, i.mnemonic, i.op_str))
print("total global dword writes:", g)
