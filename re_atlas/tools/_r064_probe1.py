# _r064_probe1.py -- R-064 仲裁探针1：PE 装载 + 原始字节读 + RTTI 双链 walk + 家族关系
# 只读 gamemd.exe（sha256 73201cc0...f67476）。不写任何文件，只打印。
# 装载器函数（rd/rd32/cstr/secs）可被后续 _r064_probe*.py 复用；分析体仅 main 执行。
import struct, hashlib

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(EXE, "rb").read()

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
coff = e_lfanew + 4
nsec, = struct.unpack_from("<H", data, coff+2)
opt_size, = struct.unpack_from("<H", data, coff+16)
opt = coff + 20
imagebase = struct.unpack_from("<I", data, opt+28)[0]
secs = []
so = opt + opt_size
for i in range(nsec):
    name = data[so:so+8].rstrip(b"\0").decode("latin1")
    vsz, va, rsz, raw = struct.unpack_from("<IIII", data, so+8)
    secs.append((name, imagebase+va, imagebase+va+vsz, raw, raw+rsz))
    so += 40

def rd(va, n):
    for name, v0, v1, r0, r1 in secs:
        if v0 <= va < v1:
            off = r0 + (va - v0)
            if off + n <= r1 and off + n <= len(data):
                return data[off:off+n]
            return None
    return None

def rd32(va):
    b = rd(va, 4)
    return struct.unpack("<I", b)[0] if b else None

def cstr(va, maxlen=96):
    b = rd(va, maxlen)
    if b is None: return None
    i = b.find(b"\0")
    return b[:i].decode("latin1") if i >= 0 else b.decode("latin1")

def rtti_walk(V, label):
    col_slot = V - 4
    raw = rd(col_slot, 4)
    if raw is None:
        print("   [V-4]=%#x 不可读（越界）" % col_slot); return None
    col = struct.unpack("<I", raw)[0]
    print("   [%#x] (vtable[-1]) = %s -> COL %#x" % (col_slot, raw.hex(), col))
    sig, off, cdoff = struct.unpack_from("<III", rd(col, 12), 0)
    td_raw = rd(col+0xC, 4)
    td = struct.unpack("<I", td_raw)[0]
    print("   COL@%#x: sig=%d off=%#x cdOff=%#x" % (col, sig, off, cdoff))
    print("   [COL+0xC] = %s -> TD %#x" % (td_raw.hex(), td))
    name = cstr(td+8)
    print("   TD@%#x: vfp=[%#x]=%#x spare=%#x" % (td, td, rd32(td), rd32(td+4)))
    print("   TD+8 名 = %r" % name)
    chd = rd32(col+0x10)
    print("   [COL+0x10] -> CHD %#x" % chd)
    if chd:
        nbases = rd32(chd+8); bca = rd32(chd+0xC)
        print("   CHD: sig=%d attr=%#x numBases=%d pBaseClassArray=%#x" % (rd32(chd), rd32(chd+4), nbases, bca))
        for i in range(min(nbases, 32)):
            bcd = rd32(bca + 4*i)
            print("      基类 %r (containedBases=%d)" % (cstr(rd32(bcd)+8), rd32(bcd+4)))
    return name

def bases_of(V):
    col = rd32(V-4); chd = rd32(col+0x10)
    nb = rd32(chd+8); bca = rd32(chd+0xC)
    return [cstr(rd32(rd32(bca+4*k))+8) for k in range(nb)]

def main():
    sha = hashlib.sha256(data).hexdigest()
    print("== A. 镜像自验 ==")
    print("sha256 =", sha)
    print("ImageBase = %#x" % imagebase)
    for name, v0, v1, r0, r1 in secs:
        print("  %-8s va=[%#x,%#x) raw=[%#x,%#x)" % (name, v0, v1, r0, r1))

    print("\n== B. RTTI 双链 walk ==")
    g = rtti_walk(0x7E1B04, "家族1（R-062 冻结 stamp 立即数）")
    i2 = rtti_walk(0x7EA5F4, "家族2（R-063b 候选 stamp 立即数）")
    print("\n-- 语境家族（R-063b §4 列举）--")
    rtti_walk(0x7E1B0C, "0x7E1B0C")
    rtti_walk(0x7E1AFC, "0x7E1AFC")
    rtti_walk(0x7E1668, "0x7E1668")
    print("\n-- R-062 控制位复现 --")
    print("   [0x8174C8] = %#x (期望 vfp 0x7F9594)" % rd32(0x8174C8))
    print("   0x8174D0 名 = %r" % cstr(0x8174D0))

    print("\n== C. 家族关系交叉核查 ==")
    print("   家族1 名 = %r ; 家族2 名 = %r ; 相同? %s" % (g, i2, g == i2))
    bg = bases_of(0x7E1B04); bi = bases_of(0x7EA5F4)
    print("   GenericList 基类集含 INIClass? ", any("INIClass@@" in (n or "") for n in bg))
    print("   INIClass    基类集含 GenericList? ", any("GenericList@@" in (n or "") for n in bi))
    print("   vtable 地址距离 = %#x" % abs(0x7EA5F4 - 0x7E1B04))

    print("\n== D. 六 stamp 写点 + 三处补 stamp 候选：原始字节 ==")
    sites = [
        ("R-062 窗1", 0x7787C0), ("R-062 窗2", 0x779BB3), ("R-062 窗3", 0x779E33),
        ("R-063b stamp1", 0x5CEF41), ("R-063b stamp2", 0x76C4A4), ("R-063b stamp3", 0x778B20),
        ("R-063b 候选补A", 0x7787F7), ("R-063b 候选补B", 0x779BEA), ("R-063b 候选补C", 0x779E6A),
        ("R-063b 同函数 stamp(0x5D76 帧)", 0x5D761D),
    ]
    for label, va in sites:
        print("   %-28s @%#x = %s" % (label, va, rd(va, 8).hex()))

if __name__ == "__main__":
    main()
