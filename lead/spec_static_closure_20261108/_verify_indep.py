# -*- coding: utf-8 -*-
# _verify_indep.py — 独立复核：从「槽值」反向回推 RTTI（不复用 _sc_p7.py 的 COL 枚举方向）
# 只读 ra2youli/gamemd.exe 磁盘镜像；输出仅到 stdout。
import struct, hashlib

P = r"D:/Project/ra2-campaign-forge/ra2youli/gamemd.exe"
d = open(P, "rb").read()
print("SHA256 =", hashlib.sha256(d).hexdigest(), "BYTES =", len(d))
e = struct.unpack_from("<I", d, 0x3C)[0]
coff = e + 4
machine, nsec, _ts, _pt, _ns, optsize, _ch = struct.unpack_from("<HHIIIHH", d, coff)
opt = coff + 20
ib = struct.unpack_from("<I", d, opt + 28)[0]
sec0 = opt + optsize
S = []
for i in range(nsec):
    o = sec0 + 40 * i
    nm = d[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
    vsz, va, rsz, raw = struct.unpack_from("<IIII", d, o + 8)
    S.append((nm, va, vsz, raw, rsz))

def sec_of_va(x):
    r = x - ib
    for nm, va, vsz, raw, rsz in S:
        if va <= r < va + max(vsz, rsz):
            return nm
    return None

def va2off(x):
    r = x - ib
    for nm, va, vsz, raw, rsz in S:
        if va <= r < va + max(vsz, rsz):
            dd = r - va
            return raw + dd if dd < rsz else None
    return None

def u32(x):
    o = va2off(x)
    return None if o is None else struct.unpack_from("<I", d, o)[0]

def is_text(x):
    return sec_of_va(x) == ".text"

# TD name map: key = 绝对 VA of TypeDescriptor name field (which points to ".?AV....@@")
td = {}
for nm in (".data", ".rdata"):
    va, vsz, raw, rsz = [t for t in S if t[0] == nm][0][1:]
    blob = d[raw:raw + rsz]
    st = 0
    while True:
        i = blob.find(b".?A", st)
        if i < 0:
            break
        j = blob.find(b"\0", i)
        # COL+12 存「绝对 VA」的 TD name 字段。td 键用同一绝对 VA。
        # 注意 blob 取自 raw 文件偏移，其 VA = ib + section_RVA + i，须显式加 ib
        # （section 元组里存的是 RVA，不是 VA）。
        td[ib + va + i] = blob[i:j if j > 0 else i + 64].decode("ascii", "replace")
        st = i + 1
print("TD names =", len(td))

# rdata as VA-keyed dwords
rva, rvsz, rraw, rrsz = [t for t in S if t[0] == ".rdata"][0][1:]
rlo = ib + rva
blob = d[rraw:rraw + rrsz]
rvals = {}
for k in range(0, len(blob) - 3, 4):
    rvals.setdefault(struct.unpack_from("<I", blob, k)[0], []).append(rlo + k)

# ---------- 独立方向：从每个「槽值 dword」反推 vt = pos-0x104，再经 vt-4 的 COL 找类名 ----------
SLOTS = {0x5F4B10: "BASE", 0x422C70: "OV1", 0x43CEA0: "OV2",
         0x71CC50: "OV3", 0x73B0B0: "OV4", 0x749B20: "OV5"}
print("\n[P7 反推] 全文件 4 对齐 dword 中 6 个槽值的分布 + 反推 RTTI 类名")
all_pos = []
for val, tag in sorted(SLOTS.items()):
    pat = struct.pack("<I", val)
    hits = []
    s = 0
    while True:
        i = d.find(pat, s)
        if i < 0:
            break
        if i % 4 == 0:
            hits.append(i)
        s = i + 1
    locs = {}
    for i in hits:
        nm = None
        vax = None
        for n2, sva, vsz, raw, rsz in S:
            if raw <= i < raw + rsz:
                nm = n2
                vax = ib + sva + (i - raw)
        locs.setdefault(nm, []).append(vax)
        all_pos.append((val, vax, nm))
    print("  %s 0x%08X count=%d locs=%s" % (tag, val, len(hits), {k: [hex(x) for x in v] for k, v in locs.items()}))
print("  TOTAL slot dwords =", len(all_pos), " all in .rdata =", all(x[2] == ".rdata" for x in all_pos))

# 对每个命中位置 pos，vt = pos - 0x104；读 u32(vt-4)=COL；COL+12 应指回 TD 名
print("\n[P7 反推] 每处 pos -> vt=pos-0x104 -> COL -> TD 名")
named = 0
for val, pos, nm in sorted(all_pos, key=lambda t: (t[0], t[1])):
    vt = pos - 0x104
    col = u32(vt - 4)
    name = None
    if col is not None and sec_of_va(col) == ".rdata" and u32(col) == 0:
        tf = u32(col + 12)
        if tf is not None:
            # COL+12 = TypeDescriptor 基址（vfptr 4B + spare 4B + name），故名字在 +8
            o = va2off(tf + 8)
            if o is not None:
                raw = d[o:o + 64]
                z = raw.find(b"\0")
                cand = raw[:z if z > 0 else 64]
                if cand.startswith(b".?A"):
                    name = cand.decode("ascii", "replace")
    ok = name is not None
    named += 1 if ok else 0
    print("  pos=0x%08X val=0x%08X vt=0x%08X COL=0x%08X NAME=%s" %
          (pos, val, vt, col if col else 0, name))

# ---------- P8 独立校验：三张 vtable 的 RTTI 名 ----------
print("\n[P8] 三张 vtable 的 RTTI 名（独立解析）")
for vt in (0x7E3354, 0x7F5C70, 0x7F6318):
    col = u32(vt - 4)
    tf = u32(col + 12) if col else None
    name = None
    if tf is not None:
        o = va2off(tf + 8)   # COL+12 = TD 基址；name 字段在 +8
        if o is not None:
            raw = d[o:o + 64]
            z = raw.find(b"\0")
            cand = raw[:z if z > 0 else 64]
            if cand.startswith(b".?A"):
                name = cand.decode("ascii", "replace")
    print("  vt=0x%08X COL=0x%08X NAME=%s" % (vt, col if col else 0, name))

# ---------- P6 独立校验 ----------
print("\n[P6] 静态数值与文件映射")
print("  qword@0x7E1738 = 0x%016X double = %r" %
      (struct.unpack_from("<Q", d, va2off(0x7E1738))[0],
       struct.unpack_from("<d", d, va2off(0x7E1738))[0]))
print("  qword@0x7E1728 = 0x%016X double = %r" %
      (struct.unpack_from("<Q", d, va2off(0x7E1728))[0],
       struct.unpack_from("<d", d, va2off(0x7E1728))[0]))
print("  va2off(0xB0CD48) =", va2off(0xB0CD48), "(None 表示不在文件镜像内)")

# ---------- S3 独立校验：跳转表 65 项 + case16 ----------
print("\n[S3] 0x6E9F74 跳转表")
tbl = 0x6E9F74
ent = []
for k in range(80):
    v = u32(tbl + 4 * k)
    if v is None or not is_text(v):
        break
    ent.append(v)
print("  text-VA 连续条目数 =", len(ent), " case16 = 0x%08X" % ent[16] if len(ent) > 16 else "case16 = N/A")

# ---------- S2 独立校验：0x709820 六槽 ----------
print("\n[S2] 0x709820 已知值六槽")
for sv in (0x7E2640, 0x7E4258, 0x7E9030, 0x7EB3F4, 0x7F4CFC, 0x7F600C):
    print("  0x%08X -> 0x%08X" % (sv, u32(sv)))
