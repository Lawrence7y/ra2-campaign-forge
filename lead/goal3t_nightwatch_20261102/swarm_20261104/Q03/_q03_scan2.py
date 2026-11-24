# -*- coding: utf-8 -*-
"""Q03 scan2：raw 字节全镜像查 push 0xA8ED84；IStorage->IStream 助手函数；
load-upper 中 src 智能指针来源；save-upper 调用链速览。"""
import sys, struct
sys.path.insert(0, r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104")
from ra2tool import Engine

eng = Engine()
out = []
def p(s=""):
    print(s); out.append(s)

# A) raw 字节搜索：全镜像 '68 84 ED A8 00'（push 0xA8ED84）与 disp '84 ED A8 00'
needle_push = bytes.fromhex("6884EDA800")
needle_disp = bytes.fromhex("84EDA800")
cnt_push = cnt_disp = 0
pos_push, pos_disp = [], []
for nm, sva, vsz, rp, rsz in eng.SEC:
    if vsz == 0:
        continue
    blob = eng.raw[rp:rp + rsz]
    i = blob.find(needle_push)
    while i >= 0:
        cnt_push += 1
        pos_push.append((nm, sva + i))
        i = blob.find(needle_push, i + 1)
    i = blob.find(needle_disp)
    while i >= 0:
        cnt_disp += 1
        pos_disp.append((nm, sva + i))
        i = blob.find(needle_disp, i + 1)
p(f"[raw] push 0xA8ED84 (68 84 ED A8 00) 全镜像命中 = {cnt_push}")
for nm, va in pos_push:
    p(f"    {nm} 0x{va:08X}")
p(f"[raw] disp 字节 84 ED A8 00 全镜像命中 = {cnt_disp}")

# B) 助手函数 0x681080/0x6810A0/0x681840 反汇编（找 IStorage vtable 调用）
for h, tag in ((0x681080, "save-stm-helper"), (0x6810A0, "save-stm-helper2"),
               (0x681840, "load-stm-helper")):
    p(f"=== {tag} 0x{h:X} ===")
    for va, bh, mn, ops in eng.disasm(h, 0x60):
        p(f"{va:08X}  {bh:<18} {mn} {ops}")
    p()

# C) load-upper 内 StgOpenStorage 之后到 QI 之前的所有 call（速览）
p("=== LOAD-upper 0x67E440 body calls (0x67E4BE..0x67E660) ===")
for va, bh, mn, ops in eng.disasm(0x67E4BE, 0x67E660 - 0x67E4BE):
    if mn in ("call", "jmp"):
        p(f"{va:08X}  {bh:<14} {mn} {ops}")

# D) save-upper 内 StgCreateDocfile 之后到驱动调用之前的所有 call（速览）
p("=== SAVE-upper 0x67CEF0 body calls (0x67CF64..0x67D1B0) ===")
for va, bh, mn, ops in eng.disasm(0x67CF64, 0x67D1B0 - 0x67CF64):
    if mn in ("call", "jmp"):
        p(f"{va:08X}  {bh:<14} {mn} {ops}")

# E) IID @ 0x7F7C80 / 0x7F7C90（驱动内对象 QI 的 IID）
for a, tag in ((0x7F7C80, "save-QI-IID"), (0x7F7C90, "load-QI-IID")):
    b = eng.rd(a, 16)
    d1, d2, d3 = struct.unpack_from("<IHH", b, 0)
    p(f"[IID @ 0x{a:X} {tag}] {d1:08X}-{d2:04X}-{d3:04X}-{b[8:10].hex().upper()}-{b[10:16].hex().upper()}")

with open(r"D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104/Q03/_q03_scan2_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(out))
print("DONE")
