#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r115_lib.py —— R115 共享底座：vtable 结构末端判据（槽数的独立上界与精确性）。

本轮新增判据（不依赖 T 尺 = "连续落在 .text 的 dword 数"）：
  S 尺（Structural end）: vtable 起点 v 之后，第一个**不是**方法槽的 dword 的位置。
  判据：MSVC 在同一 CHD 组的 vtable 是**首尾相接**排布的，且每个 vtable 前紧贴 4 字节
  的 COL 指针（R113 已用全 .rdata 普查证实 1214 个）。因此在 v 之后沿 .rdata 线扫描，
  第一个「其值本身是一个合法 COL 起点」的 dword 位置 p，就是**下一个 vtable 的 COL 指针**，
  故 (p - v)/4 是 v 的槽数的**结构上界**，且当该 p 恰为下一个 COL 指针时是**精确值**。

  这条判据与 T 尺**判据来源独立**（T 尺看 .text 归属，S 尺看 COL 指针排布），
  故 T == S 是一个不依赖外部头文件的交叉验证。

反控（必须全部有牙，任何一条 0 违例都说明反控无效）：
  K1 人为把边界后移一格（当作"多一槽"）⇒ 那一格必须不是合法方法入口
  K2 人为把边界前移一格（当作"少一槽"）⇒ 那一格必须是 .text
  K3 随机基线：全镜像 T == B 的比例（B 尺无 .text 判据时必须明显低于 100%）
"""
import collections, json, os, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
sys.path.insert(0, os.path.join(ROOT, '_r113'))
import r113_lib as L

raw, fo, u32, i32 = L.raw, L.fo, L.u32, L.i32
TS, TE = L.TEXT0, L.TEXT1
RD0, RD1 = L.RD0, L.RD1
COLS = None


def census():
    return L.census()


def cols_set():
    global COLS
    if COLS is None:
        COLS = set(census()['cols'])
    return COLS


def slot_scale_S(v):
    """S 尺：从 v 起沿 .rdata 线扫，第一个「值 ∈ 合法 COL 集合」的 dword 的下标即槽数。
    返回 (n, stop_va)。若扫到 RD1 仍未遇到 ⇒ (None, None)，不猜。"""
    cs = cols_set()
    n = 0
    while v + 4 * n + 4 <= RD1:
        d = u32(v + 4 * n)
        if d in cs:
            return n, v + 4 * n
        n += 1
        if n > 4000:
            return None, None
    return None, None


def B_scale(v, colptr_sorted):
    """B 尺（R113 已实现，此处独立重写以求可复算）：下一个 COL 指针与 v 之间的 dword 数。"""
    p = v - 4
    i = colptr_sorted.index(p) if p in colptr_sorted else None
    if i is None:
        return None
    nxt = colptr_sorted[i + 1] if i + 1 < len(colptr_sorted) else RD1
    return (nxt - v) // 4


def iface_subobj_vts(slots_json=None):
    """R113 链 H 的「接口子对象 vtable」全集（N != 0 的 10 个接口的装配点）。"""
    p = slots_json or os.path.join(ROOT, '_r113/r113c_slots.json')
    S = json.load(open(p))
    out = {}
    for nm, rows in S['detail'].items():
        out[nm] = sorted(set(int(r[2], 16) for r in rows))
    return out


def boundary_kind(d):
    if d == 0:
        return 'zero'
    if TS <= d < TE:
        return 'text'
    if d in cols_set():
        return 'COL'
    if RD0 <= d < RD1:
        return 'rdata_other'
    return 'else'


def entry_at(a):
    """该地址是否是一个可当方法入口的地址（在 .text 且是已知指令起点）。"""
    return TS <= a < TE and a in L.STARTS
