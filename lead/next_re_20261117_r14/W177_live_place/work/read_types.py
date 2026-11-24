#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""读每个 BuildingClass 的 BuildingTypeClass 名称字符串（type+0x24 区域），
判断是否有建造厂。只读。"""
import sys
import struct
import w177_core as W

# 从 FINAL_SNAPSHOT.ndjson 读建筑 obj 列表
import json
objs = []
with open(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\W177_live_place\EVIDENCE\FINAL_SNAPSHOT.ndjson", encoding="utf-8") as f:
    first = json.loads(f.readline())
    for b in first["buildings"]:
        objs.append((int(b["obj"], 16), b["o1_81"], int(b["type520"], 16)))

pid = W.pid_of()
if not pid:
    print("no gamemd")
    sys.exit(2)
m = W.Mem(pid)

def ascii_at(va, n=16):
    raw = b""
    for i in range(n):
        v = m.u8(va + i)
        if v is None or v == 0 or v < 0x20 or v > 0x7e:
            break
        raw += bytes([v])
    return raw.decode("latin-1")

for obj, o1, typ in objs:
    # 名称候选：type+0x24 (短 ID), type+0x3c 附近（长名）
    sid = ascii_at(typ + 0x24, 12)
    # 搜索 type+0..0x80 里的所有 ASCII 串
    strs = []
    i = 0
    while i < 0x90:
        s = ascii_at(typ + i, 16)
        if len(s) >= 3:
            strs.append((hex(i), s))
            i += len(s) + 1
        else:
            i += 1
    print("obj=%08X o1=%s type=%08X shortID=%r strings=%s" % (obj, o1, typ, sid, strs[:6]))
