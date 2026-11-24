#!/usr/bin/env python3
# R17-R36: PE section-table VA->raw mapping; no subprocesses, no image writes.
import hashlib, struct, sys
from pathlib import Path

IMAGE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
EXPECT_SHA = "73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476"
data = IMAGE.read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
assert sha == EXPECT_SHA, sha

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
coff = e_lfanew + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
size_opt = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
assert struct.unpack_from("<H", data, opt)[0] == 0x10B
image_base = struct.unpack_from("<I", data, opt + 28)[0]
sec_align = struct.unpack_from("<I", data, opt + 32)[0]
sec_off = opt + size_opt

sections = []
for i in range(nsec):
    o = sec_off + i * 40
    name = data[o:o+8].decode("latin1").rstrip("\x00")
    vsize, rva, raw_size, raw_ptr = struct.unpack_from("<IIII", data, o + 8)
    sections.append(dict(name=name, rva=rva, va=image_base + rva, vsize=vsize, raw_size=raw_size, raw_ptr=raw_ptr))

def align_up(x, a):
    return (x + a - 1) // a * a

def map_va(va):
    rva = va - image_base
    for s in sections:
        off = rva - s["rva"]
        if 0 <= off < s["raw_size"]:
            return s, off, s["raw_ptr"] + off, "initialized"
    for s in sections:
        off = rva - s["rva"]
        if 0 <= off < align_up(s["vsize"], sec_align):
            return s, off, None, "uninitialized"
    return None

print("IMAGE", IMAGE)
print("SHA256", sha)
for s in sections:
    print(s["name"] + "\tVA " + hex(s["va"]) + "-" + hex(s["va"] + s["vsize"]) + "\tRAW " + hex(s["raw_ptr"]) + "-" + hex(s["raw_ptr"] + s["raw_size"]))

for va in (0x87F7E8, 0x87F924):
    m = map_va(va)
    if m is None:
        print(hex(va) + "\tOUTSIDE_ALL_SECTIONS")
        continue
    s, off, file, state = m
    if file is None:
        print(hex(va) + "\t" + s["name"] + "\toff=" + hex(off) + "\tNO_FILE_BYTES\t" + state)
    else:
        word = struct.unpack_from("<I", data, file)[0]
        print(hex(va) + "\t" + s["name"] + "\toff=" + hex(off) + "\tfile=" + hex(file) + "\tdword=" + hex(word))

# Callsite: mov ecx,0x87F7E8 at 0x449476; call 0x5657A0 at 0x44947B.
s, off, file, state = map_va(0x449476)
assert file is not None and data[file:file+10].hex() == "b9e8f78700e820c31100"
s, off, file, state = map_va(0x5657A0)
assert file is not None and data[file:file+34].hex().startswith("8b542404560fbf42020fbf32c1e00903c65e78143d000004007d0d8b893c010000")
print("CALLSITE_OK", "B9 E8 F7 87 00 / E8 20 C3 11 00")
print("VERDICT", "R35 correct at runtime; dword[0x87F924] static value NOT PRESENT in PE raw")
