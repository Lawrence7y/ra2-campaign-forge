# -*- coding: utf-8 -*-
"""领队独立核验 Q1 的两条断言：写点数量 + INTRO 非脚本入口。只读。"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()
h = e.disp_hits(0xB45B68)
nw = sum(1 for x in h if x[1] == 'W')
nr = sum(1 for x in h if x[1] == 'R')
print("total=%d W=%d R=%d" % (len(h), nw, nr))
for va, k, m, o in h:
    if k == 'W':
        print("W %08X %-10s %s" % (va, m, o))

print()
print("=== 0x539320.. (claim: push 0x8263A8 = \"INTRO\", call 0x5BF260) ===")
for a, b, m, o in e.disasm(0x539320, 0x30):
    print("%08X %-16s %s %s" % (a, b, m, o))

print()
print("=== string @0x8263A8 ===")
raw = e.rd(0x8263A8, 16)
print(repr(raw.split(b"\x00")[0]))
