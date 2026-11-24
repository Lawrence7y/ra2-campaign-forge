# -*- coding: utf-8 -*-
# _verify_hy4.py — 独立复核：零真机 / 零采样 / 纯磁盘只读 + struct 解 PE 头
# 唯一写域: lead/n9_erratum_20261108/；核验脚本前缀 _verify_
import struct, hashlib, os

ROOT = r"D:\Project\ra2-campaign-forge"
def P(rel): return os.path.join(ROOT, rel.replace("/", os.sep))

def fp(rel):
    b = open(P(rel), "rb").read()
    return hashlib.sha256(b).hexdigest(), len(b), b

# ---------- A. 被核对象指纹 + 全指纹复算 ----------
print("== A 被核对象与关键件指纹 ==")
FILES = [
 "lead/n9_erratum_20261108/_er_N9_205_P6_B0CD48_ERRATUM.md",
 "lead/n9_erratum_20261108/_er_check_b0cd48.py",
 "lead/n9_erratum_20261108/_er_check_b0cd48_out.txt",
 "lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md",
 "lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md",
 "lead/spec_static_closure_20261108/_sc_scan_out.txt",
 "lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md",
 "lead/static_spec_n9_20261107/_n9_STATIC_COUNT_SPEC.md",
 "lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md",
 "lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md",
 "lead/spec_static_closure_20261108/_sc_CLOSURE_20261108.md",
 "ra2youli/gamemd.exe",
 "ra2bench/gamemd.exe",
]
for rel in FILES:
    h, n, _ = fp(rel)
    print("FP %-72s sha256=%s bytes=%d" % (rel, h, n))

# ---------- B. 原文逐字实读（抄录失真核查）----------
print("\n== B 原文逐字实读 ==")
def showlines(rel, ranges):
    L = open(P(rel), "r", encoding="utf-8").read().splitlines()
    print("--- %s (共 %d 行) ---" % (rel, len(L)))
    for a, b in ranges:
        for i in range(a-1, min(b, len(L))):
            print("%s:%d| %s" % (rel, i+1, L[i]))
showlines("lead/static_spec_n9_20261107/STATIC_COUNT_SPEC.md", [(139,139),(145,145),(198,198),(205,205)])
showlines("lead/static_spec_n9_20261107/_n9_STATIC_COUNT_SPEC.md", [(81,81),(109,109)])
showlines("lead/perf_repair_n11_20261108/PERF_REPAIR_HANDOFF.md", [(139,139),(161,161)])
showlines("lead/re_line_20261105/W8_STATIC_LOCATE/F8_VISIBILITY.md", [(169,169),(222,222)])
showlines("lead/re_line_20261105/W8_STATIC_LOCATE/W8_STATIC_LOCATE.md", [(162,162)])
showlines("lead/spec_static_closure_20261108/STATIC_GAP_CLOSURE.md", [(96,101),(173,173)])

# ---------- C. 独立 PE 解析（自实现；不复用 _er_check 代码）----------
print("\n== C 独立 PE 解析 ==")
def parse_pe(data):
    e = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e:e+4] == b"PE\0\0", "no PE sig"
    coff = e + 4
    machine, nsec, ts, pt, nsym, optsize, ch = struct.unpack_from("<HHIIIHH", data, coff)
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    imagebase = struct.unpack_from("<I", data, opt + 28)[0]
    sec0 = opt + optsize
    secs = []
    for i in range(nsec):
        o = sec0 + 40*i
        name = data[o:o+8].rstrip(b"\0").decode("ascii", "replace")
        vsz, va, rsz, raw = struct.unpack_from("<IIII", data, o+8)
        chars = struct.unpack_from("<I", data, o+36)[0]
        secs.append(dict(name=name, va=va, vsz=vsz, rsz=rsz, raw=raw, ch=chars))
    return imagebase, secs

def locate(imagebase, secs, va):
    rva = va - imagebase
    hit = None
    for s in secs:
        if s["va"] <= rva < s["va"] + max(s["vsz"], s["rsz"], 1):
            hit = s; break
    if hit is None: return None
    d = rva - hit["va"]
    in_raw = d < hit["rsz"]
    return dict(name=hit["name"], rva=rva, d=d, in_raw=in_raw,
                off=(hit["raw"]+d) if in_raw else None,
                vsz=hit["vsz"], rsz=hit["rsz"], raw=hit["raw"], va0=hit["va"])

