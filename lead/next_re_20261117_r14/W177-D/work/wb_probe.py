#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""W177-B 只读探针：在 w177_core 之上实现 §951 取格路径、建筑类型名、
House/credits 读取、逐对象快照。全部 ReadProcessMemory；不写进程内存、不注入。"""
import struct

import w177_core as W

# ---- 全局（已证，见 R13_COMMON §5 / S12-Q2 CELL_PATH.md §5 / §951）----
A_FRAME      = 0x00A8ED84     # frame counter
A_MODE       = 0x00A8B238     # game mode (5 = skirmish/ingame/paused)
A_ABSTRACT_ITEMS = 0x00B0F724   # AbstractClass::Array.Items (base 0xB0F720 +4)
A_ABSTRACT   = 0x00B0F730     # AbstractClass::Array.Count (base +0x10)
A_BUILDING   = 0x00A8EB50     # BuildingClass::Array
A_PLAYER_HOUSE = 0x00A83D4C   # PlayerHouse (HouseClass*)  [docs/re/shroud_click_interaction.md:34]
A_HOUSE_ARRAY = 0x00A80228    # HouseClass::Array (Items +4 = 0xA8022C, Count +0x10 = 0xA80238)

MAP_SINGLETON = 0x0087F7E8    # MapClass singleton
CELL_ARRAY    = 0x0087F924    # dword[CELL_ARRAY] = CellClass* array base
INVALID_CELL  = 0x00ABDC50

BUILDING_VT   = 0x007E3EBC

# ---- 对象字段偏移 ----
O_NEXT   = 0x30      # 格链 next
O_O1     = 0x81      # Limbo bool
O_O2     = 0x74      # 已进入格锁存
O_O3     = 0x80      # 精灵脏标记
O_OWNER  = 0x21C     # owner HouseClass*
O_TYPE   = 0x520     # BuildingTypeClass* (NOT MapClass)
O_LOCX   = 0x9C      # Location.X (lepton)
O_LOCY   = 0xA0      # Location.Y (lepton)

CELL_E4  = 0xE4      # 格链头 A
CELL_E8  = 0xE8      # 格链头 B
CELL_CX  = 0x24      # short CellClass.MapCoords.X (self-check)
CELL_CY  = 0x26      # short CellClass.MapCoords.Y

HOUSE_ARRAYINDEX = 0x30   # HouseClass.ArrayIndex
HOUSE_STARTINGCREDITS = 0x1DC  # StartingCredits (INI Credits), actual = *100
HOUSE_CURRENTPLAYER = 0x1EC    # bool CurrentPlayer
HOUSE_PLAYERCONTROL = 0x1ED    # bool PlayerControl


def s32(u):
    u &= 0xFFFFFFFF
    return u - 0x100000000 if u & 0x80000000 else u


def read_bytes(m, va, n):
    """ReadProcessMemory bulk read; returns bytes or None."""
    import ctypes
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    ok = m._rd(va, buf, n)
    return ok


def ascii_at(m, va, n=16):
    raw = b""
    for i in range(n):
        v = m.u8(va + i)
        if v is None or v == 0 or v < 0x20 or v > 0x7e:
            break
        raw += bytes([v])
    return raw.decode("latin-1")


def building_type_name(m, obj):
    """读 BuildingTypeClass 的短 ID 串（type+0x24）。返回 (name, type_ptr)."""
    tp = m.u32(obj + O_TYPE)
    if not tp:
        return "", None
    return ascii_at(m, tp + 0x24, 12), tp


def obj_to_cell(m, obj):
    """§951 路径 A：obj -> (cellX,cellY,idx,cellArray,CellClass*)；带越界/空槽 guard。"""
    x = s32(m.u32(obj + O_LOCX)) if m.u32(obj + O_LOCX) is not None else None
    y = s32(m.u32(obj + O_LOCY)) if m.u32(obj + O_LOCY) is not None else None
    if x is None or y is None:
        return None
    cx = x >> 8   # arithmetic shift (sar 8)
    cy = y >> 8
    idx = (cy << 9) + cx
    base = m.u32(CELL_ARRAY)
    res = {"locx": x, "locy": y, "cellX": cx, "cellY": cy, "idx": idx,
           "cellArray": base, "cell": None, "valid": False, "reason": ""}
    if base is None or base == 0:
        res["reason"] = "null cellArray"
        return res
    if idx < 0 or idx >= 0x40000:
        res["reason"] = "idx out of range"
        return res
    cell = m.u32(base + idx * 4)
    res["cell"] = cell
    if not cell:
        res["reason"] = "null cell slot"
    elif cell == INVALID_CELL:
        res["reason"] = "InvalidCell sentinel"
    else:
        res["valid"] = True
    return res


def chain(m, head, maxn=64):
    """沿 elem+0x30 遍历一条格链，返回 (nodes[list[int]], length, cycle)."""
    nodes = []
    seen = set()
    p = head
    cycle = False
    while p and len(nodes) < maxn:
        if p in seen:
            cycle = True
            break
        seen.add(p)
        nodes.append(p)
        nxt = m.u32(p + O_NEXT)
        p = nxt
    if p and len(nodes) >= maxn:
        cycle = True
    return nodes, len(nodes), cycle


def cell_chains(m, cell):
    """读 cell+0xE4 / +0xE8 两条链表头并遍历。"""
    if not cell:
        return {"cell": cell, "headA": None, "headB": None,
                "nodesA": [], "lenA": 0, "nodesB": [], "lenB": 0,
                "cycA": False, "cycB": False, "selfcx": None, "selfcy": None}
    hA = m.u32(cell + CELL_E4)
    hB = m.u32(cell + CELL_E8)
    nA, lA, cA = chain(m, hA)
    nB, lB, cB = chain(m, hB)
    return {"cell": cell, "headA": hA, "headB": hB,
            "nodesA": nA, "lenA": lA, "nodesB": nB, "lenB": lB,
            "cycA": cA, "cycB": cB,
            "selfcx": m.u16(cell + CELL_CX), "selfcy": m.u16(cell + CELL_CY)}


def enumerate_buildings(m, maxn=20000):
    """从 AbstractClass::Array 用 vftable 分类枚举 BuildingClass。"""
    aitems = m.u32(A_ABSTRACT_ITEMS)
    acount = m.u32(A_ABSTRACT)
    out = []
    if aitems and acount and 0 < acount < maxn:
        for i in range(acount):
            p = m.u32(aitems + 4 * i)
            if not p:
                continue
            if m.u32(p) == BUILDING_VT:
                out.append((i, p))
    return aitems, acount, out


def one_building(m, idx, obj):
    name, tp = building_type_name(m, obj)
    cell = obj_to_cell(m, obj)
    chains = cell_chains(m, cell["cell"]) if cell and cell.get("valid") else cell_chains(m, None)
    owner = m.u32(obj + O_OWNER)
    return {
        "idx": idx, "obj": obj, "obj_hex": hex(obj),
        "type": name, "type_ptr": hex(tp) if tp else None,
        "o1_81": m.u8(obj + O_O1), "o2_74": m.u8(obj + O_O2), "o3_80": m.u8(obj + O_O3),
        "owner_21C": owner, "owner_hex": hex(owner) if owner else None,
        "cell": cell, "chains": chains,
    }


def player_house(m):
    ph = m.u32(A_PLAYER_HOUSE)
    return ph


def house_array(m):
    items = m.u32(A_HOUSE_ARRAY + 4)
    count = m.u32(A_HOUSE_ARRAY + 0x10)
    houses = []
    if items and count and 0 < count < 64:
        for i in range(count):
            h = m.u32(items + 4 * i)
            if h:
                houses.append((i, h))
    return items, count, houses


def scan_dword(m, base, size, value, max_hits=64):
    """在 [base, base+size) 扫描 4 字节对齐 dword == value。返回偏移列表。"""
    buf = read_bytes(m, base, size)
    if buf is None:
        return []
    hits = []
    target = struct.pack("<I", value & 0xFFFFFFFF)
    for off in range(0, size - 3, 4):
        if buf[off:off + 4] == target:
            hits.append(off)
            if len(hits) >= max_hits:
                break
    return hits


def globals_snapshot(m):
    return {
        "frame": m.u32(A_FRAME),
        "mode": m.u32(A_MODE),
        "objects": m.u32(A_ABSTRACT),
        "playerHouse": player_house(m),
        "playerHouse_hex": hex(player_house(m)) if player_house(m) else None,
    }
