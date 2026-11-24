#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115_probe.py —— 探测：接口方法表槽数是否有独立于 T 尺的结构上界，且是否紧致。
只读 census.pkl + r113c_slots.json，不重扫 .text 全段。"""
import json, os, sys
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r113')
import r113_lib as L

ROOT = L.ROOT
C = L.census()
V2C, T, E, B, colptr = C['V2C'], C['T'], C['E'], C['B'], C['colptr']
S = json.load(open(os.path.join(ROOT, '_r113/r113c_slots.json')))
per = S['per_interface']
det = S['detail']

print('census: vtables=%d  T span %d..%d' % (len(V2C), min(T.values()), max(T.values())))
print('interfaces with N!=0: %s' % (sorted(per),))
print()
print('%-28s %-6s %-6s %-6s %-6s %-8s' % ('iface', 'slots', 'T', 'B', 'E', 'T==B'))
tot = {'T_eq_B': 0, 'T_lt_B': 0, 'T_gt_B': 0, 'T_gt_E': 0, 'n': 0}
for nm in sorted(per):
    slots = list(per[nm])
    vs = [int(r[2], 16) for r in det[nm]]
    tset, bset, eset = set(), set(), set()
    for v in vs:
        tot['n'] += 1
        if T[v] == B[v]: tot['T_eq_B'] += 1
        elif T[v] < B[v]: tot['T_lt_B'] += 1
        else: tot['T_gt_B'] += 1
        if T[v] > E[v]: tot['T_gt_E'] += 1
        tset.add(T[v]); bset.add(B[v]); eset.add(E[v])
    print('%-28s %-6s %-6s %-6s %-6s %-8s' % (nm, slots, sorted(tset), sorted(bset), sorted(eset),
          'yes' if tset == bset else 'NO'))
print()
print('totals:', tot)
# B 尺 <= T 尺的违例清单
bad = [(hex(v), T[v], B[v]) for v in V2C if T[v] > B[v]]
print('global T>B violations:', len(bad), bad[:5])
print('global T<B count:', sum(1 for v in V2C if T[v] < B[v]))
print('global T==B count:', sum(1 for v in V2C if T[v] == B[v]))
