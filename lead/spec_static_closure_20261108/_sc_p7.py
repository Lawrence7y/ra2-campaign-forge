# -*- coding: utf-8 -*-
# _sc_p7.py — P7 专扫：vtable[65] (+0x104) 槽位全集（RTTI 全链，纯字节解析，无需反汇编）
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/spec_static_closure_20261108/_sc_p7.py"
import struct, hashlib, time

T0 = time.time()
PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(PATH, "rb").read()
print("R0 SHA256", hashlib.sha256(data).hexdigest())
print("R0 BYTES", len(data))
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
coff = e_lfanew + 4
machine, nsec, _1, _2, _3, optsize, _4 = struct.unpack_from("<HHIIIHH", data, coff)
opt = coff + 20
imagebase = struct.unpack_from("<I", data, opt + 28)[0]
sec0 = opt + optsize
SECTIONS = []
for i in range(nsec):
    o = sec0 + 40 * i
    name = data[o:o + 8].rstrip(b"\0").decode("ascii", errors="replace")
    vsize, va, rsize, raw = struct.unpack_from("<IIII", data, o + 8)
    chars = struct.unpack_from("<I", data, o + 36)[0]
    SECTIONS.append((name, va, vsize, raw, rsize, chars))
SEC = {nm: (imagebase + va, vsz, raw, rsz) for nm, va, vsz, raw, rsz, ch in SECTIONS}
TEXT_VA, TEXT_VSZ, TEXT_RAW, TEXT_RSZ = SEC[".text"]

def sec_of(va):
    rva = va - imagebase
    for nm, sva, vsz, raw, rsz, ch in SECTIONS:
        if sva <= rva < sva + max(vsz, rsz):
            return nm
    return None

def va2off(va):
    rva = va - imagebase
    for nm, sva, vsz, raw, rsz, ch in SECTIONS:
        if sva <= rva < sva + max(vsz, rsz):
            d = rva - sva
            return raw + d if d < rsz else None
    return None

def u32(va):
    o = va2off(va)
    return None if o is None else struct.unpack_from("<I", data, o)[0]

def is_text(va):
    return sec_of(va) == ".text"

td_map = {}
for nm in (".data", ".rdata"):
    sva, vsz, raw, rsz = SEC[nm]
    blob = data[raw:raw + rsz]
    start = 0
    while True:
        i = blob.find(b".?A", start)
        if i < 0:
            break
        j = blob.find(b"\0", i)
        td_map[imagebase + sva + i - 8] = blob[i:j if j > 0 else i + 64].decode("ascii", errors="replace")
        start = i + 1
rdata_lo, rdata_vsz, rdata_raw, rdata_rsz = SEC[".rdata"]
rvals = {}
blob = data[rdata_raw:rdata_raw + rdata_rsz]
for k in range(0, len(blob) - 3, 4):
    rvals.setdefault(struct.unpack_from("<I", blob, k)[0], []).append(rdata_lo + k)
print("TD=%d rvals=%d" % (len(td_map), len(rvals)))

def vt_len(vt, maxn=0x400):
    """vftable 长度：从 vt 起连续的 .text-VA 或 0 的 dword 数"""
    n = 0
    while n < maxn:
        v = u32(vt + 4 * n)
        if v is None:
            break
        if v == 0 or is_text(v):
            n += 1
        else:
            break
    return n

BASE65 = 0x5F4B10
overwrites = {}
base_slots = []
short_vts = 0
vts_total = 0
for td_key, name in td_map.items():
    abs_td = td_key - imagebase
    for pos in rvals.get(abs_td, []):
        col = pos - 12          # ★ 命中位置 = COL+12 (pTypeDescriptor 字段)，COL 基址 = pos-12
        if col < rdata_lo:
            continue
        if u32(col) != 0:
            continue
        if u32(col + 12) != abs_td:
            continue
        for vtp in rvals.get(col, []):
            vt = vtp + 4
            vts_total += 1
            L = vt_len(vt)
            s0 = u32(vt)
            if s0 is None or not is_text(s0):
                continue
            if L < 66:
                short_vts += 1
                continue          # ★ 短表无槽65；+0x104 落在表外，不参与
            s64 = u32(vt + 0x100)
            s65 = u32(vt + 0x104)
            if not (is_text(s64) or s64 == 0):
                continue
            if s65 is None or not is_text(s65):
                continue
            rec = (vt, name, u32(col + 4), L)
            if s65 == BASE65:
                base_slots.append(rec)
            else:
                overwrites.setdefault(s65, []).append(rec)

