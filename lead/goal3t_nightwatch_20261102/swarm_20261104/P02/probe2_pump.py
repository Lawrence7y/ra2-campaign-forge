# -*- coding: utf-8 -*-
# P02 probe2: 泵 0x5D4D50 —— 边界(G-83: ret扫描+E8对齐+分支闭包)、IAT 调用、调用者
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
PUMP = 0x5D4D50

print("== pump linear window 0x5D4D50..0x5D4E80 ==")
for a, b, m, o in eng.disasm(PUMP, 0x130):
    print("%08X  %-20s %s %s" % (a, b, m, o))

# 边界：分支闭包（从 head 出发的全部可达地址，不切任何块）
reach = eng.reach_without(PUMP, PUMP + 0x800, 0x7FFFFFFF, 0)
end = max(reach) + 1
print("\n== closure ==")
print("head=%08X  max_reachable=%08X  closure_size=%d" % (PUMP, end, len(reach)))

# G-83: ret 扫描 —— 闭包内的 ret + 闭包结束处往后的对齐头
rets, succ = eng.func_rets(PUMP, end + 0x40)
print("rets in [pump, end+0x40):", ["%08X" % r.address for r in rets])

# 下一个函数头候选：end 起线性看的 8 字节
print("bytes at end:", eng.rd(end, 16).hex())
for a, b, m, o in eng.disasm(end, 0x20):
    print("%08X  %-20s %s %s" % (a, b, m, o))

# 泵内全部 call 指令 -> IAT 解析
print("\n== calls inside pump closure ==")
seq = sorted(reach)
for a, b, m, o in eng.disasm(PUMP, end - PUMP):
    if m in ("call", "jmp") and o.startswith("0x"):
        tgt = int(o, 16)
        tag = ""
        if 0x7E1100 <= tgt < 0x7E1600 or True:
            r = eng.resolve_iat(tgt) if eng.u32(tgt) and eng.fo(tgt) else None
        # IAT 判据：目标 dword 指向 user32/kernel32 区间 —— resolve_iat 只对 IAT 槽有意义
        try:
            rr = eng.resolve_iat(tgt)
        except Exception:
            rr = None
        print("%08X  %s %s   %s" % (a, m, o, ("IAT->" + repr(rr)) if rr else ""))

# 全镜像调用者（E8 直呼）
print("\n== direct callers of 0x5D4D50 (E8 scan over decoded stream) ==")
for i in eng.stream:
    if i.mnemonic == "call" and i.operands and i.operands[0].type == 2 \
            and i.operands[0].imm == PUMP:
        print("caller: %08X" % i.address)
