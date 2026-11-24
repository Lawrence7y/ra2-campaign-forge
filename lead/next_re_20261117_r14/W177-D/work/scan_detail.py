#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""原子版：全图扫 chain>=2 的格，并在同一次遍历中立即 dump 每节点完整详情（RTTI/owner/layer/type）。
附带 bypass 开关与 frame，便于判断稳定性。只读。"""
import ctypes, json, sys, time
from collections import Counter
import w177_core as W
import wb_probe as P
import dsnap as D

pid = W.pid_of()
m = W.Mem(pid)
base = m.u32(P.CELL_ARRAY)
mapc = P.MAP_SINGLETON
w = m.u32(mapc + 0x14C); h = m.u32(mapc + 0x150)
ph = P.player_house(m)

out = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "pid": pid, "frame": m.u32(W.A_FRAME),
       "w": w, "h": h, "bypass": D.bypass_globals(m), "multi": []}

for cy in range(h):
    rowbase = base + ((cy << 9) + 0) * 4
    buf = ctypes.create_string_buffer(w * 4); got = ctypes.c_size_t(0)
    if not W.k32.ReadProcessMemory(m.h, ctypes.c_void_p(rowbase), buf, w * 4, ctypes.byref(got)):
        continue
    for cx in range(w):
        cell = int.from_bytes(buf.raw[cx*4:cx*4+4], "little")
        if not cell or cell == P.INVALID_CELL:
            continue
        hA = m.u32(cell + P.CELL_E4); hB = m.u32(cell + P.CELL_E8)
        def walk(head):
            nodes=[]; seen=set(); p=head
            while p and len(nodes)<32 and (p&3)==0 and 0x100000<=p<=0x70000000:
                if p in seen: break
                seen.add(p)
                nodes.append(D.node_detail(m,p))
                p=m.u32(p+0x30)
            return nodes
        nodesA=walk(hA); nodesB=walk(hB)
        if len(nodesA)>=2 or len(nodesB)>=2:
            out["multi"].append({"cx":cx,"cy":cy,"cell":hex(cell),
                                 "headA":hex(hA) if hA else None,"lenA":len(nodesA),"nodesA":nodesA,
                                 "headB":hex(hB) if hB else None,"lenB":len(nodesB),"nodesB":nodesB})

print(json.dumps(out, ensure_ascii=False, default=str))
