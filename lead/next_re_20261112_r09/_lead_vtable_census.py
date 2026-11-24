#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Lead 亲验：虚拟表普查 + WhatAmI() 类 ID 阶梯。

背景（台账 §629-2 已证）：镜像**无 RTTI**；`.rdata` 里若干 vtable 的槽 11（`+0x2C`）
全部指向 `mov eax,N; ret`，N 唯一 —— 这就是 `WhatAmI()`。

本脚本做三件事（不引用任何既有结论，全部从原始字节重算）：
  1. 枚举所有「像 vtable」的指针数组：连续、每项都指向可执行节、长度 >= MINLEN。
  2. 对每个 vtable 取槽 11，解出 `mov eax,N; ret` 里的 N；输出 N -> vtable 起点 映射。
  3. 对给定的若干 Anchor vtable（已知成员函数，例如 0x7EB058 + slot 107 = 0x51BF90
     `InfantryClass::IsCellOccupied`），报出它的 N —— 用来给类 ID 阶梯找锚点。

用法：
  python _lead_vtable_census.py
  python _lead_vtable_census.py --json out.json
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

import pefile

EXE = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
IMAGE_BASE = 0x400000
MINLEN = 4          # vtable 至少 4 个槽
SLOT_WHATAMI = 11   # +0x2C / 4


def sections(pe):
    out = []
    for s in pe.sections:
        name = s.Name.decode("latin1").rstrip("\x00")
        out.append({
            "name": name,
            "va": IMAGE_BASE + s.VirtualAddress,
            "vsize": s.Misc_VirtualSize,
            "raw_off": s.PointerToRawData,
            "raw_size": s.SizeOfRawData,
            "exec": bool(s.Characteristics & 0x20000000),
        })
    return out


def va_to_off(secs, va: int):
    for s in secs:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["raw_size"]):
            d = va - s["va"]
            if d >= s["raw_size"]:
                return None
            return s["raw_off"] + d
    return None


def is_exec(secs, va: int) -> bool:
    for s in secs:
        if s["exec"] and s["va"] <= va < s["va"] + max(s["vsize"], s["raw_size"]):
            return True
    return False


def u32(buf, off) -> int:
    return int.from_bytes(buf[off:off + 4], "little")


def decode_whatami(pe, secs, buf, fn_va: int):
    """若 fn_va 处是 `B8 imm32 C3`（mov eax, imm32; ret）则返回 imm32，否则 None。"""
    off = va_to_off(secs, fn_va)
    if off is None:
        return None
    b = buf[off:off + 6]
    if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC3:
        return u32(buf, off + 1)
    # 也接受 `mov eax,imm32; retn`（C2 xx xx）
    if len(b) >= 6 and b[0] == 0xB8 and b[5] == 0xC2:
        return u32(buf, off + 1)
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default=None)
    ap.add_argument("--minlen", type=int, default=MINLEN)
    args = ap.parse_args()

    pe = pefile.PE(str(EXE), fast_load=True)
    buf = pe.__data__
    secs = sections(pe)

    rdata = next(s for s in secs if s["name"] == ".rdata")
    lo, hi = rdata["va"], rdata["va"] + rdata["raw_size"]

    # 1) 线性扫 .rdata，找「连续 executable 指针」的最长游程
    runs = []
    cur_start = None
    cur_len = 0
    va = lo
    while va < hi - 4:
        off = va_to_off(secs, va)
        if off is None:
            va += 4
            continue
        p = u32(buf, off)
        ok = p != 0 and is_exec(secs, p)
        if ok:
            if cur_start is None:
                cur_start = va
                cur_len = 0
            cur_len += 1
        else:
            if cur_start is not None and cur_len >= args.minlen:
                runs.append((cur_start, cur_len))
            cur_start, cur_len = None, 0
        va += 4
    if cur_start is not None and cur_len >= args.minlen:
        runs.append((cur_start, cur_len))

    # 2) 每个 vtable 取槽 11
    n_to_vt = defaultdict(list)
    vtables = []
    for start, ln in runs:
        so = va_to_off(secs, start)
        slot_off = so + SLOT_WHATAMI * 4
        if slot_off + 4 > len(buf):
            continue
        fn = u32(buf, slot_off)
        n = decode_whatami(pe, secs, buf, fn)
        vtables.append({"vt": start, "len": ln, "slot11_fn": fn, "whatami": n})
        if n is not None:
            n_to_vt[n].append(start)

    print(f"# {EXE.name}  .rdata 0x{lo:08X}..0x{hi:08X}")
    print(f"# 候选 vtable 游程数 = {len(runs)}   （minlen={args.minlen}）")
    named = [v for v in vtables if v["whatami"] is not None]
    print(f"# 其中槽 11 可解出 mov eax,N;ret 的 = {len(named)}")
    print()
    print("# ---- N -> vtable 起点（按 N 排序）----")
    for n in sorted(n_to_vt):
        vts = ", ".join(f"0x{v:08X}" for v in sorted(n_to_vt[n]))
        print(f"WhatAmI()={n:<3} vtable = {vts}")

    # 3) 锚点检查
    print()
    print("# ---- 锚点核对 ----")
    def probe(vt_va: int, note: str):
        so = va_to_off(secs, vt_va)
        if so is None:
            print(f"  vt 0x{vt_va:08X} 不在任何节  ({note})")
            return None
        fn = u32(buf, so + SLOT_WHATAMI * 4)
        n = decode_whatami(pe, secs, buf, fn)
        size_ok = any(v["vt"] == vt_va for v in vtables)
        print(f"  vt 0x{vt_va:08X}  slot11 fn=0x{fn:08X}  WhatAmI()={n}  "
              f"在游程列表内={size_ok}   ({note})")
        return n

    # 台账 §623-ERR-3 / §629-2 给的锚：InfantryClass vtable = 0x7EB058，slot 107 = 0x51BF90
    z = probe(0x007EB058, "台账称 InfantryClass vtable；slot107 应=0x51BF90")
    if z is not None:
        so = va_to_off(secs, 0x007EB058)
        slot107 = u32(buf, so + 107 * 4)
        print(f"    slot107 实测 = 0x{slot107:08X}   期望 0x0051BF90 : "
              f"{'PASS' if slot107 == 0x0051BF90 else 'FAIL'}")
        print(f"    => InfantryClass 的 WhatAmI() = {z}")
    probed6 = probe(0x007E3EBC, "台账称 WhatAmI()==6 的 vtable")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "rdata": [lo, hi], "runs": len(runs),
            "n_to_vtables": {str(k): v for k, v in n_to_vt.items()},
            "vtables": vtables,
        }, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[out] {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
