# -*- coding: utf-8 -*-
"""R-050 probe: trigger registry vector identity (L-30 残量收口取证).

Canonical section tuple: (rva, vsize, rawptr, rawsize). Single helper,
asserts the tuple order on the .text entry to kill the G-60 class of bugs
(first draft stored (va,vs,rp,rs) but unpacked (vs,va,rp,rs) => fileoff
compared VA against RVA => ALL global-ref censuses reported 0 -- third
recurrence of the G-60 family, now with a control item (House global
0xA80228 must yield 7 refs under any correct scan)).

Windows printed here are the authoritative source for the gate (G-65).
"""
import hashlib
import struct

ROOT = r"D:\Project\ra2-campaign-forge"
EXE = ROOT + r"\ra2youli\gamemd.exe"
SHA = "73201cc021497c9567742f718bf1dc78c22e9ae16c7e7365354b65f3fcf67476"
BLOB = open(EXE, "rb").read()
assert hashlib.sha256(BLOB).hexdigest() == SHA, "fingerprint mismatch"

e = struct.unpack_from("<I", BLOB, 0x3C)[0]
nsec = struct.unpack_from("<H", BLOB, e + 6)[0]
optsz = struct.unpack_from("<H", BLOB, e + 20)[0]
opt = e + 24
IB = struct.unpack_from("<I", BLOB, opt + 28)[0]
tab = opt + optsz
SEC = []  # (rva_start, vsize, rawptr, rawsize)
for i in range(nsec):
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", BLOB, tab + i * 40 + 8)
    SEC.append((vaddr, vsize, rawptr, rawsize))
assert SEC[0] == (0x1000, 0x3DF38D, 0x1000, 0x3E0000), SEC[0]  # tuple-order assertion

def fileoff(va):
    rva = va - IB
    for s_rva, vs, rp, rs in SEC:
        if s_rva <= rva < s_rva + vs:
            fo = rp + (rva - s_rva)
            return fo if fo < rp + rs else None
    return None

def rd(va, n):
    fo = fileoff(va)
    return BLOB[fo:fo + n] if fo is not None else b"\x00" * n

def u32(va):
    return struct.unpack("<I", rd(va, 4))[0]

def tdname(td):
    raw = rd(td + 8, 120)
    z = raw.find(b"\0")
    return (raw[:z] if z >= 0 else raw).decode("latin1")

print("== windows (machine dump; paste these into the gate) ==")
for lbl, va, n in [
    ("trig_ctor_vptr_init", 0x72536D, 10), ("trig_ctor_demote", 0x725398, 10),
    ("trig_gctor_head", 0x725350, 0x3D), ("trig_gdtor_head", 0x725390, 0x12),
    ("reg_add_block", 0x725FE9, 0x51), ("reg_manual_store", 0x726031, 9),
    ("house_vptr_init_CTRL", 0x4E6CFD, 10), ("house_vptr_demote_CTRL", 0x4E6D28, 10),
]:
    print(f"{lbl} 0x{va:08X}+0x{n:02X} = {rd(va, n).hex()}")

print("== RTTI chain: vt -> COL(vt-4) -> TD(COL+12) -> name ==")
for vt in (0x7E91EC, 0x7E920C, 0x7E9EE4, 0x7E9F04):
    col = u32(vt - 4)
    td = u32(col + 12)
    print(f"vt 0x{vt:08X} COL 0x{col:08X} TD 0x{td:08X} name={tdname(td)!r}")

print("== raw-find uniqueness inside .text only (bounds-safe) ==")
s_rva, vs, rp, rs = SEC[0]
TBUF = BLOB[rp:rp + min(vs, rs)]
for pat in ("c70570f6b000ec917e00", "c70570f6b0000c927e00"):
    b = bytes.fromhex(pat)
    hits = []
    p = TBUF.find(b)
    while p != -1:
        hits.append(hex(IB + s_rva + p))
        p = TBUF.find(b, p + 1)
    print(pat, "->", hits)

print("== owner-site census: imm32 ref to 0xB0F670 in trigger ctor + attach factory windows ==")
for g, window in ((0xB0F670, (0x725FA0, 0x726040)), (0xB0F670, (0x6E4EC0, 0x6E4F60))):
    needle = struct.pack("<I", g)
    lo, hi = window
    seg = rd(lo, hi - lo)
    idx = []
    p = seg.find(needle)
    while p != -1:
        idx.append(hex(lo + p))
        p = seg.find(needle, p + 1)
    print(f"0x{g:08X} refs in 0x{lo:08X}..0x{hi:08X}:", idx)

print("== control item: House global 0xA80228 census in .text (must be > 0) ==")
needle = struct.pack("<I", 0xA80228)
hits = []
p = TBUF.find(needle)
while p != -1:
    hits.append(hex(IB + s_rva + p))
    p = TBUF.find(needle, p + 1)
print("0xA80228 refs:", len(hits), hits)
