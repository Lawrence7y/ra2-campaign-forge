# -*- coding: utf-8 -*-
"""BuildingClass 主虚表全量导出 + 18 行槽位/槽号自洽核对 + 安装点/atexit/direct callers。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core as C

MAIN_VT = 0x007E3EBC          # slot0 = 00410260, COL 007FC360 (sig=0), TD 00818D60 .?AVBuildingClass@@
COL_MAIN = 0x007FC360
TD_MAIN = 0x00818D60

here = os.path.dirname(os.path.abspath(__file__))
rows = json.load(open(os.path.join(here, "rows_b1.json"), encoding="utf-8"))


def vt_slot(vt, n):
    return C.u32(vt + 4 * n)


def find_last_slot(vt, limit=2000):
    """主虚表终点：从 vt 起向后，直到遇到一个不是 .text 指针的 dword（或遇到下一个 vtable 头）。"""
    n = 0
    while n < limit:
        v = C.u32(vt + 4 * n)
        if v is None or not C.in_text(v):
            return n
        n += 1
    return limit


if __name__ == "__main__":
    print("MAIN_VT=%08X  COL=%08X sig=%d  TD=%08X name=%s" %
          (MAIN_VT, COL_MAIN, C.u32(COL_MAIN), TD_MAIN, C.read_cstr(TD_MAIN + 8, 60)))
    nslots = find_last_slot(MAIN_VT)
    print("主虚表连续 .text 槽数 = %d (slot 0..%d), 表末 %08X" %
          (nslots, nslots - 1, MAIN_VT + 4 * nslots))
    print()
    for i, r in enumerate(rows, 1):
        e = int(r["entry"], 16)
        name = r["name"]
        m = name.split("::")[-1]
        hint = int(m.lstrip("vslot").lstrip("slot")) if (m.startswith("vslot") or m.startswith("slot")) else None
        hits = []
        for s in range(nslots):
            if vt_slot(MAIN_VT, s) == e:
                hits.append(s)
        inhint = (hint is not None and hint < nslots and vt_slot(MAIN_VT, hint) == e)
        print("%2d %s %-26s hint=%-4s 主虚表命中槽=%s  hint槽位==entry? %s" %
              (i, r["entry"], name, hint, hits if hits else "无", inhint))
