# -*- coding: utf-8 -*-
"""NAME-CEILING 内部核查：把 REPORT.md 里出现的每一个派生数字重算一遍。

只读。任何一项与报告不符会打印 FAIL。
"""
import collections
import io
import math
import re
import struct

import pefile

PROJ = r"D:\Project\ra2-campaign-forge"
R14 = PROJ + r"\lead\next_re_20261117_r14"
ATLAS = PROJ + r"\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"
COV = R14 + r"\COVERAGE\coverage.tsv"
VT = PROJ + r"\lead\next_re_20261112_r10\W130_atlas\vtables_rebuilt.tsv"
CEIL = R14 + r"\NAME_CEILING\ceiling.tsv"
EXE = PROJ + r"\ra2youli\gamemd.exe"
TEXT_LO, TEXT_HI = 0x401000, 0x7E038D

fails = []


def chk(name, got, want):
    ok = got == want
    if not ok:
        fails.append((name, got, want))
    print("  %-52s %-10s exp=%-10s %s" % (name, got, want, "OK" if ok else "FAIL"))


atlas = {}
with io.open(ATLAS, encoding="utf-8") as f:
    for ln in f.read().splitlines()[1:]:
        if not ln.strip():
            continue
        p = ln.split("\t")
        atlas[p[0].strip().upper()] = (int(p[7]), p[8] if len(p) > 8 else "")

RE_SUB = re.compile(r"^(sub_|.*::sub_)")
RE_SLOT = re.compile(r"::v?slot\d+$")
RE_RTTI = re.compile(r"\.\?A[VU]")
RE_QUAL = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*::[A-Za-z_~][A-Za-z0-9_~]*")
RE_ASRT = re.compile(r"[A-Za-z0-9_\\/:. -]*\.(?:CPP|cpp|Cpp)\b")

A = B = C = D = N = 0
b_str = b_asrt = 0
asrt_files = set()
rtti_rows = qual_rows = 0
tot_str = 0
all_slot_named = 0
atlas_slot_named = 0
non_slot_named = 0
s10_strict = s11_strict = 0
for ln in io.open(COV, encoding="utf-8").read().splitlines()[1:]:
    p = ln.split("\t")
    if len(p) < 8:
        continue
    nm = p[2].strip()
    if RE_SLOT.search(nm):
        all_slot_named += 1
    e = p[0].strip().upper()
    if e not in atlas:
        continue
    N += 1
    tot_str += 1 if atlas[e][0] > 0 else 0
    if RE_RTTI.search(atlas[e][1]):
        rtti_rows += 1
    if RE_QUAL.search(atlas[e][1]):
        qual_rows += 1
    isA = bool(nm) and not nm.startswith("sub_") and not re.search(r"::sub_", nm)
    if isA:
        A += 1
        non_slot_named += 1 if not RE_SLOT.search(nm) else 0
        if RE_SLOT.search(nm):
            C += 1
            atlas_slot_named += 1
        if p[1] == "S10" and not RE_SLOT.search(nm):
            s10_strict += 1
        if p[1] == "S11" and not RE_SLOT.search(nm):
            s11_strict += 1
    elif not nm:
        D += 1
    else:
        B += 1
        if atlas[e][0] > 0:
            b_str += 1
            mm = RE_ASRT.search(atlas[e][1])
            if mm:
                b_asrt += 1
                asrt_files.add(mm.group(0).split("\\")[-1].lower())

print("[1] 分类与串统计")
chk("A_named", A, 7203)
chk("B_substyle", B, 5713)
chk("C_slotstyle", C, 5831)
chk("D_empty", D, 0)
chk("n", N, 12916)
chk("atlas 内 n_strings>0", tot_str, 1019)
chk("B 类含 strings 行数", b_str, 593)
chk("B 类含断言源文件名行数", b_asrt, 201)
chk("断言源文件去重数", len(asrt_files), 53)
chk("含 RTTI 描述符的行（全表）", rtti_rows, 0)
chk("含 Foo::Bar 形态的行（全表）", qual_rows, 0)
chk("盘上 ::slotN 名总数（全部 coverage）", all_slot_named, 6241)
chk("盘上 ::slotN 名（atlas 内）", atlas_slot_named, 5831)
chk("非 slot 真名（atlas 内）", non_slot_named, 1372)
chk("非 slot 真名占全表百分比(1位小)", round(100.0 * non_slot_named / N, 1), 10.6)
chk("S10 非 slot 真名", s10_strict, 82)
chk("S11 非 slot 真名", s11_strict, 29)

