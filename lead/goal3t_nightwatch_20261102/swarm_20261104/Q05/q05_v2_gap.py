# -*- coding: utf-8 -*-
"""Q05 v2：补 v1 普查漏洞 + 0x55CFD0 结构 + LogicUpdate 等待环 + 0x7970D0 死代码。"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage: %.6f%% / %d insns / %d resync" % eng.coverage)
by = eng.by()
stream = eng.stream

def disby(lo, hi, tag):
    print("-- %s [0x%X,0x%X) --" % (tag, lo, hi))
    a = lo
    while a < hi:
        i = by.get(a)
        if i is None:
            a += 1
            continue
        print("  0x%08X: %-22s %s %s" % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
        a += i.size

def dis(va, n, tag):
    print("-- %s @0x%X --" % (tag, va))
    for a, b, m, o in eng.disasm(va, n):
        print("  0x%08X: %-22s %s %s" % (a, b, m, o))

# 全量 call/jmp 目标 -> 站点
calls = {}
for ins in stream:
    if ins.mnemonic not in ("call", "jmp"):
        continue
    if not ins.operands or ins.operands[0].type != 2:
        continue
    calls.setdefault(ins.operands[0].imm, []).append((ins.address, ins.mnemonic))

def csites(t, lo=None, hi=None):
    return [hex(a) for a, mn in calls.get(t, [])
            if (lo is None or lo <= a < hi) and mn == "call"]

print("\n== V1 pseudocode anchors in MLF [0x55D360,0x55DEE0) ==")
for t, nm in [(0x54F5C0, "输入0x54F5C0"), (0x4A9840, "视口0x4A9840"),
              (0x637550, "0x637550"), (0x5D4430, "0x5D4430"),
              (0x647260, "NetSync0x647260"), (0x55E160, "LogicUpdate"),
              (0x725C70, "0x725C70"), (0x637270, "0x637270"),
              (0x48D080, "UnknownCall"), (0x5D4D50, "Pump"),
              (0x5D5870, "timeBegin"), (0x5D5880, "timeEnd"),
              (0x5D5890, "timeGetTimeThunk"), (0x53B560, "0x53B560"),
              (0x4F4480, "0x4F4480"), (0x4F4320, "0x4F4320"),
              (0x55DEE0, "0x55DEE0(次函数)"), (0x55AFB0, "0x55AFB0")]:
    print("  %-18s MLF内: %s" % (nm, csites(t, 0x55D360, 0x55DEE0)))

print("\n== V2 UnknownCall callsites in LogicUpdate [0x55E160,0x55E400) ==")
print(" ", csites(0x48D080, 0x55E160, 0x55E400))

print("\n== V3 four-flag globals: all W sites ==")
for g in (0xA83D49, 0xA8ECD0, 0x8B41C0, 0xA83D48):
    hs = eng.disp_hits(g)
    print("  0x%08X total=%d W=%s" % (g, len(hs),
          [(hex(a), m, o) for a, k, m, o in hs if k == "W"]))

print("\n== V4 write-block exact bytes ==")
for wva in (0x55D123, 0x55D1B1, 0x55D219, 0x55D25C):
    print("  0x%08X: %s" % (wva, eng.rd(wva, 8).hex(" ")))
    dis(wva, 6, "wb")

print("\n== V5 0x55CFD0 full stream decode [0x55CFD0,0x55D0A0) + gate zone ==")
disby(0x55CFD0, 0x55D020, "cfd0_head")
disby(0x55D050, 0x55D0B0, "gate_0x55D059")

print("\n== V6 LogicUpdate wait/execute paths ==")
disby(0x55E229, 0x55E2C0, "lu_wait")
disby(0x55E2AC, 0x55E2C0, "lu_gate_fall")
disby(0x55E330, 0x55E3E0, "lu_exec_head")

print("\n== V7 GameSpeed->887330 (S5#2 anchors) ==")
disby(0x55D510, 0x55D570, "gs_map")

print("\n== V8 W-site contexts ==")
for wva in (0x52DA08, 0x5B7329, 0x5BB20C, 0x5E550F, 0x5E747C, 0x68466B, 0x686765, 0x795234, 0x79758C):
    dis(wva - 6, 14, "W@0x%X" % wva)

print("\n== V9 0x7970D0 deadness ==")
raw = eng.raw
SEC = eng.SEC
def off2va(i):
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= i < rp + rsz:
            return sva + (i - rp)
    return None
# imm32 data refs
pat = struct.pack("<I", 0x7970D0)
pos, immhits = 0, []
while True:
    i = raw.find(pat, pos)
    if i < 0:
        break
    va = off2va(i)
    pos = i + 1
    if va is not None:
        immhits.append(va)
print("  imm32 0x7970D0 occurrences(VA):", [hex(a) for a in immhits])
# E8/E9 rel32 across whole file
tgt = 0x7970D0
relhits = []
n = len(raw)
for i in range(n - 5):
    if raw[i] in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", raw, i + 1)[0]
        va = off2va(i)
        if va is not None and va + 5 + rel == tgt:
            relhits.append((hex(va), hex(raw[i])))
print("  E8/E9 rel32 -> 0x7970D0:", relhits)
# 函数包含关系：rets in [0x7970D0, 0x79758C)
rets, _ = eng.func_rets(0x7970D0, 0x7975A0)
print("  rets in [0x7970D0,0x7975A0):", [hex(r.address) for r in rets])
reach = eng.reach_without(0x7970D0, 0x7975A0, -1, -1)
print("  0x79758C reachable from 0x7970D0 head:", 0x79758C in reach)

print("\n== V10 挂起深度 inc helper 头与调用者 ==")
disby(0x684150, 0x684182, "inc_helper_zone")
# 猜头：0x684150 区域内被 call 的地址
for t in sorted(set(k for k in calls if 0x684100 <= k < 0x684200)):
    print("  calltarget 0x%08X sites=%s" % (t, [hex(a) for a, _ in calls[t]][:10]))

print("\n== V11 0x684180(dec helper) 全部调用者 ==")
print(" ", csites(0x684180)[:20])

print("\n== V12 0x68466B 上下文（clock 附录B 0x684675 声称） ==")
disby(0x684655, 0x684690, "68466B_ctx")

print("\n== V13 WndProc fmt 串 0x849E94 ==")
s = eng.rd(0x849E94, 40)
print("  raw:", s.hex(" "))
print("  ascii:", s.split(b"\x00")[0].decode("ascii", "replace"))

print("\n== V14 MLF elapsed-clamp 块 [0x55DD90,0x55DE40) ==")
disby(0x55DD90, 0x55DE40, "elapsed")

print("\n== V15 0x55DC9E 上下文（轮询器调用点） ==")
disby(0x55DBB0, 0x55DCB0, "poller_ctx")
