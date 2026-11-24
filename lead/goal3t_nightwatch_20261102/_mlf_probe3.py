# -*- coding: utf-8 -*-
"""§533 probe C -- 基线核验：0x55D360 睡眠/泵循环 与 IAT 解析 + 三处读点定位。

只读 gamemd.exe。零真机、零写入（除 stdout）。
目的：把 probe A/B 看到的结构钉成可复算的字节事实，而不是叙述。
"""
import hashlib
import struct

from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
EXPECT_SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == EXPECT_SHA, "image drift"

e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e + 6)[0]
optsz = struct.unpack_from("<H", raw, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", raw, opt + 28)[0]
tab = opt + optsz
SEC = []
for i in range(nsec):
    nm = raw[tab + i * 40: tab + i * 40 + 8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab + i * 40 + 8)
    SEC.append((nm, IB + va, vsz, rp, rsz))
TEXT = next(s for s in SEC if s[0] == ".text")
TLO, THI = TEXT[1], TEXT[1] + TEXT[4]


def fo(va):
    for nm, sva, vsz, rp, rsz in SEC:
        if sva <= va < sva + vsz:
            off = rp + (va - sva)
            return off if off < rp + rsz else None
    return None


def rd(va, n):
    o = fo(va)
    return raw[o:o + n] if o is not None else b"\0" * n


# ---- import table ----------------------------------------------------------
def resolve_iat(va):
    """VA in IAT -> (dll, func) using import descriptors."""
    dd = opt + 96
    imp_rva, imp_sz = struct.unpack_from("<II", raw, dd + 8)
    if not imp_rva:
        return None
    o = fo(IB + imp_rva)
    k = 0
    while True:
        desc = raw[o + k * 20: o + k * 20 + 20]
        if len(desc) < 20 or desc == b"\0" * 20:
            break
        oft, _ts, _fc, name_rva, ft = struct.unpack_from("<IIIII", desc, 0)
        no = fo(IB + name_rva)
        dll = raw[no:raw.index(b"\0", no)].decode("ascii", "replace")
        thunk = oft or ft
        j = 0
        while True:
            tv = struct.unpack_from("<I", raw, fo(IB + thunk) + j * 4)[0]
            if tv == 0:
                break
            slot = IB + ft + j * 4
            if slot == va:
                if tv & 0x80000000:
                    return (dll, "ord#%d" % (tv & 0xFFFF))
                ho = fo(IB + tv + 2)
                return (dll, raw[ho:raw.index(b"\0", ho)].decode("ascii", "replace"))
            j += 1
        k += 1
    return None


print("=" * 70)
print("T1 IAT 解析（定位 0x7E11F0 / 0x7E1530）")
print("=" * 70)
for va in (0x55D387 + 0, 0x55D360):
    pass
for va in (0x7E11F0, 0x7E1530):
    print("  [%08X] -> %s  (dword=%08X)" % (
        va, resolve_iat(va), struct.unpack_from("<I", rd(va, 4), 0)[0]))

# ---- 精确复现 0x55D377..0x55D3BB 睡眠块 -------------------------------------
print()
print("=" * 70)
print("T2 睡眠/泵块逐字节 [0x55D377, 0x55D3BB)")
print("=" * 70)
MD = Cs(CS_ARCH_X86, CS_MODE_32)
for ins in MD.disasm(rd(0x55D377, 0x55D3BB - 0x55D377), 0x55D377):
    print("  %08X  %-22s %-7s %s" % (ins.address, ins.bytes.hex(), ins.mnemonic, ins.op_str))

# ---- 0xA8ED80 在 0x55D360 内的全部引用 -------------------------------------
print()
print("=" * 70)
print("T3 [0xA8ED80] 在 MainLogicFrame 内的全部引用（raw abs32）")
print("=" * 70)
lo, hi = 0x55D360, 0x55DEE0
buf = rd(lo, hi - lo)
pat = b"\x80\xed\xa8\x00"
i = 0
n = 0
while True:
    j = buf.find(pat, i)
    if j < 0:
        break
    va = lo + j
    # 向上对齐取指令
    print("  hit at %08X  prefix=%s" % (va, buf[max(0, j - 2):j].hex()))
    n += 1
    i = j + 1
print("  总计 %d 处" % n)

# ---- 全镜像 0xA8ED80 引用计数（与本函数内对比） ----------------------------
print()
print("=" * 70)
print("T4 全镜像 [0xA8ED80] raw 引用计数（复核 R-063a 的 46）")
print("=" * 70)
allb = raw
cnt = 0
sites = []
p = 0
while True:
    j = allb.find(pat, p)
    if j < 0:
        break
    # 换算 VA
    va = None
    for nm, sva, vsz, rp, rsz in SEC:
        if rp <= j < rp + rsz:
            va = sva + (j - rp)
            break
    sites.append(va)
    cnt += 1
    p = j + 1
print("  总计 %d 处 (R-063a 报 46)" % cnt)
intext = [s for s in sites if s is not None and TLO <= s < THI]
print("  其中 .text 内 %d 处" % len(intext))
