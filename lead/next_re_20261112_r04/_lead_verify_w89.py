#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lead 独立核验 W89 的两条承重断言。

A. `0x0051C2D3` 是否在函数 `0x0051BF90` 内；该入口是否只被 InfantryClass 虚表 `+0x1AC` 引用。
   做法：定位 0x51BF90 前的函数序言；在全镜像搜 4 字节小端 `0x0051BF90` 的所有出现，
        并判断每处落在哪个虚拟表（打印表基址与槽偏移）。
B. `0x0087E8E0`（PathFinder GenerationStamp 候选）在对照臂是否全程 0xFFFFFFFF，
   在 Hunt 臂是否开火前就已增长。
"""
import json
from pathlib import Path

import pefile

BASE = Path(r"D:\Project\ra2-campaign-forge")
EXE = BASE / r"ra2bench\gamemd.exe"


def verify_static():
    print("=" * 80)
    print("A · 0x0051C2D3 归属与引用")
    print("=" * 80)
    data = EXE.read_bytes()
    pe = pefile.PE(data=data, fast_load=False)
    ib = pe.OPTIONAL_HEADER.ImageBase

    def foff(va):
        rva = va - ib
        for s in pe.sections:
            if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
                return s.PointerToRawData + (rva - s.VirtualAddress)
        raise ValueError(hex(va))

    # 1) 找 0x51BF90 的函数序言（前 0x40 字节里找 55 8B EC 之类）
    fn = 0x0051BF90
    o = foff(fn)
    print(f"  函数候选入口 0x{fn:08X}  bytes = {data[o:o+16].hex(' ').upper()}")

    # 2) 全镜像搜 0x0051BF90 的小端出现
    pat = fn.to_bytes(4, "little")
    hits = []
    start = 0
    while True:
        i = data.find(pat, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    print(f"  小端 {pat.hex()} 全文件命中 {len(hits)} 处")
    for off in hits:
        # off -> VA（按节）
        va = None
        sec_name = None
        for s in pe.sections:
            if s.PointerToRawData <= off < s.PointerToRawData + max(s.SizeOfRawData, 1):
                va = ib + s.VirtualAddress + (off - s.PointerToRawData)
                sec_name = s.Name.rstrip(b"\0").decode()
                break
        print(f"    文件偏移 0x{off:06X} -> VA 0x{va:08X}  节 {sec_name}")

    # 3) 若有 .rdata 命中，判断落在哪个虚表：向前找连续的指针数组起点太复杂，
    #    改为直接打印该地址前后 8 个 dword，人工看表边界。
    for off in hits:
        for s in pe.sections:
            if s.PointerToRawData <= off < s.PointerToRawData + max(s.SizeOfRawData, 1):
                va = ib + s.VirtualAddress + (off - s.PointerToRawData)
                nm = s.Name.rstrip(b"\0").decode()
                break
        if nm != ".rdata":
            continue
        print(f"\n  --- .rdata 命中 0x{va:08X} 附近 dword ---")
        base = off - 8 * 4
        for k in range(-8, 9):
            oo = off + k * 4
            if oo < 0 or oo + 4 > len(data):
                continue
            v = int.from_bytes(data[oo:oo + 4], "little")
            mark = "  <<< 0x0051BF90" if k == 0 else ""
            print(f"    0x{va + k*4:08X}  (k={k:+d})  0x{v:08X}{mark}")

    # 4) InfantryClass vtable 断言：0x007EB204 = 0x007EB058 + 0x1AC ?
    vtb = 0x007EB058
    print(f"\n  InfantryClass 候选虚表基址 0x{vtb:08X}；+0x1AC = 0x{vtb + 0x1AC:08X}")
    oo = foff(vtb + 0x1AC)
    val = int.from_bytes(data[oo:oo + 4], "little")
    print(f"  读 [0x{vtb+0x1AC:08X}] = 0x{val:08X}  {'== 0x0051BF90' if val == fn else ''}")


def verify_dynamic():
    print()
    print("=" * 80)
    print("B · 0x0087E8E0 对照臂 vs Hunt 臂")
    print("=" * 80)

    def scan(path: Path, label: str):
        vals = []
        a8 = []
        frames = []
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d = json.loads(line)
                if d.get("kind") != "sample":
                    continue
                v = d.get("X87E8E0")
                if v is not None:
                    vals.append(v)
                a8.append(d.get("A8ED50") or 0)
                frames.append(d.get("frame"))
        if not vals:
            print(f"  {label}: 无 X87E8E0 字段")
            return
        uniq = set(vals)
        changes = sum(1 for i in range(1, len(vals)) if vals[i] != vals[i - 1])
        first_a8 = next((i for i, v in enumerate(a8) if v), None)
        print(
            f"  {label}: n={len(vals)} 首值={vals[0]} 末值={vals[-1]} "
            f"唯一值数={len(uniq)} 变化次数={changes}"
        )
        print(f"     A8ED50 首个非零样本 idx={first_a8}")
        if first_a8 is not None and first_a8 > 0:
            pre = vals[:first_a8]
            print(f"     开火前 X87E8E0: 首={pre[0]} 末={pre[-1]} 变化={sum(1 for i in range(1,len(pre)) if pre[i]!=pre[i-1])}")

    C = BASE / r"lead\next_re_20261112_r03\W85_pressure\out"
    scan(C / "trip_control_dose1500_static" / "run.ndjson", "control(dose1500 静态)")
    for name in ("trip_pressure_P4_nonacnst_crash", "trip_pressure_P3_notanks_crash",
                 "trip_pressure_dose400_crash", "trip_pressure_dose1500_crash"):
        p = C / name / "run.ndjson"
        if p.exists():
            scan(p, name)


if __name__ == "__main__":
    verify_static()
    verify_dynamic()
