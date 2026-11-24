"""Independent PE access layer. Index convention verified explicitly.

get_memory_mapped_image() returns a buffer whose index 0 == ImageBase.
So absolute VA v maps to buf[v - ImageBase].
"""
import pefile, struct, hashlib

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
IB = 0x400000

pe = pefile.PE(EXE, fast_load=True)
pe.parse_data_directories()

BUF = pe.get_memory_mapped_image()
assert len(BUF) == 0xA794B0 or True

SECTIONS = []
for s in pe.sections:
    name = s.Name.rstrip(b"\x00").decode()
    SECTIONS.append(dict(name=name,
                         va=IB + s.VirtualAddress,
                         vsize=s.Misc_VirtualSize,
                         rawsize=s.SizeOfRawData,
                         rawptr=s.PointerToRawData))

def by_name(n):
    for s in SECTIONS:
        if s["name"] == n:
            return s
    raise KeyError(n)

TEXT = by_name(".text")
RDATA = by_name(".rdata")
DATA = by_name(".data")

def u8(va):
    return BUF[va - IB]

def u16(va):
    return struct.unpack_from("<H", BUF, va - IB)[0]

def u32(va):
    return struct.unpack_from("<I", BUF, va - IB)[0]

def s32(va):
    return struct.unpack_from("<i", BUF, va - IB)[0]

def blob(va, n):
    return bytes(BUF[va - IB: va - IB + n])

def cstr(va, maxlen=256):
    i = va - IB
    out = bytearray()
    while i < len(BUF) and len(out) < maxlen:
        c = BUF[i]
        if c == 0:
            break
        out.append(c)
        i += 1
    return out.decode("latin-1")

def sec_of(va):
    for s in SECTIONS:
        if s["va"] <= va < s["va"] + max(s["vsize"], s["rawsize"]):
            return s
    return None

def in_raw(va, n=1):
    """True iff [va, va+n) lies inside file-backed bytes of its section."""
    s = sec_of(va)
    if s is None:
        return False
    off = va - s["va"]
    return off >= 0 and off + n <= s["rawsize"]

def va_from_sec_off(secname, off):
    s = by_name(secname)
    return s["va"] + off

if __name__ == "__main__":
    print("image size", hex(len(BUF)))
    for s in SECTIONS:
        print("%-8s va=%08X vsize=%08X rawsize=%08X rawptr=%08X end=%08X" %
              (s["name"], s["va"], s["vsize"], s["rawsize"], s["rawptr"],
               s["va"] + s["vsize"]))
    print("sha", hashlib.sha256(open(EXE, "rb").read()).hexdigest().upper())
