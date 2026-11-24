#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 亲验：用 MSVC RTTI 建「vtable → 类名」全表，并反查 WhatAmI() 类 ID 阶梯。

背景：台账 §629-2 曾签发「镜像无 RTTI（.?AV / COL 全部 0 命中）」。
W106 报称镜像**确有** MSVC RTTI，且 `.data` 里成片 `.?AV...@@`。
Lead 实测：`.data` 里 **962** 个 `.?AV...@@`（`.text`/`.rdata`/`.rsrc`/`.detour` 均 0）
⇒ §629-2 该句**错**（W92 当初很可能只搜了 `.rdata`）。

本脚本打通整条链并输出全表：
    vtable[-1]  ->  COL(CompleteObjectLocator)
    COL+0x0C    ->  pTypeDescriptor (TD)
    TD+0x08     ->  类名字符串 ".?AV<Class>@@"
    vtable+0x2C ->  WhatAmI() 的 `mov eax,N; ret`

用法：python _lead_rtti_map.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

import pefile

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
IMAGE_BASE = 0x400000
TD_NAME_OFF = 0x08      # TypeDescriptor: vftable_ptr(4) + spare(4) + name
COL_TD_OFF = 0x0C       # CompleteObjectLocator: sig(4)+offset(4)+cdOffset(4)+pTypeDescriptor
SLOT_WHATAMI = 0x2C


def sections(pe):
    return [{
        "name": s.Name.decode("latin1").rstrip("\x00"),
        "va": IMAGE_BASE + s.VirtualAddress,
        "vsize": s.Misc_VirtualSize,
        "raw": s.PointerToRawData,
        "rsize": s.SizeOfRawData,
        "exec": bool(s.Characteristics & 0x20000000),
    } for s in pe.sections]


def va2off(secs, va):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rsize"]):
            d = va - s["va"]
            if d < s["rsize"]:
                return s["raw"] + d
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    args = ap.parse_args()

    pe = pefile.PE(str(EXE), fast_load=True)
    data = bytes(pe.__data__)
    secs = sections(pe)

    def u32(va):
        o = va2off(secs, va)
        return None if o is None else int.from_bytes(data[o:o + 4], "little")

    # ---------- 1) 枚举 TypeDescriptor ----------
    pat = re.compile(rb"\.\?AV[A-Za-z0-9_@?$]{2,80}@@")
    td = {}          # TD VA -> class name
    per_sec = {}
    for s in secs:
        blob = data[s["raw"]: s["raw"] + s["rsize"]]
        n = 0
        for m in pat.finditer(blob):
            name_va = s["va"] + m.start()
            td[name_va - TD_NAME_OFF] = m.group().decode("latin1")
            n += 1
        per_sec[s["name"]] = n
    print("=== 1) `.?AV...@@` 命中（按节） ===")
    for k, v in per_sec.items():
        print(f"  {k:<10} {v}")
    print(f"  合计 = {sum(per_sec.values())}   TD 数 = {len(td)}")

    # ---------- 2) 找 COL ----------
    td_set = set(td)
    col2name = {}
    for s in secs:
        blob = data[s["raw"]: s["raw"] + s["rsize"]]
        for i in range(0, len(blob) - 4, 4):
            v = int.from_bytes(blob[i:i + 4], "little")
            if v in td_set:
                col_va = s["va"] + i - COL_TD_OFF
                if col_va >= 0:
                    col2name[col_va] = td[v]
    print(f"\n=== 2) COL 数 = {len(col2name)} ===")

    # ---------- 3) 找 vtable（vptr[-1] == COL） ----------
    vt2name = {}
    for s in secs:
        blob = data[s["raw"]: s["raw"] + s["rsize"]]
        for i in range(0, len(blob) - 4, 4):
            v = int.from_bytes(blob[i:i + 4], "little")
            if v in col2name:
                vt2name[s["va"] + i + 4] = col2name[v]
    print(f"=== 3) vtable 起点数（经 COL 反查） = {len(vt2name)} ===")

    # ---------- 4) 抽样：已知锚点 ----------
    print("\n=== 4) 已知锚点核对 ===")
    anchors = {
        0x7E3EBC: "台账 L2：WhatAmI()==6",
        0x7EB058: "台账 L2：WhatAmI()==15",
        0x7E3AD0: "Lead L2 普查：WhatAmI()==19",
    }
    for a, note in anchors.items():
        print(f"  vtable 0x{a:08X} -> {vt2name.get(a, '[未命中]'):<40} ({note})")

    # ---------- 5) WhatAmI 阶梯（vtable -> N -> 类名） ----------
    rows = []
    for vt, name in vt2name.items():
        fn = u32(vt + SLOT_WHATAMI)
        n = None
        if fn:
            o = va2off(secs, fn)
            if o is not None and o + 6 <= len(data) and data[o] == 0xB8 and data[o + 5] in (0xC3, 0xC2):
                n = int.from_bytes(data[o + 1:o + 5], "little")
        rows.append({"whatami": n, "name": name, "vtable": vt})

    known = [r for r in rows if r["whatami"] is not None and r["whatami"] < 200]
    known.sort(key=lambda r: (r["whatami"], r["vtable"]))
    print(f"\n=== 5) WhatAmI() 类 ID 阶梯（N<200，共 {len(known)} 条） ===")
    by_n = defaultdict(list)
    for r in known:
        by_n[r["whatami"]].append(r["name"])
    for n in sorted(by_n):
        names = sorted(set(by_n[n]))
        print(f"  ID={n:<4} {', '.join(names)}")

    print(f"\n[vtable 无 WhatAmI 或 N>=200 的条数 = {len(rows) - len(known)}]")

    if args.json:
        Path(args.json).write_text(json.dumps(
            {"per_section": per_sec, "td_count": len(td), "col_count": len(col2name),
             "vt2name": {f"0x{k:08X}": v for k, v in vt2name.items()},
             "whatami_rows": [{"n": r["whatami"], "name": r["name"], "vt": f"0x{r['vtable']:08X}"}
                              for r in rows]},
            ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"[out] {args.json}")


if __name__ == "__main__":
    main()
