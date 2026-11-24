# -*- coding: utf-8 -*-
"""A12 probe0: 现场自证 —— coverage + 基线复核对账。"""
import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\goal3t_nightwatch_20261102\swarm_20261104")
from ra2tool import Engine

eng = Engine()
print("== coverage ==")
print(eng.coverage)
print("expect: 100.00% / 1394120 insns")

print("\n== sha256 ==")
print(eng.sha)

print("\n== MLF 头部字节 ==")
print("0x55D360:", eng.rd(0x55D360, 16).hex())

print("\n== inc 块 0x55DE73..0x55DE8A ==")
for va, by, mn, ops in eng.disasm(0x55DE73, 0x20):
    print(hex(va), by, mn, ops)

print("\n== IAT ==")
print("0x7E11F0 ->", eng.resolve_iat(0x7E11F0))
print("0x7E1530 ->", eng.resolve_iat(0x7E1530))

print("\n== MLF 3 rets ==")
rets, succ = eng.func_rets(0x55D360, 0x55DEE0)
for r in rets:
    print(hex(r.address), r.bytes.hex(), r.mnemonic, r.op_str)

print("\n== reach_without INC ==")
seen = eng.reach_without(0x55D360, 0x55DEE0, 0x55DE73, 0x55DE84)
print("reachable count:", len(seen))
for r in (0x55D877, 0x55DEC7, 0x55DEDB):
    print(hex(r), "in set:", r in seen)

print("\n== MLF 回边 ==")
for be in eng.loop_backedges(0x55D360, 0x55DEE0):
    print(hex(be[0]), "->", hex(be[1]), be[2])
