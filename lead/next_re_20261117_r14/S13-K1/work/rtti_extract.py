"""S13-K1: RTTI TypeDescriptor -> COL -> vftable extraction for 4 target classes.
Independently re-derived from binary. Clue only: classes_meta/symbols (not trusted).
COL layout confirmed empirically in THIS binary: +C = pTypeDescriptor (VA), +0 signature=0.
Vftable linked by: dword at [vt-4] == COL VA.
Read-only on target. Emits EVIDENCE/rtti_extract.txt
"""
import struct
import pefile

EXE = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
OUT = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13-K1\EVIDENCE\rtti_extract.txt"
pe = pefile.PE(EXE)
IB = pe.OPTIONAL_HEADER.ImageBase
DATA = open(EXE, "rb").read()
SECS = []
for s in pe.sections:
    name = s.Name.decode("ascii", "replace").rstrip("\x00")
    lo = IB + s.VirtualAddress
    hi = lo + max(s.Misc_VirtualSize, s.SizeOfRawData)
    rawlo = s.PointerToRawData
    rawhi = rawlo + s.SizeOfRawData
    SECS.append((name, lo, hi, rawlo, rawhi))

lines = []
def p(x=""):
    lines.append(str(x))

def sec_of(va):
    for n, lo, hi, rl, rh in SECS:
        if lo <= va < hi:
            return n
    return None

def off_of(va):
    for n, lo, hi, rl, rh in SECS:
        if lo <= va < hi:
            o = rl + (va - lo)
            if o < rh:
                return o
    return None

def u32(va):
    o = off_of(va)
    if o is None or o + 4 > len(DATA):
        return None
    return struct.unpack_from("<I", DATA, o)[0]

def cstr(va, cap=128):
    o = off_of(va)
    if o is None:
        return ""
    raw = DATA[o:o+cap]
    return raw.split(b"\x00")[0].decode("latin1")

TARGETS = ["WeaponTypeClass", "WarheadTypeClass", "BulletTypeClass", "BulletClass"]

# 1. locate TypeDescriptors by mangled name anywhere in image
td_by_name = {}
for cls in TARGETS:
    pat = (".?AV" + cls + "@@").encode("latin1")
    hits = []
    pos = 0
    while True:
        i = DATA.find(pat, pos)
        if i < 0:
            break
        va = None
        for n, lo, hi, rl, rh in SECS:
            if rl <= i < rh:
                va = lo + (i - rl)
                break
        hits.append(va)
        pos = i + 1
    tds = []
    for nv in hits:
        if nv is None: continue
        td = nv - 8
        vf = u32(td); spare = u32(td + 4)
        if vf is not None and sec_of(vf) == ".rdata" and spare == 0:
            tds.append(td)
    td_by_name[cls] = tds
    p(f"[{cls}] name VAs: {[hex(x) for x in hits]}")
    p(f"[{cls}] TypeDescriptors: {[hex(x) for x in tds]}")
    for td in tds:
        p(f"  TD {hex(td)}: pVFTable={hex(u32(td))} spare={u32(td+4)} name='{cstr(td+8)}'")

all_tds = set()
for v in td_by_name.values():
    all_tds.update(v)

# 2. find COLs: scan all sections' raw bytes for dword at +0xC == a TD VA
col_by_td = {td: [] for td in all_tds}
for n, lo, hi, rl, rh in SECS:
    end = rh
    for i in range(rl, end - 16, 4):
        ptd = struct.unpack_from("<I", DATA, i + 12)[0]
        if ptd in all_tds:
            colva = lo + (i - rl)
            col_by_td[ptd].append(colva)

# 3. find vftables: scan all sections for dword == COL VA; vftable starts right after that dword
col_set = set()
for v in col_by_td.values():
    col_set.update(v)

for cls in TARGETS:
    p(f"\n=== {cls} vftables ===")
    for td in td_by_name.get(cls, []):
        for col in col_by_td.get(td, []):
            for n, lo, hi, rl, rh in SECS:
                end = rh
                for i in range(rl, end - 4, 4):
                    val = struct.unpack_from("<I", DATA, i)[0]
                    if val != col:
                        continue
                    vt = lo + (i - rl) + 4
                    if sec_of(vt) != ".rdata":
                        continue
                    # measure slots from vt: contiguous dwords pointing into .text,
                    # bounded by .rdata raw end (the next non-code dword stops it).
                    slots = []
                    j = i + 4
                    while j + 4 <= end:
                        w = struct.unpack_from("<I", DATA, j)[0]
                        if sec_of(w) != ".text":
                            break
                        slots.append(w)
                        j += 4
                    p(f"  VT {hex(vt)} (sec={n}, COL={hex(col)}, TD={hex(td)}): measured_slots={len(slots)}")
                    p("    slots: " + " ".join(hex(x) for x in slots))

p("\n=== clue cross-check (symbols.json metadata; VERIFY ABOVE) ===")
for cls, td, col, vt in [
    ("WeaponTypeClass",0x849248,0x80E3C0,0x7F73B8),
    ("WarheadTypeClass",0x847C18,0x80D2C0,0x7F6B30),
    ("BulletTypeClass",0x81AFB0,0x7FC7C8,0x7E4948),
    ("BulletClass",0x81AF70,0x7FC710,0x7E46E4),
]:
    v = u32(vt-4)
    p(f"{cls}: TD={hex(td)} (found={td in all_tds}) COL={hex(col)} (found={col in col_set}) VT={hex(vt)} [vt-4]={hex(v) if v else None} ([vt-4] in cols={v in col_set})")

open(OUT, "w", encoding="utf-8").write("\n".join(lines))
print("wrote", OUT, len(lines), "lines")
