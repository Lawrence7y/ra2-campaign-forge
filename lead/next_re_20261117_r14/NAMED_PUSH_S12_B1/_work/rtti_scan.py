# -*- coding: utf-8 -*-
"""环①② 取证：18 行逐个解 RTTI / vtable 槽 / 主线判定 / direct callers。"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

rows = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "rows_b1.json"),
                      encoding="utf-8"))

# 已知：BuildingClass 主虚表槽 0 常见 00410260（任务卡给的锚），先自查
def find_main_vtables(rtti_name, slot0_expect=None):
    """在 .rdata/.data 中找所有 COL/TD 链，名字以 rtti_name 结尾的 vtable。"""
    out = []
    for nm, v0, vs, data in C.SECS:
        if nm == ".text":
            continue
        st = 0
        while True:
            i = data.find(b".?AV", st)
            if i < 0:
                break
            td = v0 + i - 8
            nmstr = C.read_cstr(v0 + i, 260)
            if nmstr == rtti_name:
                col = C.u32(td)  # TD[0] 不一定是 COL；TD 结构: pVFTable, spare, name
                # 找 TD 被谁引用（COL+0xC == td）
                st = i + 1
                out.append(dict(td=td, name_va=v0 + i, name=nmstr))
            st = i + 1
    return out


def col_to_td_scan():
    """全镜像扫：找所有 (COL, TD) 对，COL sig==0 且 TD 名 .?AV。"""
    pairs = []
    for nm, v0, vs, data in C.SECS:
        if nm == ".text":
            continue
        for off in range(0, len(data) - 0x14, 4):
            sig = int.from_bytes(data[off:off + 4], "little")
            if sig != 0:
                continue
            td = int.from_bytes(data[off + 0xC:off + 0x10], "little")
            if not td or C.va_sec(td) is None:
                continue
            nm2 = C.read_cstr(td + 8, 260)
            if not nm2.startswith(".?AV"):
                continue
            pairs.append(dict(col=v0 + off, td=td, name=nm2, sec=nm))
    return pairs


if __name__ == "__main__":
    pairs = col_to_td_scan()
    print("COL/TD pairs: %d" % len(pairs))
    bc = [p for p in pairs if p["name"].startswith(".?AVBuildingClass@")]
    print("BuildingClass RTTI pairs:")
    for p in bc:
        print("  COL=%08X TD=%08X %s" % (p["col"], p["td"], p["name"]))
    bt = [p for p in pairs if p["name"].startswith(".?AVBuildingTypeClass@")]
    print("BuildingTypeClass pairs:")
    for p in bt:
        print("  COL=%08X TD=%08X %s" % (p["col"], p["td"], p["name"]))
    # 找所有 vtable：base-4 == COL 的位置
    print("\nvtables whose [-4] is a BuildingClass COL:")
    for p in bc:
        needle = int(p["col"]).to_bytes(4, "little")
        for nm, v0, vs, data in C.SECS:
            if nm == ".text":
                continue
            st = 0
            while True:
                i = data.find(needle, st)
                if i < 0:
                    break
                vb = v0 + i + 4
                print("  vt=%08X slot0=%08X sec=%s" % (vb, C.u32(vb) or 0, nm))
                st = i + 1
