# -*- coding: utf-8 -*-
"""P04 probe2 —— 引擎自证 + 本报告引用的已定谳基线字节复核（只读 gamemd.exe）

复核项：
1. eng.coverage 自证（100.00% / 1394120 insns）
2. 0xA8ED80 引用普查：总数 + 唯一写者（基线：46 引用 / 唯一写 0x7778CE）
3. 0x55D360 头部门控字节：0xA8E9A0 早退 / 0xA8ED80 焦点门 / Sleep(500ms) 与 Sleep(10ms) 环
4. IAT：0x7E11F0=Sleep、0x7E1530=timeGetTime
5. 写者 0x7778CE 上下文（WndProc WM_ACTIVATEAPP 沿）
6. 0x55DE7E/0x55DE81 唯一定常 inc + 写回（frame 推进点，证明战斗中 frame 由该处推进）
"""
import sys

sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()

print("== 1. coverage 自证")
cov, nins, resync = eng.coverage
print("eng.coverage = %.2f%% / %d insns / %d resync" % (cov, nins, resync))
print("sha256 = %s" % eng.sha)

print("\n== 2. 0xA8ED80 引用普查")
h = eng.disp_hits(0x00A8ED80)
ws = [x for x in h if x[1] == "W"]
print("总引用 %d（基线 46）/ 写 %d（基线 1）" % (len(h), len(ws)))
for va, rw, mn, ops in h:
    if rw == "W":
        print("  W %08X  %-8s %s" % (va, mn, ops))

print("\n== 3. 0x55D360 头部门控（焦点旗标假说的机制字节）")
for va, bs, mn, ops in eng.disasm(0x55D360, 0x60):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

print("\n== 4. IAT")
for va in (0x7E11F0, 0x7E1530):
    print("  [0x%08X] -> %r" % (va, eng.resolve_iat(va)))

print("\n== 5. 写者 0x7778CE 上下文")
for va, bs, mn, ops in eng.disasm(0x7778B0, 0x40):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

print("\n== 6. frame 推进点 0x55DE7E / 写回 0x55DE81")
for va, bs, mn, ops in eng.disasm(0x55DE70, 0x20):
    print("  %08X  %-20s  %-8s %s" % (va, bs, mn, ops))

print("\n== 7. 0xA8E9A0 在 0x55D360 头部的读（菜单停帧混杂的机制依据）")
h2 = eng.disp_hits(0x00A8E9A0)
inhead = [x for x in h2 if 0x55D360 <= x[0] < 0x55D380]
print("0xA8E9A0 全镜像 %d 处引用；0x55D360 头部 %d 处" % (len(h2), len(inhead)))
for va, rw, mn, ops in inhead:
    print("  %08X %s %-8s %s" % (va, rw, mn, ops))

print("\n[P04 probe2 DONE]")
