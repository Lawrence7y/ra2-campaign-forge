"""R0-d: second, independent path for vtable[12] -> instance size.

Deliberately does NOT read rtti/symbols.json. It locates each class's vtable
from the raw .rdata pointer that the corpus cites, reads slot 12 directly out
of the file, and decodes the target body. This is a different code path from
xcheck_sizes.py so agreement between the two is meaningful.

Read-only; prints a report.
"""

import struct

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"

# (class, vtable VA) taken from ATLAS §11.2 and from this line's suspects
CASES = [
    ("TeamTypeClass", 0x007F47D0),
    ("AITriggerTypeClass", 0x007E2A50),
    ("UnitClass", 0x007F5C70),
    ("HouseClass", 0x007EA8A0),
    ("RadarClass", 0x007F0344),
    ("WWMouseClass", 0x007F7B2C),
    ("TeamClass", 0x007F4730),
]


def load(path):
    d = open(path, "rb").read()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    nsec = struct.unpack_from("<H", d, e + 6)[0]
    opt = e + 24
    ib = struct.unpack_from("<I", d, opt + 28)[0]
    tab = opt + struct.unpack_from("<H", d, e + 20)[0]
    secs = []
    for i in range(nsec):
        o = tab + i * 40
        nm = d[o:o + 8].rstrip(b"\0").decode("ascii", "replace")
        vs, va, rs, rp = struct.unpack_from("<IIII", d, o + 8)
        secs.append((nm, va, vs, rp, rs))
    return d, ib, secs


D, IB, SECS = load(EXE)


def file_off(rva):
    for nm, va, vs, rp, rs in SECS:
        if va <= rva < va + rs:
            return rp + (rva - va)
    return None


def u32(va):
    o = file_off(va - IB)
    return None if o is None else struct.unpack_from("<I", D, o)[0]


def body(va, n=8):
    o = file_off(va - IB)
    return b"" if o is None else D[o:o + n]


print("# independent path: vtable VA -> raw slot 12 -> body bytes")
for name, vt in CASES:
    f12 = u32(vt + 12 * 4)
    b = body(f12)
    # decode: B8 imm32 (mov eax,imm32) | B8 imm8? no; B0-B7 imm8 affects other regs
    kind = "?"
    size = None
    if b[:1] == b"\xB8":
        size = struct.unpack_from("<I", b, 1)[0]
        kind = "mov eax,imm32"
    elif b[:2] == b"\x8B\x01":
        kind = "mov eax,[ecx]"
    elif len(b) >= 3 and b[0] == 0x8B:
        kind = f"mov eax,[ecx+{b[2]}]"
    print(f"  {name:22s} vt=0x{vt:08X}  v[12]=0x{f12:08X}  bytes={b.hex(' '):<26} {kind}"
          f"  size={size if size is not None else '-'}")
