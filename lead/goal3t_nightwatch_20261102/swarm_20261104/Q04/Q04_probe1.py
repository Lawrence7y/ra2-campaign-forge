# -*- coding: utf-8 -*-
# Q04_probe1.py — 判别式关键 VA 逐字节核验（纯静态只读，零真机）
# 只用共享引擎 ra2tool.Engine（重同步解码），禁止裸 capstone 扫全镜像。
# eng.disasm 返回 [(va, bytes_hex, mnem, op_str)]。
import sys
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("coverage:", eng.coverage)


def show(title, va, n):
    print(f"\n=== {title} ===")
    for a, by, mn, ops in eng.disasm(va, n):
        print(f"{a:08X}  {by:<18} {mn} {ops}")


show("A. MLF 四旗标门：0x55DEB0..0x55DEE0（jne 0x55DEC8 与 ret 0x55DEDB）", 0x55DEB0, 0x30)
show("B. MLF 焦点等待环入口：0x55D377..0x55D3C3（0xABCD58 闩 + Sleep 环）", 0x55D377, 0x4C)
show("C. 挂起门：0x55D7D4..0x55D884（读 [0xA8B230]+0x62C 与 0x55D877 ret）", 0x55D7D4, 0xB0)
show("D. 旗标状态机 0x55CFD0 头部", 0x55CFD0, 0x60)
show("E. dispatcher 帧循环 0x48CE80..0x48CEB0", 0x48CE80, 0x30)

print("\n=== F. 泵计数 0xAA0430 写点（复钉 r063a 7 组写者）===")
hits = eng.disp_hits(0xAA0430)
print("hits =", len(hits))
for va, rw, mnem, ops in hits:
    print(f"  {va:08X} {rw} {mnem} {ops}")

print("\n=== G. 0xA8E9A0（in-tactical/INGAME 门）写点 ===")
hits = eng.disp_hits(0xA8E9A0)
ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
print(f"hits = {len(hits)}  W = {len(ws)}")
for va, mnem, ops in ws:
    print(f"  W {va:08X} {mnem} {ops}")

print("\n=== H. 四旗标各自写点普查 ===")
for g in (0xA8ECD0, 0xA83D49, 0x8B41C0, 0xA83D48):
    hits = eng.disp_hits(g)
    ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
    print(f"  {g:08X} hits={len(hits)} W={len(ws)}")
    for va, mnem, ops in ws:
        print(f"      W {va:08X} {mnem} {ops}")

print("\n=== I. 0xABCD58 全部读写点（闩语义核验）===")
hits = eng.disp_hits(0xABCD58)
print("hits =", len(hits))
for va, rw, mnem, ops in hits:
    print(f"  {va:08X} {rw} {mnem} {ops}")

print("\n=== J. 0xA8B24C（加载相位）与 0xA8B238（GameMode）写点 ===")
for g in (0xA8B24C, 0xA8B238):
    hits = eng.disp_hits(g)
    ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
    print(f"  {g:08X} hits={len(hits)} W={len(ws)}")
    for va, mnem, ops in ws[:12]:
        print(f"      W {va:08X} {mnem} {ops}")

print("\n=== K. 挂起态全局镜像 0xA8ED9C 与追帧目标 0xB07784 写点 ===")
for g in (0xA8ED9C, 0xB07784):
    hits = eng.disp_hits(g)
    ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
    print(f"  {g:08X} hits={len(hits)} W={len(ws)}")
    for va, mnem, ops in ws[:12]:
        print(f"      W {va:08X} {mnem} {ops}")

print("\n=== L. 渐变状态机 0xA9FAB0/0xA9FA98 写点（P01 判别式第 4 条）===")
for g in (0xA9FAB0, 0xA9FA98):
    hits = eng.disp_hits(g)
    ws = [(va, mnem, ops) for va, rw, mnem, ops in hits if rw == "W"]
    print(f"  {g:08X} hits={len(hits)} W={len(ws)}")
    for va, mnem, ops in ws[:12]:
        print(f"      W {va:08X} {mnem} {ops}")

print("\nQ04_probe1 done.")