print("vftable 候选=%d 其中长度<66(无槽65)=%d" % (vts_total, short_vts))
print("P7 槽65==基实现0x5F4B10 的 vftable=%d 张：" % len(base_slots))
for vt, name, coff, L in sorted(base_slots):
    print("   base vt=0x%08X len=%d %s COLoff=0x%X" % (vt, L, name, coff))
print("P7 槽65!=基实现 的覆写值=%d 个：" % len(overwrites))

def e8_callers(fn):
    out = []
    start = TEXT_RAW
    endt = TEXT_RAW + TEXT_RSZ
    first = struct.pack("<B", 0xE8)
    while True:
        i = data.find(first, start, endt)
        if i < 0:
            break
        rel = struct.unpack_from("<i", data, i + 1)[0]
        site = TEXT_VA + (i - TEXT_RAW)
        if site + 5 + rel == fn:
            out.append(site)
        start = i + 1
    return out

for fn, recs in sorted(overwrites.items()):
    o = va2off(fn)
    head = data[o:o + 6].hex() if o else "?"
    callers = e8_callers(fn)
    print("   fn=0x%08X 头6B=%s vftable数=%d E8直调=%s" % (fn, head, len(recs), [hex(v) for v in callers]))
    for vt, name, coff, L in sorted(recs):
        print("      vt=0x%08X len=%d %s COLoff=0x%X" % (vt, L, name, coff))
print("P7 VAL .rdata 内 0x5F4B10 出现=%d (F8_review R6:230=16)" % len(rvals.get(0x5F4B10, [])))
print("P7 VAL 16 张 base vftable 的槽位位置 vs .rdata 中 0x5F4B10 的 16 处位置:")
pos16 = set(rvals.get(0x5F4B10, []))
calc = set(vt + 0x104 for vt, name, coff, L in base_slots)
print("   位置完全一致=%s (差集=%s)" % (pos16 == calc, [hex(x) for x in pos16 ^ calc]))
print("P7 全文件（4对齐）6 个槽65值的 dword 分布（补 .data 等段）：")
for v in (0x5F4B10, 0x422C70, 0x43CEA0, 0x71CC50, 0x73B0B0, 0x749B20):
    pat = struct.pack("<I", v)
    hits = []
    s = 0
    while True:
        i = data.find(pat, s)
        if i < 0:
            break
        if i % 4 == 0:
            hits.append(i)
        s = i + 1
    locs = {}
    for i in hits:
        nm = None
        rva = None
        for n2, sva, vsz, raw, rsz, ch in SECTIONS:
            if raw <= i < raw + rsz:
                nm = n2
                rva = imagebase + sva + (i - raw)
        locs.setdefault(nm, []).append(rva)
    print("   0x%08X: %s" % (v, {k: [hex(x) for x in vs] for k, vs in locs.items()}))
# 校验
def rtti_of_vftable(vt):
    col = u32(vt - 4)
    if col is None or sec_of(col) != ".rdata" or u32(col) != 0:
        return None
    return (col, u32(col + 4), td_map.get(imagebase + (u32(col + 12) or 0)))
for vt in (0x7F4348, 0x7E85D4, 0x7E3354, 0x7F5C70, 0x7F6318):
    print("RTTI vt=0x%08X -> %s" % (vt, rtti_of_vftable(vt)))
print("RUN %.1fs" % (time.time() - T0))
