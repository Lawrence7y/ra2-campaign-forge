# -*- coding: utf-8 -*-
# _er_report_pe.py — N9_SPEC_ERRATUM.md 撰写会话：0xB0CD48 结构性开口独立判定（纯磁盘只读 + struct，零真机零采样）
# 不复用 _er_check_b0cd48.py / _sc_scan.py 代码，独立实现 PE 节表解析。
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_report_pe.py"
import struct, hashlib

PATHS = [r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe",
         r"D:\Project\ra2-campaign-forge\ra2bench\gamemd.exe"]

def parse(path):
    data = open(path, "rb").read()
    sha = hashlib.sha256(data).hexdigest()
    e = struct.unpack_from("<I", data, 0x3C)[0]
    assert data[e:e+4] == b"PE\0\0", "PE signature"
    coff = e + 4
    machine, nsec, _ts, _pt, _nsym, optsize, _ch = struct.unpack_from("<HHIIIHH", data, coff)
    opt = coff + 20
    magic = struct.unpack_from("<H", data, opt)[0]
    assert magic == 0x10B, "PE32 expected"
    imagebase = struct.unpack_from("<I", data, opt + 28)[0]
    secs = []
    for i in range(nsec):
        o = opt + optsize + 40*i
        name = data[o:o+8].rstrip(b"\0").decode("ascii", "replace")
        vsz, va, rsz, raw = struct.unpack_from("<IIII", data, o+8)
        secs.append((name, va, vsz, raw, rsz))
    return data, sha, machine, nsec, imagebase, secs

def locate(secs, ib, va):
    rva = va - ib
    for nm, sva, vsz, raw, rsz in secs:
        if sva <= rva < sva + max(vsz, rsz, 1):
            d = rva - sva
            return nm, d, (raw + d) if d < rsz else None, vsz, rsz
    return None, None, None, None, None

def qword(data, off):
    if off is None or off + 8 > len(data):
        return None
    q = struct.unpack_from("<Q", data, off)[0]
    return struct.unpack("<d", struct.pack("<Q", q))[0]

