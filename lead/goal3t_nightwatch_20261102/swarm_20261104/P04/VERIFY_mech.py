# -*- coding: utf-8 -*-
"""P04 VERIFY mech-side —— 独立复核 P04 报告机制字节。只读 gamemd.exe，零真机。"""
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()

print("[M1] coverage 自证")
cov, nins, resync = eng.coverage
print("eng.coverage = %.2f%% / %d insns / %d resync" % (cov, nins, resync))
print("sha256 = %s" % eng.sha)

print("\n[M2] 0xA8ED80 绝对全局访存普查")
h = eng.disp_hits(0x00A8ED80)
ws = [x for x in h if x[1] == "W"]
print("总引用 = %d（基线 46）| 写 = %d（基线 1）" % (len(h), len(ws)))
for va, rw, mn, ops in h:
    if rw == "W":
        print("  W %08X  %-8s %s" % (va, mn, ops))

print("\n[M3] 0x55D360 头部门控（原始字节 + 反汇编）")
print("raw[0x55D360:0x55D3A0] =", eng.rd(0x55D360, 0x40).hex())
for va, bs, mn, ops in eng.disasm(0x55D360, 0x64):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))
# 手工解码 je 0x55D371 的目标：0f84 rel32
rel = int.from_bytes(eng.rd(0x55D372, 4), "little", signed=True)
print("[M3] 0x55D371 je rel32=%+d → 目标=0x%X（报告称 0x55DECF）" % (rel, 0x55D377 + rel))
rel2 = int.from_bytes(eng.rd(0x55D386, 1), "little", signed=True)
print("[M3] 0x55D385 jne rel8=%+d → 目标=0x%X（报告称 0x55D3BB）" % (rel2, 0x55D387 + rel2))
rel3 = int.from_bytes(eng.rd(0x55D3AF, 1), "little", signed=True)
print("[M3] 0x55D3AE je rel8=%+d → 目标=0x%X（报告称环回 0x55D38D）" % (rel3, 0x55D3B0 + rel3))

print("\n[M4] 早退目标 0x55DECF 处（应为 epilogue/ret，不含 inc）")
for va, bs, mn, ops in eng.disasm(0x55DECF, 0x14):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

print("\n[M5] IAT")
for va in (0x7E11F0, 0x7E1530):
    print("  [0x%08X] -> %r" % (va, eng.resolve_iat(va)))

print("\n[M6] 写者 0x7778CE 上下文（沿触发：旧==新跳写）")
print("raw[0x7778B0:0x7778F0] =", eng.rd(0x7778B0, 0x40).hex())
for va, bs, mn, ops in eng.disasm(0x7778B0, 0x30):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

print("\n[M7] frame 推进点 0x55DE7E inc / 0x55DE81 写回")
print("raw[0x55DE70:0x55DE90] =", eng.rd(0x55DE70, 0x20).hex())
for va, bs, mn, ops in eng.disasm(0x55DE79, 0x10):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

print("\n[M8] 0xA8E9A0 头部读 + GameMode 0xA8B238 环判据")
h2 = eng.disp_hits(0x00A8E9A0)
print("0xA8E9A0 全镜像引用 =", len(h2), "| 0x55D360..0x55D380 内 =",
      sum(1 for va, *_ in h2 if 0x55D360 <= va < 0x55D380))
h3 = eng.disp_hits(0x00A8B238)
inloop = [x for x in h3 if 0x55D38D <= x[0] < 0x55D3BB]
print("0xA8B238 全镜像引用 =", len(h3), "| 0x55D38D..0x55D3BB 环内 =", len(inloop))
for va, rw, mn, ops in inloop:
    print("  %08X %s %-8s %s" % (va, rw, mn, ops))
print("\n[VERIFY_MECH DONE]")
