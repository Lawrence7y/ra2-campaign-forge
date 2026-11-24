# -*- coding: utf-8 -*-
# _p11_supplement.py — P11 补充探针（只读）：宿主锚点性质/序言/父函数/跳表归属
# 前置: _p11_stations_scan.py（同目录）输出 _p11_stations_out.txt 的疑点补充。
# 零真机/零采样/零进程 API/本脚本零写盘。
import struct, hashlib
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
data = open(PATH, "rb").read()
print("R0 SHA256", hashlib.sha256(data).hexdigest())
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
        td_map[sva + i - 8] = blob[i:j if j > 0 else i + 64].decode("ascii", errors="replace")
        start = i + 1

rvals = {}
for nm in (".rdata", ".data"):
    sva, vsz, raw, rsz = SEC[nm]
    for off in range(0, rsz - 3, 4):
        v = struct.unpack_from("<I", data, raw + off)[0]
        if 0x401000 <= v < 0x8A0000:
            rvals.setdefault(v, []).append(sva + off)

def vt_len(vt, maxn=4096):
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

func_slots = {}
for td_key, name in td_map.items():
    for pos in rvals.get(td_key, []):
        col = pos - 12
        if col < SEC[".rdata"][0] or u32(col) != 0 or u32(col + 12) != td_key:
            continue
        for vtp in rvals.get(col, []):
            vt = vtp + 4
            for k in range(vt_len(vt)):
                v = u32(vt + 4 * k)
                if v and is_text(v):
                    func_slots.setdefault(v, []).append((name, vt, k))

callers = {}
TEXT_VA, TEXT_VSZ, TEXT_RAW, TEXT_RSZ = SEC[".text"]
for i in range(TEXT_RAW, TEXT_RAW + TEXT_RSZ - 5):
    b = data[i]
    if b in (0xE8, 0xE9):
        rel = struct.unpack_from("<i", data, i + 1)[0]
        tgt = (TEXT_VA + (i - TEXT_RAW)) + 5 + rel
        callers.setdefault(tgt, []).append((TEXT_VA + (i - TEXT_RAW), "call" if b == 0xE8 else "jmp"))

cs = Cs(CS_ARCH_X86, CS_MODE_32)

def D(va, n, title):
    print("-- disasm %08x (%s) --" % (va, title))
    o = va2off(va)
    for ins in list(cs.disasm(data[o:o + n], va))[:40]:
        print("   %08x  %-8s %s" % (ins.address, ins.mnemonic, ins.op_str))

def pad_before(va, k=10):
    o = va2off(va)
    return " ".join("%02x" % data[o - i] for i in range(k, 0, -1))

def anchor_info(va):
    print("ANCHOR 0x%08X pad_before[-10..-1]=%s" % (va, pad_before(va)))
    print("  callers:", [(hex(a), t) for a, t in callers.get(va, [])][:10])
    print("  rvals positions:", [hex(p) for p in rvals.get(va, [])][:10])
    print("  func_slots:", [(c, hex(vt), "vslot%d" % s) for c, vt, s in func_slots.get(va, [])][:6])

print("### A. 0x416D50（站 0x417481 的 PASS2 宿主）")
anchor_info(0x416D50)
D(0x416D50, 0x40, "prologue")
print("### A2. 0x4166D0（对 0x416D50 的唯一 jmp 者）")
anchor_info(0x4166D0)
D(0x4166D0, 0x30, "context")

print("### B. 0x50D170（站 0x50D1D2 宿主）")
anchor_info(0x50D170)
D(0x50D170, 0x30, "prologue")
print("### B2. 5 个直调者的父函数边界试探")
for c in (0x5099C6, 0x509B7E, 0x509C6E, 0x509D34, 0x509E6B):
    D(c - 0x10, 0x20, "around caller 0x%08x" % c)

print("### C. 0x6ED090 / 0x6F0130（S3 开关下游 helper）")
for va in (0x6ED090, 0x6F0130):
    anchor_info(va)
    D(va, 0x20, "prologue")

print("### D. S3 开关宿主 0x6E9050 的身份线索：case0 块与 0x6E978F")
D(0x6E9783, 0x30, "case0 block (table entry[0])")
D(0x6E9DD3 - 0x20, 0x30, "block containing 0x6E9DD3")

print("### E. 跳表 0x6E9F74 全 65 条目")
tbl = []
for k in range(65):
    v = u32(0x6E9F74 + 4 * k)
    tbl.append(hex(v) if v else "None")
print("  ", tbl)
print("  0x6ED090 in table:", 0x6ED090 in tbl, " 0x6F0130 in table:", 0x6F0130 in tbl)

print("### F. 其余新目标锚点")
for va in (0x6EB490, 0x6EF9E0, 0x6EC3D0, 0x645BB0, 0x565730, 0x5657A0,
           0x5B3A00, 0x703590, 0x65C7E0, 0x4DE19A, 0x4D4E80, 0x70C610, 0x4068E0):
    print("0x%08X callers=%s slots=%s rvals=%d" % (
        va, [(hex(a), t) for a, t in callers.get(va, [])][:6],
        [(c, "vslot%d" % s) for c, vt, s in func_slots.get(va, [])][:4],
        len(rvals.get(va, []))))

print("### G. 0x414A80（Aircraft vslot138 宿主）与 0x4D4DC0（Foot vslot132）直调者邻域")
D(0x51F538 - 0x18, 0x28, "0x51F538 call site context (Infantry v[266] 内)")
D(0x7447A0, 0x20, "0x7447A0 jmp-tail 起点")
anchor_info(0x7447A0)
print("### H. 0x4D4280 唯一直调者 0x740B49 邻域（UnitClass v[151] 内）")
D(0x740B40, 0x18, "around 0x740B49")
print("### I. 0x50D170 父候选：0x5099C6 所在函数的锚点试探")
for va in (0x509900, 0x5099A0):
    print("0x%08X pad=%s callers=%s slots=%s" % (va, pad_before(va),
          [(hex(a), t) for a, t in callers.get(va, [])][:4],
          [(c, "vslot%d" % s) for c, vt, s in func_slots.get(va, [])][:4]))
print("RUN DONE")