for path in PATHS:
    data, sha, machine, nsec, ib, secs = parse(path)
    print("== %s" % path)
    print("R0 SHA256=%s bytes=%d MACHINE=0x%04X NSEC=%d IMAGEBASE=0x%08X" % (sha, len(data), machine, nsec, ib))
    for nm, sva, vsz, raw, rsz in secs:
        print("SEC %-8s VA=0x%08X VSZ=0x%06X RAWPTR=0x%06X RAWSZ=0x%06X %s"
              % (nm, ib+sva, vsz, raw, rsz, "ZEROINIT_TAIL=YES tail_len=0x%X" % (vsz-rsz) if vsz > rsz else ""))
    has_bss = any(nm.lower() == ".bss" for nm, *_ in secs)
    print("SEC HAS_INDEPENDENT_.bss_SECTION=%s" % has_bss)

    print("-- VA 判定 --")
    for va, tag in [(0x00B0CD48, "P6 争议地址"),
                    (0x00B0CD78, "fdiv 除数"), (0x00B0CD88, "call 实参1"), (0x00B0CD8C, "call 实参2"),
                    (0x00B0CE18, "fmul 暂存槽"), (0x007E1728, "fld 常量"), (0x007E1738, "已闭常量"),
                    (0x007E27F8, "校验锚点")]:
        nm, d, off, vsz, rsz = locate(secs, ib, va)
        if nm is None:
            print("CHK VA=0x%08X %-10s -> NO-SECTION RVA=0x%06X" % (va, tag, va-ib))
            continue
        if off is None:
            print("CHK VA=0x%08X %-10s sec=%s d=0x%06X d>=RAWSZ(0x%06X) -> 文件镜像无字节（零初始化域）qword=不可读"
                  % (va, tag, nm, d, rsz))
        else:
            v = qword(data, off)
            print("CHK VA=0x%08X %-10s sec=%s d=0x%06X off=0x%06X qword=0x%016X double=%r"
                  % (va, tag, nm, d, off, struct.unpack_from("<Q", data, off)[0], v))

    nm, d, off, vsz, rsz = locate(secs, ib, 0x00B0CD48)
    if nm and off is None:
        lo = ib + [s for s in secs if s[0] == nm][0][1]
        print("TAIL %s 零初始化尾 VA 域=[0x%08X,0x%08X) 尾长=0x%X；0xB0CD48 线性假想文件偏移=0x%06X（超出该节 RAW 末端 0x%X 字节；全文件=0x%X）"
              % (nm, lo+rsz, lo+vsz, vsz-rsz, off if off else (d + [s for s in secs if s[0]==nm][0][3]),
                 (d + [s for s in secs if s[0]==nm][0][3]) - ([s for s in secs if s[0]==nm][0][3] + [s for s in secs if s[0]==nm][0][4]),
                 len(data)))

    print("-- 写者链指令字节（文件镜像直读）--")
    for va, ln, exp, tag in [(0x006D1BB0, 6, "dd0528177e00", "fld qword [0x7E1728]"),
                             (0x006D1BB6, 6, "dc3578cdb000", "fdiv qword [0xB0CD78]"),
                             (0x006D1BBC, 5, "a18ccdb000",   "mov eax,[0xB0CD8C]"),
                             (0x006D1BC1, 6, "8b0d88cdb000", "mov ecx,[0xB0CD88]"),
                             (0x006D1BC9, 6, "dd1d18ceb000", "fstp qword [0xB0CE18]"),
                             (0x006D1BCF, 1, "e8",           "call 操作码"),
                             (0x006D1BD4, 6, "dc0d18ceb000", "fmul qword [0xB0CE18]"),
                             (0x006D1BDA, 3, "83c408",       "add esp,8"),
                             (0x006D1BDD, 6, "dd1d48cdb000", "fstp qword [0xB0CD48]")]:
        _nm, _d, o, _v, _r = locate(secs, ib, va)
        got = data[o:o+ln].hex() if o is not None else "不可读"
        print("BYT 0x%08X %-20s got=%s exp=%s %s" % (va, tag, got, exp, "OK" if got == exp else "MISMATCH"))
    _nm, _d, o, _v, _r = locate(secs, ib, 0x006D1BD0)
    rel = struct.unpack_from("<i", data, o)[0]
    print("CALL E8@0x6D1BCF rel32=0x%08X(%d) target=0x%08X %s"
          % (rel & 0xFFFFFFFF, rel, (0x6D1BD4 + rel) & 0xFFFFFFFF, "OK(target=0x4CACB0)" if (0x6D1BD4+rel) & 0xFFFFFFFF == 0x4CACB0 else "MISMATCH"))

    print("-- 全文件 disp32 0x48CDB000 (=0xB0CD48) 扫描 --")
    pat = b"\x48\xcd\xb0\x00"
    hits, pos = [], 0
    while True:
        i = data.find(pat, pos)
        if i < 0:
            break
        hits.append(i)
        pos = i + 1
    print("SCAN raw hits=%d" % len(hits))
    # 建立 raw→VA 映射（按节 RAW 区间）
    def off2va(o):
        for nm2, sva, vsz, raw, rsz in secs:
            if raw <= o < raw + rsz:
                return ib + sva + (o - raw), nm2
        return None, None
    for o in hits:
        va, nm2 = off2va(o)
        pre = data[o-2:o].hex()
        kind = {"dd1d": "fstp 写", "dc0d": "fmul 读"}.get(pre, "其他 pre=%s" % pre)
        print("HIT off=0x%06X VA=%s sec=%s pre2=%s -> %s" % (o, ("0x%08X" % va) if va else "unmapped", nm2, pre, kind))
    print()
