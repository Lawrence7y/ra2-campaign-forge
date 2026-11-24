#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-C 扩展只读探针：在 wb_probe 之上加 camera scroll origin、cell-by-coords、
目标格链、can-place 相关字段。全部 ReadProcessMemory，不写进程内存/不注入。"""
import struct
import w177_core as W
import wb_probe as P

# camera scroll / view origin (任务给定，只读探测)
A_CAM_X = 0x00886FA0
A_CAM_Y = 0x00886FA4

# can-place 候选字段
OBJ_CANPLACE_1AC = 0x1AC


def cam_origin(m):
    return {"cam_x": m.u32(A_CAM_X), "cam_y": m.u32(A_CAM_Y)}


def cell_at_coords(m, cx, cy):
    """§951 给定 GetCellAt 路径：CellClass* = dword[0x87F924] + ((Y<<9)+X)*4。
    这里 cx,cy 是 map cell 坐标（lepton>>8）。返回 (cellPtr, chains, raw)."""
    base = m.u32(P.CELL_ARRAY)
    idx = (cy << 9) + cx
    if not base or idx < 0 or idx >= 0x40000:
        return {"cx": cx, "cy": cy, "idx": idx, "cell": None, "valid": False,
                "chains": None, "reason": "bad base/idx"}
    cell = m.u32(base + idx * 4)
    valid = bool(cell) and cell != P.INVALID_CELL
    ch = P.cell_chains(m, cell) if valid else None
    return {"cx": cx, "cy": cy, "idx": idx, "cell": cell, "valid": valid,
            "cell_hex": hex(cell) if cell else None,
            "headA": hex(ch["headA"]) if ch and ch["headA"] else None,
            "headB": hex(ch["headB"]) if ch and ch["headB"] else None,
            "lenA": ch["lenA"] if ch else None, "lenB": ch["lenB"] if ch else None,
            "nodesA": [hex(n) for n in ch["nodesA"]] if ch else [],
            "nodesB": [hex(n) for n in ch["nodesB"]] if ch else [],
            "selfcx": ch["selfcx"] if ch else None, "selfcy": ch["selfcy"] if ch else None}


def napowr_objects(m, ph=None):
    """列出全部 NAPOWR 对象，含 type/o1/o2/o3/owner/cell/链/can-place 字段。"""
    out = []
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["type"] != "NAPOWR":
            continue
        rec = {
            "obj": b["obj_hex"], "o1_81": b["o1_81"], "o2_74": b["o2_74"], "o3_80": b["o3_80"],
            "owner": b["owner_hex"], "is_player": (ph is not None and b["owner_21C"] == ph),
            "cellX": b["cell"]["cellX"], "cellY": b["cell"]["cellY"], "valid": b["cell"]["valid"],
            "cell": hex(b["cell"]["cell"]) if b["cell"].get("cell") else None,
            "lenA": b["chains"]["lenA"], "lenB": b["chains"]["lenB"],
            "nodesA": [hex(n) for n in b["chains"]["nodesA"]],
            "nodesB": [hex(n) for n in b["chains"]["nodesB"]],
            "canplace_1AC_u8": m.u8(obj + OBJ_CANPLACE_1AC),
            "canplace_1AC_u32": m.u32(obj + OBJ_CANPLACE_1AC),
        }
        out.append(rec)
    return out


def all_player_building_types(m, ph):
    from collections import Counter
    c = Counter()
    for i, obj in P.enumerate_buildings(m)[2]:
        b = P.one_building(m, i, obj)
        if b["owner_21C"] == ph:
            c[b["type"]] += 1
    return dict(c)


def full_snapshot(m, targets=None):
    """一次完整快照。targets = [(cx,cy),...] 目标格 map 坐标。"""
    ph = P.player_house(m)
    snap = {
        "frame": m.u32(W.A_FRAME),
        "mode": m.u32(W.A_MODE),
        "playerHouse": hex(ph) if ph else None,
        "credit_30C": m.u32(ph + 0x30C) if ph else None,
        "cam": cam_origin(m),
        "napowr": napowr_objects(m, ph),
        "player_building_types": all_player_building_types(m, ph),
    }
    if targets:
        snap["targets"] = [cell_at_coords(m, tx, ty) for tx, ty in targets]
    return snap