for rel in ["ra2youli/gamemd.exe", "ra2bench/gamemd.exe"]:
    h, n, data = fp(rel)
    ib, secs = parse_pe(data)
    print("\n--- %s sha256=%s bytes=%d ---" % (rel, h, n))
    print("IMAGEBASE=0x%08X NSEC=%d" % (ib, len(secs)))
    for s in secs:
        print("  SEC %-8s VA=0x%08X VSZ=0x%X RAWPTR=0x%X RAWSZ=0x%X CH=0x%08X ZEROTAIL=%s"
              % (s["name"], ib+s["va"], s["vsz"], s["raw"], s["rsz"], s["ch"], "YES" if s["vsz"]>s["rsz"] else "no"))
    print("  HAS_INDEPENDENT_.bss_SECTION =", any(s["name"]==".bss" for s in secs))
    # 判定 0xB0CD48
    r = locate(ib, secs, 0x00B0CD48)
    print("  [0xB0CD48] RVA=0x%X sec=%s d=0x%X in_raw=%s off=%s RAWSZ=0x%X VSZ=0x%X"
          % (r["rva"], r["name"], r["d"], r["in_raw"], ("0x%X"%r["off"]) if r["off"] is not None else "无", r["rsz"], r["vsz"]))
    if r["in_raw"]:
        q = struct.unpack_from("<Q", data, r["off"])[0]
        print("  [0xB0CD48] qword=0x%016X double=%r  <<< 有文件镜像值" % (q, struct.unpack("<d", struct.pack("<Q", q))[0]))
    else:
        print("  [0xB0CD48] => 文件镜像无字节（d>=RAWSZ）；零初始化尾 VA∈[0x%08X,0x%08X) 尾长=0x%X"
              % (ib+r["va0"]+r["rsz"], ib+r["va0"]+r["vsz"], r["vsz"]-r["rsz"]))
    # 输入端地址
    for va in [0x00B0CD78,0x00B0CD88,0x00B0CD8C,0x00B0CE18,0x007E1728,0x007E1738,0x007E27F8]:
        rr = locate(ib, secs, va)
        if rr["in_raw"]:
            q = struct.unpack_from("<Q", data, rr["off"])[0]
            print("  [0x%08X] sec=%-8s off=0x%X qword=0x%016X double=%r" % (va, rr["name"], rr["off"], q, struct.unpack("<d",struct.pack("<Q",q))[0]))
        else:
            print("  [0x%08X] sec=%-8s d=0x%X >=RAWSZ 文件镜像无值" % (va, rr["name"], rr["d"]))
    # 写点 / 函数字节实证
    for va, exp in [(0x006D1BDD, b"\xDD\x1D\x48\xCD\xB0\x00"),
                    (0x006D1BB0, b"\xDD\x05\x28\x17\x7E\x00"),
                    (0x006D1BB6, b"\xDC\x35\x78\xCD\xB0\x00"),
                    (0x006D1BBC, b"\xA1\x8C\xCD\xB0\x00"),
                    (0x006D1BC1, b"\x8B\x0D\x88\xCD\xB0\x00"),
                    (0x006D1BC9, b"\xDD\x1D\x18\xCE\xB0\x00"),
                    (0x006D1BCF, b"\xE8"),
                    (0x006D1BD4, b"\xDC\x0D\x18\xCE\xB0\x00"),
                    (0x006D1BDA, b"\x83\xC4\x08")]:
        rr = locate(ib, secs, va)
        if rr["in_raw"]:
            got = data[rr["off"]:rr["off"]+len(exp)]
            print("  0x%08X off=0x%X bytes=%s exp=%s %s" % (va, rr["off"], got.hex(), exp.hex(), "OK" if got==exp else "MISMATCH"))
        else:
            print("  0x%08X 不在文件镜像" % va)

# ---------- D. 全 lead 检索 premise 载体（下游影响清单完备性）----------
print("\n== D 全 lead/*.md 检索 ==")
root = P("lead")
keys = ["静态 u64 窗口读", "静态可闭", "均静态可闭", "B0CD48", "P6", "半闭半开"]
res = {k: [] for k in keys}
for dp, dns, fns in os.walk(root):
    for fn in fns:
        if not fn.lower().endswith(".md"): continue
        full = os.path.join(dp, fn)
        rel = os.path.relpath(full, ROOT).replace(os.sep, "/")
        try: lines = open(full, "r", encoding="utf-8", errors="replace").read().splitlines()
        except Exception: continue
        for i, L in enumerate(lines, 1):
            for k in keys:
                if k in L: res[k].append((rel, i, L.strip()[:200]))
for k in keys:
    print("-- KEY %r hits=%d --" % (k, len(res[k])))
    for rel, i, L in res[k]: print("   %s:%d | %s" % (rel, i, L))
