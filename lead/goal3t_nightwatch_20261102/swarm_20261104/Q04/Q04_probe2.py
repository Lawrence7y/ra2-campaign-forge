# -*- coding: utf-8 -*-
# Q04_probe2.py — 节奏/节流通道字节核验（纯静态只读，零真机）
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage:", eng.coverage)

print("\n=== M. 0x887328 / 0x887330（G_TICKLAST / G_TICKTGT，ra2tool 常量）读写点 ===")
for g in (0x887328, 0x887330):
    hits = eng.disp_hits(g)
    ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
    print(f"  {g:08X} hits={len(hits)} W={len(ws)}")
    for va, rw, mnem, ops in hits:
        print(f"      {rw} {va:08X} {mnem} {ops}")

print("\n=== N. 0xA8B55C（MLF timeGetTime 存点，P03 §2.2）读写点 ===")
hits = eng.disp_hits(0xA8B55C)
for va, rw, mnem, ops in hits:
    print(f"  {rw} {va:08X} {mnem} {ops}")

print("\n=== O. 0xA8E2E4（帧阈值，P03 称全镜像无写者）读写点 ===")
hits = eng.disp_hits(0xA8E2E4)
ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
print(f"hits={len(hits)} W={len(ws)}")
for va, rw, mnem, ops in hits[:10]:
    print(f"  {rw} {va:08X} {mnem} {ops}")

print("\n=== P. MLF 帧阈值/节流块 0x55D3BB..0x55D3F0 ===")
for a, by, mn, ops in eng.disasm(0x55D3BB, 0x38):
    print(f"{a:08X}  {by:<18} {mn} {ops}")

print("\n=== Q. 0x48C8B0 函数是否覆盖 0x48CB2E（四旗标写者归属）===")
rets, _succ = eng.func_rets(0x48C8B0, 0x48CCC0)
rs = [r.address for r in rets]
print("rets in [0x48C8B0,0x48CCC0):", [hex(r) for r in rs])
print("0x48CB2E 前 最近 ret:", hex(max([r for r in rs if r < 0x48CB2E], default=0)))

print("\n=== R. 0x48CB2E 上下文（写 0x8B41C0=1 的守卫）===")
for a, by, mn, ops in eng.disasm(0x48CB00, 0x30):
    print(f"{a:08X}  {by:<18} {mn} {ops}")

print("\nQ04_probe2 done.")
