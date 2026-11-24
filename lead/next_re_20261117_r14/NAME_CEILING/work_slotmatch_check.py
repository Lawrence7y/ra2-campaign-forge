# -*- coding: utf-8 -*-
"""NAME-CEILING 内部核查：盘上既有 ::slotN 名与本卡虚表推导的一致度分级。

分三级判定（避免单一口径掩盖差异）：
  in_map      该函数出现在推导图的任一槽里（通道覆盖）
  class_match 且类名一致（demangle 后）
  both        类名与槽号都一致
"""
import collections
import io
import re
import struct

import pefile

PROJ = r"D:\Project\ra2-campaign-forge"
VT = PROJ + r"\lead\next_re_20261112_r10\W130_atlas\vtables_rebuilt.tsv"
COV = PROJ + r"\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
EXE = PROJ + r"\ra2youli\gamemd.exe"
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()


def u32(va):
    return struct.unpack("<I", IMG[va - IB: va - IB + 4])[0]


def dem(n):
    m = re.match(r"^\.\?A[VU](.+)@@$", n)
    return m.group(1) if m else n


def build(keep):
    m = collections.defaultdict(set)
    with io.open(VT, encoding="utf-8") as f:
        for ln in f.read().splitlines()[1:]:
            if not ln.strip():
                continue
            p = ln.split("\t")
            if not keep(p[2], p[5]):
                continue
            vt, cls, n = int(p[0], 16), p[1], int(p[4])
            for k in range(n):
                v = u32(vt + 4 * k)
                if TEXT_LO <= v < TEXT_HI:
                    m[v].add((dem(cls), k))
    return m


RE_SLOT = re.compile(r"::v?slot(\d+)$")
named = []
with io.open(COV, encoding="utf-8") as f:
    for ln in f.read().splitlines()[1:]:
        p = ln.split("\t")
        if len(p) < 8:
            continue
        nm = p[2].strip()
        mm = RE_SLOT.search(nm)
        if mm:
            named.append((int(p[0], 16), p[0], nm, nm[:mm.start()], int(mm.group(1))))
print("盘上 ::slotN/::vslotN 命名 %d 条" % len(named))

for tag, keep in (("strict", lambda p, t: p == "1" and t == "next-col"),
                  ("loose", lambda p, t: True)):
    m = build(keep)
    in_map = clsm = both = 0
    cls_bad = []
    slot_bad = []
    for ea, hexe, nm, cn, k in named:
        d = m.get(ea)
        if not d:
            continue
        in_map += 1
        if any(c == cn for c, _ in d):
            clsm += 1
            if any(c == cn and k2 == k for c, k2 in d):
                both += 1
            elif len(slot_bad) < 6:
                slot_bad.append((hexe, nm, sorted(d)))
        elif len(cls_bad) < 6:
            cls_bad.append((hexe, nm, sorted(d)))
    print("\n[%s] 槽内唯一函数 %d" % (tag, len(m)))
    print("    in_map %d / class_match %d / class+slot %d" % (in_map, clsm, both))
    print("    类名不一致样本:")
    for x in cls_bad:
        print("      ", x)
    print("    槽号不一致样本:")
    for x in slot_bad:
        print("      ", x)
