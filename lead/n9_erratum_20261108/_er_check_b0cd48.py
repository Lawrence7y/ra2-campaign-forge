# -*- coding: utf-8 -*-
# _er_check_b0cd48.py — 勘误判定探件：VA 0xB0CD48 是否落在 gamemd.exe 文件镜像内
# 零真机、零采样、纯磁盘文件只读 + struct 解 PE 头。唯一写域: lead/n9_erratum_20261108/。
# 用法: python -I -X utf8 "D:/Project/ra2-campaign-forge/lead/n9_erratum_20261108/_er_check_b0cd48.py"
import struct, hashlib

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(PATH, "rb").read()
SHA = hashlib.sha256(data).hexdigest()
print("R0 SHA256", SHA)
print("R0 BYTES", len(data))
print("R0 SHA_MATCH_CORPUS_73201cc0", SHA == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476")

# ---- PE 头解析（独立实现，不复用 _sc_scan.py 代码）----
e = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e:e+4] == b"PE\0\0"
coff = e + 4
machine, nsec, _ts, _pt, _nsym, optsize, _ch = struct.unpack_from("<HHIIIHH", data, coff)
opt = coff + 20
magic = struct.unpack_from("<H", data, opt)[0]
imagebase = struct.unpack_from("<I", data, opt + 28)[0]
sec0 = opt + optsize
print("R0 MACHINE 0x%04X NSEC=%d MAGIC=0x%04X IMAGEBASE=0x%08X" % (machine, nsec, magic, imagebase))
SECS = []
for i in range(nsec):
    o = sec0 + 40*i
    name = data[o:o+8].rstrip(b"\0").decode("ascii", "replace")
    vsz, va, rsz, raw = struct.unpack_from("<IIII", data, o+8)
    ch = struct.unpack_from("<I", data, o+36)[0]
    SECS.append((name, va, vsz, raw, rsz, ch))
    print("R0 SEC %-8s VA=0x%08X VSZ=0x%06X RAWPTR=0x%06X RAWSZ=0x%06X CH=0x%08X ZEROINIT_TAIL=%s"
          % (name, imagebase+va, vsz, raw, rsz, ch, "YES" if vsz > rsz else "no"))

def locate(va):
    rva = va - imagebase
    hit = None
    for nm, sva, vsz, raw, rsz, ch in SECS:
        if sva <= rva < sva + max(vsz, rsz, 1):
            hit = (nm, sva, vsz, raw, rsz, ch)
            break
    if hit is None:
        return ("NO-SECTION", rva)
    nm, sva, vsz, raw, rsz, ch = hit
    d = rva - sva
    in_raw = d < rsz
    off = raw + d if in_raw else None
    return (nm, rva, d, in_raw, off, vsz, raw, rsz)

def qword_if_mapped(va):
    r = locate(va)
    if r[0] == "NO-SECTION" or not r[4-1+1]:  # in_raw flag at index 3
        return None, r
    off = r[4]
    if off + 8 > len(data):
        return None, r
    return struct.unpack_from("<Q", data, off)[0], r

print("\n== P6 相关 VA 逐一判定 ==")
VAS = [
    (0x00B0CD48, "[0xB0CD48] 争议地址（P6 开口）"),
    (0x00B0CD78, "函数 0x6D1BB0 的 fdiv 除数"),
    (0x00B0CD88, "call 0x4CACB0 实参1"),
    (0x00B0CD8C, "call 0x4CACB0 实参2"),
    (0x00B0CE18, "fstp 暂存槽（fmul 回读）"),
    (0x007E1728, "fld 常量（声称=60.0，.rdata）"),
    (0x007E1738, "已闭常量（声称=0.5，.rdata）"),
    (0x007E27F8, "方法校验锚点（声称=900.0，.rdata）"),
]
for va, tag in VAS:
    q, r = qword_if_mapped(va)
    if r[0] == "NO-SECTION":
        print("CHK VA=0x%08X %-28s -> 无任何节覆盖（RVA=0x%06X）" % (va, tag, r[1]))
        continue
    nm, rva, d, in_raw, off, vsz, raw, rsz = r
    if in_raw:
        print("CHK VA=0x%08X %-28s sec=%s d=0x%06X 文件偏移=0x%06X qword=0x%016X double=%r"
              % (va, tag, nm, d, off, q, struct.unpack("<d", struct.pack("<Q", q))[0]))
    else:
        where = "节内零初始化尾（BSS 型，VA ∈ [VAbase+RAWSZ, VAbase+VSZ)）" if d < vsz else "节外"
        print("CHK VA=0x%08X %-28s sec=%s d=0x%06X 文件偏移=无（d>=RAWSZ: 0x%X>=0x%X）qword=不可读 %s"
              % (va, tag, nm, d, d, rsz, where))

# ---- 写点字节实证：0x6D1BDD 处应为 DD 1D 48 CD B0 00 ----
print("\n== 写点/读点指令字节实证（直接从文件镜像读）==")
for va, exp, tag in [
    (0x006D1BDD, b"\xDD\x1D\x48\xCD\xB0\x00", "fstp qword [0xB0CD48] 编码"),
    (0x006D1BB0, b"\xDD\x05\x28\x17\x7E\x00", "fld  qword [0x7E1728] 编码"),
    (0x006D1BB6, b"\xDC\x35\x78\xCD\xB0\x00", "fdiv qword [0xB0CD78] 编码"),
    (0x006D1BCF, b"\xE8", "call 0x4CACB0 操作码"),
]:
    r = locate(va)
    if r[0] == "NO-SECTION" or not r[3]:
        print("CHK 0x%08X %s -> 不在文件镜像（sec=%s）" % (va, tag, r[0]))
        continue
    got = data[r[4]:r[4]+len(exp)]
    print("CHK 0x%08X %-24s 文件偏移=0x%06X 字节=%s 期望=%s %s"
          % (va, tag, r[4], got.hex(), exp.hex(), "OK" if got == exp else "MISMATCH"))

# ---- .data 文件镜像尾邻域旁证：取文件镜像内最后 8 字节及全文件尾 ----
print("\n== .data 文件镜像边界旁证 ==")
for nm, sva, vsz, raw, rsz, ch in SECS:
    if nm == ".data":
        lo = imagebase + sva
        print("SEC .data 文件镜像 VA 域=[0x%08X,0x%08X) 零初始化尾 VA 域=[0x%08X,0x%08X) 尾长=0x%X 字节"
              % (lo, lo+rsz, lo+rsz, lo+vsz, vsz-rsz))
        last = struct.unpack_from("<Q", data, raw+rsz-8)[0]
        print("SEC .data 文件镜像末 qword @VA=0x%08X = 0x%016X" % (lo+rsz-8, last))
        # 0xB0CD48 若按线性外推的假想文件偏移（仅示意，实际不映射）
        hypo = raw + (0x00B0CD48 - imagebase - sva)
        print("SEC .data 假想线性偏移=0x%06X 超出 RAWSZ(0x%06X) 达 0x%X 字节；全文件大小=0x%X"
              % (hypo, rsz, hypo-(raw+rsz), len(data)))
