# -*- coding: utf-8 -*-
# P02 probe3: 单遍流扫描 —— 旗标/hwnd/GameMode/0xABCD58/泵计数 访存普查
#              + WndProc 注册头扫描 + 泵调用者 + IAT 解析 + 包装函数窗口
import sys, bisect
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
PUMP = 0x5D4D50
TARGETS = {
    0xA8ED80: "FOCUS_FLAG",
    0xA8ED84: "CURRENT_FRAME",
    0xB73550: "HWND_MAIN",
    0xA8B238: "GAME_MODE",
    0xABCD58: "UNKNOWN_55D37C",
    0xAA0430: "PUMP_COUNT",
}
hits = {va: [] for va in TARGETS}
wnd_imm = []
pump_callers = []
stream = eng.stream          # 一次性解码
addrs = [i.address for i in stream]
print("stream decoded: %d insns" % len(stream))

for ins in stream:
    try:
        ops = ins.operands
    except Exception:
        continue
    for op in ops:
        if op.type == 3 and op.mem.base == 0 and op.mem.index == 0:
            if op.mem.disp in hits:
                hits[op.mem.disp].append(
                    (ins.address, "W" if (op.access & 2) else "R", ins.mnemonic, ins.op_str))
                break
        if op.type == 2 and 0x777700 <= op.imm <= 0x7778FF:
            wnd_imm.append((ins.address, hex(op.imm), ins.mnemonic, ins.op_str))
    if ins.mnemonic == "call" and ops and ops[0].type == 2 and ops[0].imm == PUMP:
        pump_callers.append(ins.address)

for va, name in TARGETS.items():
    print("\n== disp_hits(%08X) %s : %d refs ==" % (va, name, len(hits[va])))
    for h in hits[va]:
        print("  %08X %s  %s %s" % h)

print("\n== imm in [0x777700,0x7778FF] (WndProc 候选/注册点) ==")
for t in wnd_imm:
    print("  %08X  imm=%s  %s %s" % t)

print("\n== pump callers: %d ==" % len(pump_callers))
print("  " + " ".join("%08X" % c for c in pump_callers))

def ctx(va, back=6, fwd=4):
    k = bisect.bisect_right(addrs, va) - 1
    lo, hi = max(0, k - back), min(len(stream), k + fwd + 1)
    for i in stream[lo:hi]:
        mark = " ->" if i.address == va else "   "
        print("  %s %08X  %-18s %s %s" % (mark, i.address, i.bytes.hex(), i.mnemonic, i.op_str))

for va, name in ((0xB73550, "HWND_MAIN"), (0xA8B238, "GAME_MODE"), (0xABCD58, "UNKNOWN")):
    print("\n== 写点上下文 %s ==" % name)
    for h in hits[va]:
        if h[1] == "W":
            print(" -- writer %08X (%s %s):" % (h[0], h[2], h[3]))
            ctx(h[0], back=4, fwd=3)

print("\n== IAT ==")
for slot in (0x7E14F4, 0x7E14F8, 0x7E14BC, 0x7E14C0, 0x7E11F0, 0x7E1530):
    print("  %08X -> %s" % (slot, eng.resolve_iat(slot)))

print("\n== wrapper 0x53E770 ==")
for a, b, m, o in eng.disasm(0x53E770, 0x60):
    print("  %08X  %-18s %s %s" % (a, b, m, o))
print("\n== wrapper 0x53E730 ==")
for a, b, m, o in eng.disasm(0x53E730, 0x40):
    print("  %08X  %-18s %s %s" % (a, b, m, o))
print("\n== 0x49F740 ==")
for a, b, m, o in eng.disasm(0x49F740, 0x40):
    print("  %08X  %-18s %s %s" % (a, b, m, o))
