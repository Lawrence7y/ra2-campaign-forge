# -*- coding: utf-8 -*-
"""领队裁决 Q1 vs Q3 冲突：0x5BF260 是否写 0xB45B68（影片队列 Count）？

Q1_B45B68 声称：0x5BF260 的 10 个非脚本调用者（INTRO/Intro/胜败影片）会把播放器
压进 0xB45B58，Count 0→1 ⇒「无脚本动作时 +0x62C 也会非零」。
Q3_SOURCES 反证：0x5BF260 只调 0x5BED40，不写 Count；0x5BF260 与 0x5BF2B0 是不同函数。

本探针独立判定，只读 gamemd.exe。
"""
import sys

sys.path.insert(0, r'D:/Project/ra2-campaign-forge/lead/goal3t_nightwatch_20261102/swarm_20261104')
from ra2tool import Engine

e = Engine()
print("coverage", e.coverage)

print("\n=== 0x5BF260 全函数（到 ret 0xC 为止）===")
for a, b, m, o in e.disasm(0x5BF260, 0x50):
    print("%08X %-18s %s %s" % (a, b, m, o))
    if m.startswith("ret"):
        break

print("\n=== 0x5BF2B0 全函数（到 ret 为止）===")
for a, b, m, o in e.disasm(0x5BF2B0, 0xE0):
    print("%08X %-18s %s %s" % (a, b, m, o))
    if m.startswith("ret"):
        break

print("\n=== 0x5BED40 头部 30 条（看是否触达 0xB45B68 / 0xB45B5C）===")
for a, b, m, o in e.disasm(0x5BED40, 0x80):
    print("%08X %-18s %s %s" % (a, b, m, o))

print("\n=== 谁写 0xB45B5C（队列数组基址）===")
for va, k, m, o in e.disp_hits(0xB45B5C):
    print("%s %08X %-10s %s" % (k, va, m, o))
