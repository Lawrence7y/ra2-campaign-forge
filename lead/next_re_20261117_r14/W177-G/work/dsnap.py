#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-D 只读快照扩展：在 W177-C 探针之上加
  - RTTI 类名恢复（严格 COL+0xC -> TD+8 链，fail-closed 不猜名）
  - ObjectClass+0x94 层号（signed）
  - 目标格两条链的逐节点 this / +0x94 / +0x80 / owner / RTTI
全部 ReadProcessMemory，不写进程内存、不注入、不 Hook。
"""
import struct

import w177_core as W
import wb_probe as P
import wc_probe as C

# 合法 VA 范围（本镜像 ImageBase 0x400000，size 0x49C110）
VA_LO = 0x00400000
VA_HI = 0x00900000

# RTTI 结构偏移（MSVC，逐字节核对；纪律 5：COL+0xC->TD, TD+8->name）
COL_OFF_TYPE_DESCRIPTOR = 0x0C
TD_OFF_NAME = 0x08
MANGLED_PREFIX = ".?A"   # MSVC: .?AV<Class>@@ / .?AU<Struct>@@


def _plausible_va(v):
    """用于 RTTI 结构（vptr/COL/TD）：须落在镜像范围内。"""
    return bool(v) and VA_LO <= v <= VA_HI


def _plausible_obj(v):
    """对象 this：是堆地址（本镜像堆约 0x10xxxxxx~0x16xxxxxx），只要非零且 4 字节对齐即可。"""
    return bool(v) and (v & 3) == 0 and 0x00100000 <= v <= 0x7FFFFFFF


def rtti_name(m, obj):
    """走 obj->vptr[-4]=COL -> COL+0xC=TD -> TD+8=name。
    返回 (name_or_None, chain_dict)；任一步不可读/不合法 => None（fail-closed，不猜名）。"""
    d = {"obj": hex(obj) if obj else None}
    if not _plausible_obj(obj):
        d["reason"] = "bad obj VA (heap)"
        return None, d
    vptr = m.u32(obj)
    d["vptr"] = hex(vptr) if vptr is not None else None
    if not _plausible_va(vptr):
        d["reason"] = "bad vptr"
        return None, d
    col = m.u32(vptr - 4)
    d["col"] = hex(col) if col is not None else None
    if not _plausible_va(col):
        d["reason"] = "bad COL (vptr-4)"
        return None, d
    td = m.u32(col + COL_OFF_TYPE_DESCRIPTOR)
    d["td"] = hex(td) if td is not None else None
    if not _plausible_va(td):
        d["reason"] = "bad TD (COL+0xC)"
        return None, d
    # 读 TD+8 起最多 96 字节的 mangled name
    raw = b""
    for i in range(96):
        v = m.u8(td + TD_OFF_NAME + i)
        if v is None:
            d["reason"] = "name byte unreadable"
            return None, d
        if v == 0:
            break
        raw += bytes([v])
    if not raw.startswith(MANGLED_PREFIX.encode()):
        d["name_raw"] = raw.decode("latin-1", "replace")
        d["reason"] = "name not MSVC mangled (.?A)"
        return None, d
    name = raw.decode("latin-1", "replace")
    d["name_raw"] = name
    # 粗解 .?AVFoo@@ / .?AUFoo@@ -> Foo（仅展示，判定以 name_raw 为准）
    inner = name[3:]
    if inner.endswith("@@"):
        inner = inner[:-2]
    if len(inner) > 1 and inner[0] in "VU":
        d["name_demangled_guess"] = inner[1:]
    d["ok"] = True
    return name, d


def s32(u):
    if u is None:
        return None
    u &= 0xFFFFFFFF
    return u - 0x100000000 if u & 0x80000000 else u


OFF_LAYER94 = 0x94
OFF_OWNER = 0x21C
OFF_O1 = 0x81
OFF_O2 = 0x74
OFF_O3 = 0x80
OFF_CHAINBIT_8C = 0x8C   # S12-K2: 0->headA(+0xE4), nonzero->headB(+0xE8)

# S12-K2 静态旁路开关（只读轮询）
A_CANPLACE_BYPASS = 0xA8E7AC   # dword !=0 => 0x47C620 return 1
A_HEADA_SCAN_GATE = 0xA8E9A0   # byte ==0 => skip WhatAmI scans (R14_COMMON §0: 恒1)
A_BACKUP_PATH_GATE = 0xA8ED6B  # byte ==0 => entry 0x47C878 branch

def bypass_globals(m):
    return {
        "A8E7AC_dword": m.u32(A_CANPLACE_BYPASS),
        "A8E9A0_byte": m.u8(A_HEADA_SCAN_GATE),
        "A8ED6B_byte": m.u8(A_BACKUP_PATH_GATE),
    }


def node_detail(m, p):
    """格链单节点：this / +0x94 层 / +0x80 / +0x81 / +0x74 / owner / RTTI / typeID。"""
    if not _plausible_obj(p):
        return {"this": hex(p) if p else None, "valid": False, "reason": "bad heap VA"}
    r = {
        "this": hex(p),
        "layer_94": s32(m.u32(p + OFF_LAYER94)),
        "o3_80": m.u8(p + OFF_O3),
        "o1_81": m.u8(p + OFF_O1),
        "o2_74": m.u8(p + OFF_O2),
        "chainbit_8C": m.u8(p + OFF_CHAINBIT_8C),
        "owner_21C": m.u32(p + OFF_OWNER),
        "owner_hex": hex(m.u32(p + OFF_OWNER)) if m.u32(p + OFF_OWNER) else None,
        "next_30": m.u32(p + 0x30),
    }
    name, rtti = rtti_name(m, p)
    r["rtti_name"] = name            # None => [未证] fail-closed
    r["rtti_chain"] = rtti
    try:
        tid, _tp = P.building_type_name(m, p)
        r["building_type_id"] = tid if tid else None
    except Exception:
        r["building_type_id"] = None
    r["valid"] = True
    return r


def cell_detail(m, cx, cy):
    """给定 map cell 坐标，返回两条链的逐节点详情 + 链长。"""
    base = m.u32(P.CELL_ARRAY)
    idx = (cy << 9) + cx
    out = {"cx": cx, "cy": cy, "idx": idx, "array_base": hex(base) if base else None}
    if not base or not (0 <= idx < 0x40000):
        out["valid"] = False
        out["reason"] = "bad base/idx"
        return out
    cell = m.u32(base + idx * 4)
    out["cell"] = hex(cell) if cell else None
    if not cell or cell == P.INVALID_CELL:
        out["valid"] = False
        out["reason"] = "null/invalid cell"
        return out
    out["valid"] = True
    out["selfcx"] = m.u16(cell + P.CELL_CX)
    out["selfcy"] = m.u16(cell + P.CELL_CY)
    for tag, off in (("A", P.CELL_E4), ("B", P.CELL_E8)):
        head = m.u32(cell + off)
        nodes, cyc = [], False
        seen = set()
        p = head
        while p and len(nodes) < 64 and _plausible_obj(p):
            if p in seen:
                cyc = True
                break
            seen.add(p)
            nodes.append(node_detail(m, p))
            p = m.u32(p + 0x30)
        out["head" + tag] = hex(head) if head else None
        out["len" + tag] = len(nodes)
        out["nodes" + tag] = nodes
        out["cyc" + tag] = cyc
    out["max_chain"] = max(out.get("lenA", 0), out.get("lenB", 0))
    return out


def buildings_snapshot(m, ph=None, only_player=False):
    """枚举 BuildingClass，逐对象 this/layer/owner/RTTI/cell/链长摘要。"""
    out = []
    for i, obj in P.enumerate_buildings(m)[2]:
        o = P.one_building(m, i, obj)
        name, rtti = rtti_name(m, obj)
        rec = {
            "idx": i, "this": hex(obj),
            "o1_81": o["o1_81"], "o2_74": o["o2_74"], "o3_80": o["o3_80"],
            "chainbit_8C": m.u8(obj + OFF_CHAINBIT_8C),
            "layer_94": s32(m.u32(obj + OFF_LAYER94)),
            "owner_21C": o["owner_21C"], "owner_hex": o["owner_hex"],
            "is_player": (ph is not None and o["owner_21C"] == ph),
            "building_type_id": o["type"],
            "rtti_name": name,
            "cell": [o["cell"]["cellX"], o["cell"]["cellY"]],
            "cell_valid": o["cell"]["valid"],
            "lenA": o["chains"]["lenA"], "lenB": o["chains"]["lenB"],
            "nodesA": [hex(x) for x in o["chains"]["nodesA"]],
            "nodesB": [hex(x) for x in o["chains"]["nodesB"]],
            "canplace_1AC_u8": m.u8(obj + 0x1AC),
            "canplace_1AC_u32": m.u32(obj + 0x1AC),
        }
        if only_player and not rec["is_player"]:
            continue
        out.append(rec)
    return out


def full_snapshot(m, targets=None, all_buildings=True, only_player=False):
    ph = P.player_house(m)
    snap = {
        "ts": __import__("time").strftime("%Y-%m-%dT%H:%M:%S%z"),
        "frame": m.u32(W.A_FRAME),
        "mode": m.u32(W.A_MODE),
        "bullets": m.u32(W.A_BULLETS),
        "objects": m.u32(W.A_ABSTRACT),
        "playerHouse": hex(ph) if ph else None,
        "credit_30C": m.u32(ph + 0x30C) if ph else None,
        "cam": C.cam_origin(m),
        "bypass": bypass_globals(m),
        "building_array_count": W.building_array(m)[1],
    }
    if all_buildings:
        snap["buildings"] = buildings_snapshot(m, ph, only_player)
    if targets:
        snap["targets"] = [cell_detail(m, tx, ty) for tx, ty in targets]
    return snap
