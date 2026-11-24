# -*- coding: utf-8 -*-
"""A04 probe1: 0xA8B238 GameMode 全镜像引用普查（重同步解码引擎）。
只读 gamemd.exe；输出全部写点 + 读点计数。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==", eng.coverage)
print("== sha256 ==", eng.sha[:16], "...")

GM = 0x00A8B238
hits = eng.disp_hits(GM)
writes = [h for h in hits if h[1] == "W"]
reads = [h for h in hits if h[1] == "R"]
print("total hits:", len(hits), " writes:", len(writes), " reads:", len(reads))

by = eng.by()

print("\n== ALL WRITES (va, bytes, mnem, op_str) ==")
for va, k, mn, ops in writes:
    ins = by.get(va)
    print("0x%08X  %-20s %s %s" % (va, ins.bytes.hex(), mn, ops))

print("\n== WRITES with surrounding context (prev 2 / next 2 insns) ==")
addr_list = sorted(by.keys())
idx_of = {a: i for i, a in enumerate(addr_list)}
for va, k, mn, ops in writes:
    i = idx_of.get(va)
    print("---- write @0x%08X ----" % va)
    for j in range(max(0, i - 2), min(len(addr_list), i + 3)):
        ins = by[addr_list[j]]
        mark = ">>" if addr_list[j] == va else "  "
        print("%s 0x%08X  %-18s %s %s" % (mark, ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# 读点按函数聚合粗计数（供分档参考）
print("\n== READ count by VA (dedup) ==", len(reads))
