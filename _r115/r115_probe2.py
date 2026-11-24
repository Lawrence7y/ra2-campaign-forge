#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115_probe2 —— 边界 dword 分类：vtable 的 T 尺末端之后那个 dword 到底是什么。
若它是 COL（值落在 .rdata 且自身合法），则该处结构上不可能是方法槽 ⇒ T 是精确末端而非下界。"""
import json, os, sys, collections
sys.path.insert(0, '/home/t628/projects/ra2-campaign-forge/_r113')
import r113_lib as L
ROOT = L.ROOT
C = L.census(); V2C, T, B, colptr = C['V2C'], C['T'], C['B'], C['colptr']
COLS = set(C['cols'])
TS, TE, RD0, RD1 = L.TEXT0, L.TEXT1, L.RD0, L.RD1
S = json.load(open(os.path.join(ROOT, '_r113/r113c_slots.json')))
iface_vts = set()
for nm, rows in S['detail'].items():
    for r in rows:
        iface_vts.add(int(r[2], 16))
print('iface subobject vtables:', len(iface_vts))

def kind(d):
    if d == 0: return 'zero'
    if TS <= d < TE: return 'text'
    if d in COLS: return 'COL'
    if RD0 <= d < RD1: return 'rdata_other'
    return 'else'

cnt_all = collections.Counter(); cnt_if = collections.Counter()
notCOL = []
for v in V2C:
    t = T[v]; d = L.u32(v + 4 * t)
    k = kind(d); cnt_all[k] += 1
    if v in iface_vts:
        cnt_if[k] += 1
        if k != 'COL': notCOL.append([hex(v), t, hex(d), k])
print('ALL 1214 vtable boundary kind:', dict(cnt_all))
print('IFACE 259 boundary kind:', dict(cnt_if))
print('IFACE non-COL boundaries:', len(notCOL), notCOL[:10])

# 反控 1：故意把边界前移一格（当作"少一槽"）⇒ 那格必然是 .text，说明 T 不是随意取的
back = sum(1 for v in iface_vts if TS <= L.u32(v + 4*(T[v]-1)) < TE)
print('反控1 边界前移一格落在 .text 的接口 vtable 数:', back, '/', len(iface_vts))

# 反控 2：随机基线 —— 全镜像 T==B 的比例
eqB = sum(1 for v in V2C if T[v] == B[v])
print('反控2 全镜像 T==B: %d/%d = %.2f%%' % (eqB, len(V2C), 100.0*eqB/len(V2C)))
print('       接口子对象 T==B: %d/%d = %.2f%%' % (
    sum(1 for v in iface_vts if T[v]==B[v]), len(iface_vts),
    100.0*sum(1 for v in iface_vts if T[v]==B[v])/len(iface_vts)))

# 反控 3：C2 随机置换强零模型（R114 做过 2000 次，此处缩小到 500 次独立复算）
import random
bychd = collections.defaultdict(dict)
for v in V2C:
    bychd[L.u32(V2C[v] + 0x10)][L.u32(V2C[v] + 4)] = v
print('CHD groups:', len(bychd))
