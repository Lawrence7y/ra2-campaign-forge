# -*- coding: utf-8 -*-
"""_r064rev_probe5.py — 收尾：COL/CHD/BCD 盘面版式亲读 / 帧A直线D轨迹(第三法) /
   T16 PURE 分级 / 0x7787DB this-D / List<INISection*> 复用槽 P / 帧F线外块
"""
import struct, hashlib, re
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
raw = open(EXE, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
e = struct.unpack_from("<I", raw, 0x3C)[0]
nsec = struct.unpack_from("<H", raw, e+6)[0]; optsz = struct.unpack_from("<H", raw, e+20)[0]
opt = e+24; ib = struct.unpack_from("<I", raw, opt+28)[0]; tab = opt+optsz
secs = []
for i in range(nsec):
    name = raw[tab+i*40:tab+i*40+8].rstrip(b"\0").decode()
    vsz, va, rsz, rp = struct.unpack_from("<IIII", raw, tab+i*40+8)
    secs.append((name, ib+va, vsz, rp, rsz))
def rb(va, n):
    rva = va - ib
    for name, sva, vsz, rp, rsz in secs:
        if sva - ib <= rva < sva - ib + vsz:
            fo = rp + (rva - (sva - ib)); return raw[fo:fo+n] if fo < rp+rsz else bytes(n)
    return b""
def rd(va):
    b = rb(va, 4); return int.from_bytes(b, "little") if len(b) == 4 else None
def cstr(va, mx=90):
    out = bytearray()
    for i in range(mx):
        c = rb(va+i, 1)
        if not c or c == b"\0": break
        out += c
    return out.decode("latin1")

print("== COL/CHD/BCD 盘面 dump（GenericList 家族 + INIClass 家族 + List）==")
def dump_family(V, label):
    col = rd(V-4)
    print("\n%s V=%06X COL=%06X" % (label, V, col))
    for off in range(0, 0x20, 4):
        v = rd(col+off)
        extra = ""
        if v and 0x400000 < v < 0xC00000:
            nm = cstr(v+8) if rb(v+8, 1) not in (b"",) else ""
            printable = nm and all(32 <= ord(ch) < 127 for ch in nm)
            if printable: extra = " ->名? %r" % nm
            if rb(v,4) == bytes.fromhex("94957f00"): extra = " ->TD(vfp=7F9594) 名=%r" % cstr(v+8)
        print("  COL+0x%02X = %06X%s" % (off, v, extra))
    chd = rd(col+0x10)
    print("  CHD=%06X:" % chd)
    for off in range(0, 0x14, 4):
        v = rd(chd+off)
        print("    CHD+0x%02X = %06X" % (off, v))
    # 候选语义：A) numBases=CHD+8, arr=CHD+0xC（本线既往读法）
    nbA = rd(chd+8); arrA = rd(chd+0xC)
    # B) numBases=CHD+4, selfTD=CHD+0xC? 用 TD vfp 判
    for i in range(max(nbA or 0, 0, rd(chd+4) or 0)):
        for base, arrl, tag in (("A", arrA, "CHD+0xC起"), ):
            p = rd(arrl + i*4) if arrl else None
            if p:
                nm = cstr(p+8); tdv = rd(p)
                print("    %s[%d] = %06X %r (BCD? 首字=%06X %r)" % (tag, i, p, cstr(p+8, 40), tdv, cstr(tdv+8) if tdv else None))
dump_family(0x7E1B04, "GenericList")
dump_family(0x7EA5F4, "INIClass")
dump_family(0x7E1AFC, "List<INISection*>")

# 直接读 BCD 常见版式 {TD*, numBaseCls, numPrim, attrs, mdisp...}：0x7FAD00 首字
for addr, lab in [(0x7FAD00, "GenericList CHD+0xC 指向"), (0x8024F4, "INIClass CHD+0xC 指向"), (0x7FAC00, "List CHD+0xC 指向")]:
    t = rd(addr)
    print("  %s: [%06X]=%06X 名=%r vfp?=%s" % (lab, addr, t, cstr(t+8) if t else None, rb(t,4).hex() if t else None))

# ---- 线性解码（同域）----
tname, tva, tvsz, trp, trsz = next(s for s in secs if s[0] == ".text")
TLO, THI = tva, tva + trsz
code = raw[trp:trp+trsz]
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = False
insns = []; cur = TLO; end = TLO + trsz
while cur < end:
    got = None
    for ins in md.disasm(code[cur-TLO:min(cur-TLO+15, end-TLO)], cur):
        got = (ins.address, ins.size, ins.bytes.hex(), ins.mnemonic, ins.op_str); break
    if got is None: cur += 1; continue
    insns.append(got); cur += got[1]
IDX = {a: i for i, (a, s, b, m, o) in enumerate(insns)}
e8set = set()
for a, s, b, m, o in insns:
    if m == "call" and b.startswith("e8") and len(b) == 10:
        try: t = int(o, 16)
        except ValueError: continue
        if TLO <= t < THI: e8set.add(t)
RIM = {0x528C00:0x10, 0x525A10:8, 0x5256F0:0, 0x527F20:0x10, 0x526D90:0xC, 0x5295F0:0xC,
       0x40E340:4, 0x7B6290:0, 0x7B4630:0, 0x4325C0:0, 0x526810:0, 0x7B5B30:0, 0x52B4F0:4}

print("\n== 帧 A 第三法：0x778710→0x77884F 直线 D 轨迹（亲验该段无分支）==")
k0 = IDX[0x778710]
branchy = [(insns[i][0], insns[i][3], insns[i][4]) for i in range(k0, IDX[0x77884F]) if insns[i][3].startswith("j")]
print("  分支指令：", branchy if branchy else "无（直线）")
D = 0; p = 0; marks = {}
for i in range(k0, IDX[0x77884F]+1):
    a, s, b, m, o = insns[i]
    if a in (0x7787C0, 0x7787D1, 0x7787DB, 0x7787F7, 0x77884B):
        marks[a] = (D, p)
    if m == "push": D += 4; p += 4
    elif m == "pop": D -= 4
    elif m == "sub" and o.startswith("esp, "):
        x = int(o.split(", ")[1], 0); D += x; p += x
    elif m == "add" and o.startswith("esp, "):
        x = int(o.split(", ")[1], 0); D -= x; p = 0
    elif m == "call":
        t = int(o, 16) if o.startswith("0x") else None
        if t in RIM: r = RIM[t]; D -= r; p = max(0, p-r)
        elif t is not None and t not in RIM:
            print("    未知 callee %06X @%06X p=%d" % (t, a, p))
print("  关键点 (D,p):")
for a in sorted(marks):
    d, pp = marks[a]
    it = insns[IDX[a]]
    print("    %06X %s %-28s D=0x%X p=%d" % (a, it[2], it[4], d, pp))
dispGL = 0x38; dispINI = 0x30
print("  G-stamp 0x7787C0: P=0x38-0x%X = 0x%X" % (marks[0x7787C0][0], dispGL - marks[0x7787C0][0]))
print("  INI-stamp 0x7787F7: P=0x30-0x%X = %s" % (marks[0x7787F7][0], hex(0x30 - marks[0x7787F7][0])))
print("  witness lea 0x77884B: W=0x38-0x%X = %s" % (marks[0x77884B][0], hex(0x38 - marks[0x77884B][0])))
print("  0x7787DB this-lea (INIClass ctor this): 0x30-0x%X = %s ；期望同 W 格（R-064 构造完整性）" % (
    marks[0x7787DB][0], hex(0x30 - marks[0x7787DB][0])))
print("  List-stamp 0x7787D1 (0x7E1AFC): disp=0x34 D=0x%X P=%s" % (marks[0x7787D1][0], hex(0x34 - marks[0x7787D1][0])))

print("\n== 帧 F 线外块（R-064 E6：jne→0x778B61..0x778B9F 与 stamp 0x778B20 同帧）==")
for a in (0x778A20, 0x778B20, 0x778B61, 0x778B95, 0x778B9F):
    it = insns[IDX[a]] if a in IDX else None
    print("  %06X %s %s %s" % (a, it[2] if it else "?", it[3] if it else "?", it[4] if it else "?"))

print("\n== 0x5D76A9(T16) 直线片段：0x5D761D(stamp) 前后各 6 条 ==")
k = IDX[0x5D761D]
for j in range(max(0, k-6), k+7):
    a, s, b, m, o = insns[j]
    print("  %06X %-20s %s %s" % (a, b, m, o))
print("\n== 0x5CF4C7 帧 D：0x5CEF41 前后 ==")
k = IDX[0x5CEF41]
for j in range(max(0, k-4), k+5):
    a, s, b, m, o = insns[j]
    print("  %06X %-20s %s %s" % (a, b, m, o))
