#!/usr/bin/env python3
# R17-R10-DISPATCH 可复跑脚本：只读 gamemd.exe，重新产出 Q1/Q2 全部结论
# 用法: python work.py [path/to/gamemd.exe]
import sys, struct, hashlib, json, os

EXE = sys.argv[1] if len(sys.argv) > 1 else r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = os.path.dirname(os.path.abspath(__file__))
data = open(EXE, "rb").read()
print("size", len(data), "sha256", hashlib.sha256(data).hexdigest().upper())

# --- PE sections ---
pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
ib = struct.unpack_from("<I", data, pe + 24 + 28)[0]
secs = []
for i in range(nsec):
    o = pe + 24 + optsz + i * 40
    name = data[o:o+8].rstrip(b"\0").decode()
    vs, va, rs, rp = struct.unpack_from("<IIII", data, o + 8)
    secs.append((name, ib + va, vs, rp, rs))
for s in secs: print("section", s[0], hex(s[1]), hex(s[2]), "raw", hex(s[3]), hex(s[4]))
TEXT = next(s for s in secs if s[0] == ".text")
TV, TSZ, TRAW, TRS = TEXT[1], TEXT[2], TEXT[3], TEXT[4]
def va2off(va):
    for name, v, vs, rp, rs in secs:
        if v <= va < v + rs: return rp + (va - v)
    return -1
def off2va(off):
    for name, v, vs, rp, rs in secs:
        if rp <= off < rp + rs: return v + (off - rp)
    return -1
def rd32(va): return struct.unpack_from("<I", data, va2off(va))[0]
def cstr(va):
    o = va2off(va); e = o
    while data[e] != 0 and e - o < 300: e += 1
    return data[o:e].decode("latin1")
print("anchor gap check: first instruction byte after last 90/CC of .text start padding =",
      hex(TV + 0x10))

# --- Q1: decorated names ---
names = []
i = data.find(b".?A")
while i >= 0:
    if data[i-1] == 0:
        names.append((off2va(i), cstr(off2va(i))))
    i = data.find(b".?A", i + 1)
seccount = {}
for va, nm in names:
    for name, v, vs, rp, rs in secs:
        if v <= va < v + vs: seccount[name] = seccount.get(name, 0) + 1
print("Q1 decorated names total", len(names), "by section", seccount)
nameva = {va for va, _ in names}
refs = []
for off in range(0, len(data) - 4):
    if struct.unpack_from("<I", data, off)[0] in nameva:
        refs.append((off2va(off), struct.unpack_from("<I", data, off)[0]))
print("Q1 refs to name strings", len(refs))
for va, t in refs: print("   ref at", hex(va), "->", hex(t), cstr(t))
HOSTS = [(0x43B680, 0x43B740), (0x43B740, 0x43BCDE), (0x43BCF0, 0x43C0CA)]
for s, e in HOSTS:
    inside = [r for r in refs if s <= r[0] < e]
    near = [r for r in refs if s - 0x1000 <= r[0] < e + 0x1000]
    print("Q1 host", hex(s), "fn_end", hex(e), "internal refs", len(inside), "near4k refs", len(near))

# --- Q2: scale-4 indirect call/jmp ---
scanned = TRS
byref = 0; call_rr4 = 0; jmp_disp4 = 0; jmp_in_seg = 0; reg_based = []
for o in range(TRAW, TRAW + TSZ):
    if data[o] != 0xFF: continue
    m = data[o + 1]
    reg = (m >> 3) & 7
    if reg not in (2, 4): continue
    mod, rm = (m >> 6) & 3, m & 7
    if rm != 4: continue
    sib = data[o + 2]; scale, idx, base = sib >> 6, (sib >> 3) & 7, sib & 7
    if scale != 2: continue
    va = off2va(o)
    if reg == 4 and mod == 0 and base == 5:                    # FF 24 8x disp32
        jmp_disp4 += 1
        t = ib + struct.unpack_from("<i", data, o + 3)[0]
        if 0x7E3EBC <= t < 0x7E43C4: jmp_in_seg += 1
    else:
        reg_based.append((va, reg, mod, idx, base, data[o:o+8].hex()))
print("Q2 scanned .text raw bytes", scanned)
print("Q2 jmp [reg*4+disp32] sites", jmp_disp4, " tables inside slot segment", jmp_in_seg)
print("Q2 register-based scale4 sites", len(reg_based))
for r in reg_based: print("   ", hex(r[0]), "call" if r[1] == 2 else "jmp", "mod", r[2], "idx", r[3], "base", r[4], r[5])

# --- slot segment integrity ---
A, B = 0x7E3EBC, 0x7E43C4
n = (B - A) // 4
bad = [(i, A + i * 4, rd32(A + i * 4)) for i in range(n) if not (TV <= rd32(A + i * 4) < TV + TSZ)]
print("slot segment slots", n, "non-.text entries", len(bad))
print("slot73", hex(rd32(0x7E3FE0)), "slot107", hex(rd32(0x7E4068)))