print("\n[2] L2 推导")
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
IMG = pe.get_memory_mapped_image()


def u32(va):
    return struct.unpack("<I", IMG[va - IB: va - IB + 4])[0]


vtr = []
with io.open(VT, encoding="utf-8") as f:
    for ln in f.read().splitlines()[1:]:
        if not ln.strip():
            continue
        p = ln.split("\t")
        vtr.append((int(p[0], 16), p[1], p[2] == "1", int(p[4]), p[5]))


def build(strict):
    m = collections.defaultdict(set)
    for vt, cls, prim, slots, bad in vtr:
        if strict and not (prim and bad == "next-col"):
            continue
        if not re.match(r"^\.\?A[VU]", cls or ""):
            continue
        for k in range(slots):
            v = u32(vt + 4 * k)
            if TEXT_LO <= v < TEXT_HI:
                m[v].add((cls, k))
    return m


for tag, st in (("strict", True), ("loose", False)):
    m = build(st)
    chk("slot map[%s] 唯一函数数" % tag, len(m), 4255 if st else 6256)
    chk("slot map[%s] 多槽指认数" % tag,
        sum(1 for f, v in m.items() if len({(c, k) for c, k in v}) > 1),
        589 if st else 1129)

# 逐子系统 L2（严格）与 ceiling.tsv 对照
L2 = collections.Counter()
L2amb = collections.Counter()
for ln in io.open(COV, encoding="utf-8").read().splitlines()[1:]:
    p = ln.split("\t")
    if len(p) < 8:
        continue
    e = p[0].strip().upper()
    if e not in atlas:
        continue
    nm = p[2].strip()
    if nm and not RE_SUB.match(nm):
        continue
    v = build(True).get(int(e, 16))
    if not v:
        continue
    if len({(c, k) for c, k in v}) > 1:
        L2amb[p[1]] += 1
    else:
        L2[p[1]] += 1
chk("L2 严格合计", sum(L2.values()), 29)
chk("L2 严格 归属不唯一", sum(L2amb.values()), 9)

print("\n[3] ceiling.tsv 与缺口")
rows = []
with io.open(CEIL, encoding="utf-8") as f:
    hdr = f.read().splitlines()
for ln in hdr[1:]:
    rows.append(ln.split("\t"))
chk("ceiling.tsv 数据行数", len(rows), 22)
col = {k: i for i, k in enumerate(hdr[0].split("\t"))}
reach = 0
gap_sum = 0
for r in rows:
    s = r[0]
    n = int(r[col["n"]])
    a = int(r[col["A_named"]])
    l1 = int(r[col["L1"]])
    l2 = int(r[col["L2"]])
    l3 = int(r[col["L3"]])
    b = int(r[col["B_substyle"]])
    d = int(r[col["D_empty"]])
    cof = int(r[col["ceiling_off"]])
    thr = int(r[col["thr_named"]])
    ok = (cof >= thr)
    if r[col["reachable"]] != ("True" if ok else "False"):
        fails.append(("reachable flag " + s, r[col["reachable"]], ok))
    if l1 + l2 + l3 != b + d:
        fails.append((("L1+L2+L3==B+D " + s), l1 + l2 + l3, b + d))
    if cof != a + l1 + l2:
        fails.append(("ceiling_off " + s, cof, a + l1 + l2))
    if thr != math.ceil(0.9 * n):
        fails.append(("thr " + s, thr, math.ceil(0.9 * n)))
    if l2 != L2[s]:
        fails.append(("L2 vs 重算 " + s, l2, L2[s]))
    reach += 1 if ok else 0
    if not ok:
        gap_sum += thr - cof
chk("够门槛子系统数", reach, 8)
chk("够不到子系统数", 22 - reach, 14)
chk("14 个缺口合计", gap_sum, 4500)

print("\n[4] 结论")
if fails:
    print("  !! %d 项不符：" % len(fails))
    for f in fails:
        print("    ", f)
else:
    print("  全部一致。")
