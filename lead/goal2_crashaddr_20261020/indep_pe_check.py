"""独立核验 0x0084F2BA 的段归属与页保护（不复用 qwen 的 addr_probe.py）。"""
import struct
import hashlib

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
TARGET = 0x0084F2BA

data = open(EXE, "rb").read()
print("file size =", len(data), " sha256[:16] =", hashlib.sha256(data).hexdigest()[:16])

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e_lfanew:e_lfanew + 4] == b"PE\0\0"
coff = e_lfanew + 4
machine, nsec = struct.unpack_from("<HH", data, coff)
sz_opt = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
magic = struct.unpack_from("<H", data, opt)[0]
image_base = struct.unpack_from("<I", data, opt + 28)[0]
size_image = struct.unpack_from("<I", data, opt + 56)[0]
dllchar = struct.unpack_from("<H", data, opt + 70)[0]
print(f"magic=0x{magic:04X} image_base=0x{image_base:08X} SizeOfImage=0x{size_image:08X} "
      f"DllCharacteristics=0x{dllchar:04X}")
print(f"  NX_COMPAT(0x0100) = {'SET' if dllchar & 0x0100 else 'CLEAR'}")
print(f"  DYNAMIC_BASE(0x0040) = {'SET' if dllchar & 0x0040 else 'CLEAR'}")
print(f"  HIGH_ENTROPY_VA(0x0020) = {'SET' if dllchar & 0x0020 else 'CLEAR'}")

sec = opt + sz_opt
print("\n%-10s %10s %10s %10s %10s %10s  %s" %
      ("name", "VA", "VSize", "RawPtr", "RawSize", "Chars", "flags"))
secs = []
for i in range(nsec):
    off = sec + i * 40
    name = data[off:off + 8].rstrip(b"\0").decode("latin-1")
    vs, va, rs, rp = struct.unpack_from("<IIII", data, off + 8)
    chars = struct.unpack_from("<I", data, off + 36)[0]
    flags = ("R" if chars & 0x40000000 else "-") + \
            ("W" if chars & 0x80000000 else "-") + \
            ("X" if chars & 0x20000000 else "-")
    secs.append((name, image_base + va, vs, rp, rs, chars))
    print(f"{name:10} 0x{image_base+va:08X} 0x{vs:08X} 0x{rp:08X} 0x{rs:08X} 0x{chars:08X}  {flags}")

print(f"\n=== locate 0x{TARGET:08X} ===")
hit = None
for name, va, vs, rp, rs, chars in secs:
    if va <= TARGET < va + vs:
        hit = (name, va, vs, rp, rs, chars)
        break
if not hit:
    print("  NOT IN ANY SECTION (would be in uncommitted image space)")
else:
    name, va, vs, rp, rs, chars = hit
    intra = TARGET - va
    file_off = rp + intra
    print(f"  section = {name}")
    print(f"  section VA range = 0x{va:08X} .. 0x{va+vs:08X}")
    print(f"  intra-section offset = 0x{intra:X}")
    print(f"  file offset = 0x{file_off:X}  (delta = 0x{TARGET-file_off:06X})")
    print(f"  section Characteristics = 0x{chars:08X}")
    print(f"    MEM_WRITE (0x80000000) = {'SET' if chars & 0x80000000 else 'CLEAR'}")
    print(f"    MEM_EXECUTE (0x20000000) = {'SET' if chars & 0x20000000 else 'CLEAR'}")
    print(f"    MEM_READ (0x40000000) = {'SET' if chars & 0x40000000 else 'CLEAR'}")
    page = TARGET & ~0xFFF
    print(f"  containing page = 0x{page:08X} (page offset 0x{TARGET & 0xFFF:03X})")
    in_file = intra < rs
    print(f"  within raw data? {'YES' if in_file else 'NO (zero-filled / not file-backed)'}")
    if in_file and file_off + 32 <= len(data):
        chunk = data[file_off:file_off + 32]
        print(f"  32 bytes at file off 0x{file_off:X}: {chunk.hex(' ').upper()}")
        print(f"  all zero? {all(b == 0 for b in chunk)}")
    print(f"  TARGET mod 4 = {TARGET % 4}")

print("\n=== EP ===")
ep = struct.unpack_from("<I", data, opt + 16)[0]
print(f"  AddressOfEntryPoint = 0x{ep:08X} -> VA 0x{image_base+ep:08X}")
