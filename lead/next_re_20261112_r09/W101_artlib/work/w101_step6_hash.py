# -*- coding: utf-8 -*-
"""W101 step6: hash tail + crc table + exact engine-hash simulation (read-only)."""
import json, os, struct, zlib
import capstone, pefile

EXE  = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUTD = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r09\W101_artlib\EVIDENCE"
data = open(EXE, "rb").read()
pe = pefile.PE(EXE, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = [(s.Name.rstrip(b"\x00").decode(), s.VirtualAddress + IB, s.Misc_VirtualSize,
         s.PointerToRawData, s.SizeOfRawData) for s in pe.sections]

def va2off(va):
    for name, vstart, vsz, raw, rsz in secs:
        if vstart <= va < vstart + max(vsz, rsz):
            o = raw + (va - vstart)
            if o < len(data): return o
    return None

md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
PBUF = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); PBUF.append(s)

def disasm(start, end, title):
    P("")
    P("=" * 100)
    P(f"## {title}   0x{start:08X} - 0x{end:08X}")
    P("=" * 100)
    off = va2off(start)
    for ins in md.disasm(data[off: off + (end - start)], start):
        P(f"0x{ins.address:08X}  {ins.bytes.hex():<18s} {ins.mnemonic} {ins.op_str}")

disasm(0x4A1EB6, 0x4A1FB0, "hash tail 0x4A1DE0 (leftover handling + return)")

# crc table at 0x81F7B4
off = va2off(0x81F7B4)
tab = struct.unpack_from("<8I", data, off)
P("")
P("crc table @0x81F7B4 first 8 dwords:", " ".join(f"{v:08X}" for v in tab))
zt = [zlib.crc32(bytes([c])) - zlib.crc32(b"") for c in range(8)]  # not directly comparable; build ref
ref = []
for c in range(8):
    crc = c
    for _ in range(8):
        crc = (crc >> 1) ^ (0xEDB88320 if crc & 1 else 0)
    ref.append(crc)
P("reference zlib table  first 8     :", " ".join(f"{v:08X}" for v in ref))
P("TABLE == zlib table[0:8]:", list(tab) == ref)

def engine_hash(name, tail_mode):
    """Replicate 0x4A1DE0 exactly; tail_mode selects leftover handling variant."""
    b = name.encode("ascii", "replace")
    crc = 0
    n = len(b)
    i = 0
    # main 4-byte block loop (0x4A1E75): per block: not; 4 table steps; not
    full = (n // 4) * 4
    crc = zlib.crc32(b[:full]) & 0xFFFFFFFF if full else 0
    # NOTE zlib crc32 over prefix == engine state after blocks (both end in 'normal' form)
    left = b[full:]
    if tail_mode == "stage_only":          # leftover staged, never processed, no finalize
        return crc & 0xFFFFFFFF
    if tail_mode == "pad_nul":             # leftover padded with NULs to 4 then processed
        pad = left + b"\x00" * (4 - len(left))
        return (zlib.crc32(pad, zlib.crc32(b[:full]))) & 0xFFFFFFFF
    if tail_mode == "pad_first_byte":      # leftover padded by repeating first leftover byte
        if left:
            pad = left + left[0:1] * (4 - len(left))
        else:
            pad = left
        return (zlib.crc32(pad, zlib.crc32(b[:full]))) & 0xFFFFFFFF
    if tail_mode == "stream":              # leftover streamed byte-wise (no padding) = plain crc32
        return zlib.crc32(b) & 0xFFFFFFFF
    raise ValueError

P("")
P("== engine-hash candidates per name ==")
for nm in ["ARTMD.INI", "RULESMD.INI", "ART.INI", "RULES.INI", "TEMPERAT.MIX",
           "AMAZON.MMX", "BATTLEMD.INI", "LOCAL.MIX", "ISOTEMMD.MIX", "ECH01.MAP",
           "ARTMD.IN", "RULESMD.IN", "A.MIX", "AB.MIX", "ABC.MIX"]:
    vals = {m: engine_hash(nm, m) for m in ("stage_only", "pad_nul", "pad_first_byte", "stream")}
    P(f"{nm:14s} len={len(nm):2d} " + "  ".join(f"{k}={v:08X}" for k, v in vals.items())
      + f"  mixlib_crc={zlib.crc32(nm.upper().encode()) & 0xFFFFFFFF:08X}"
      f"  mixlib_classic={__import__('sys').path.append(r'D:\\Project\\ra2-campaign-forge\\ra2forge') or __import__('mixlib').classic_hash(nm):08X}")

open(os.path.join(OUTD, "step6_hash.txt"), "w", encoding="utf-8").write("\n".join(PBUF) + "\n")
print("\nsaved ->", os.path.join(OUTD, "step6_hash.txt"))
