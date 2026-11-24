from pathlib import Path
import hashlib
import struct

MIRROR = Path(r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe")
OUT = Path(r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R15_SLOT73")
EXPECTED_SHA_PREFIX = "73201CC0"
IMAGE = 0x400000
TARGET73 = 0x43F180
TARGET107 = 0x449440
WANT = [
    ".?AVBuildingClass@@",
    ".?AVTechnoClass@@",
    ".?AVInfantryClass@@",
    ".?AVUnitClass@@",
    ".?AVAircraftClass@@",
]

data = MIRROR.read_bytes()
sha = hashlib.sha256(data).hexdigest().upper()
if not sha.startswith(EXPECTED_SHA_PREFIX):
    raise SystemExit(f"sha256 mismatch: {sha}")
OUT.mkdir(parents=True, exist_ok=True)

pe = struct.unpack_from("<I", data, 0x3C)[0]
nsec = struct.unpack_from("<H", data, pe + 6)[0]
optsz = struct.unpack_from("<H", data, pe + 20)[0]
sec_off = pe + 24 + optsz
sections = []
for i in range(nsec):
    o = sec_off + i * 40
    name = data[o:o + 8].rstrip(b"\0").decode("ascii")
    vsize, rva, raw_size, raw = struct.unpack_from("<IIII", data, o + 8)
    sections.append(dict(name=name, vsize=vsize, rva=rva, size=raw_size, raw=raw))
by_name = {s["name"]: s for s in sections}
text, rdata, sdata = by_name[".text"], by_name[".rdata"], by_name[".data"]
code_lo = IMAGE + text["rva"]
code_hi = code_lo + text["size"]

def va_to_off(va):
    r = va - IMAGE
    for s in sections:
        if s["rva"] <= r < s["rva"] + s["size"]:
            return s["raw"] + (r - s["rva"])
    return None

def off_to_va(o):
    for s in sections:
        if s["raw"] <= o < s["raw"] + s["size"]:
            return IMAGE + s["rva"] + (o - s["raw"])
    return None

def u32_off(o):
    if o is None or o < 0 or o + 4 > len(data):
        return None
    return struct.unpack_from("<I", data, o)[0]

def u32_va(va):
    return u32_off(va_to_off(va))

def hex8(v):
    return "未取得" if v is None else f"0x{v:08X}"

# TD: TypeDescriptor+8 内联名 ".?AV..."。
td_by_va = {}
data_end = sdata["raw"] + sdata["size"]
for o in range(sdata["raw"], data_end - 8):
    if data[o:o + 4] != b".?AV":
        continue
    e = o + 4
    while e < data_end and 0x20 <= data[e] < 0x7F:
        e += 1
    if e >= data_end or data[e] != 0 or e - o < 10:
        continue
    name = data[o:e].decode("ascii")
    tva = off_to_va(o - 8)
    if tva is None:
        continue
    vf = u32_va(tva)
    spare = u32_va(tva + 4)
    if vf and spare == 0 and tva not in td_by_va:
        td_by_va[tva] = name

# COL: +12 -> TD, +16 -> ClassHierarchyDescriptor。
col_by_va = {}
rd_end = rdata["raw"] + rdata["size"]
for o in range(rdata["raw"], rd_end - 24, 4):
    td = u32_off(o + 12)
    if td not in td_by_va:
        continue
    cd = u32_off(o + 16)
    co = va_to_off(cd) if cd is not None else None
    if co is None or co + 16 > len(data):
        continue
    sig, attr, nbases, basearr = struct.unpack_from("<IIII", data, co)
    if sig == 0 and attr < 0x100 and 0 < nbases < 0x1000 and va_to_off(basearr) is not None:
        colva = off_to_va(o)
        if colva is not None:
            col_by_va[colva] = td_by_va[td]

def slot_count(vbase):
    o = va_to_off(vbase)
    if o is None:
        return 0
    n = 0
    p = o
    while p + 4 <= rd_end:
        v = struct.unpack_from("<I", data, p)[0]
        if not (code_lo <= v < code_hi):
            break
        n += 1
        p += 4
    return n

def slot_value(vbase, idx):
    o = va_to_off(vbase)
    if o is None or o + (idx + 1) * 4 > rd_end:
        return None
    return struct.unpack_from("<I", data, o + idx * 4)[0]

refs = []
for o in range(rdata["raw"], rd_end - 4, 4):
    col = u32_off(o)
    if col in col_by_va:
        vbase = off_to_va(o) + 4
        refs.append((col_by_va[col], vbase, slot_count(vbase)))

main = {}
for name, vbase, count in refs:
    cur = main.get(name)
    if cur is None or count > cur[1] or (count == cur[1] and vbase < cur[0]):
        main[name] = (vbase, count)

with (OUT / "class_index.tsv").open("w", encoding="utf-8", newline="\n") as f:
    f.write("class_name\tvtable_va\tslot_count\tis_main\n")
    for name, vbase, count in sorted(refs):
        m = main.get(name)
        f.write(f"{name}\t{hex8(vbase)}\t{count}\t{'yes' if m and m[0] == vbase else 'no'}\n")

with (OUT / "slot73_107.tsv").open("w", encoding="utf-8", newline="\n") as f:
    f.write("class_name\tmain_vtable\tslot_count\tslot_73\tslot_107\teq_0x43F180 / eq_0x449440\n")
    for name in WANT:
        m = main.get(name)
        if m is None:
            f.write(f"{name}\t未取得\t未取得\t未取得\t未取得\tNA / NA\n")
            continue
        vbase, count = m
        s73 = slot_value(vbase, 73) if count > 73 else None
        s107 = slot_value(vbase, 107) if count > 107 else None
        f.write(
            f"{name}\t{hex8(vbase)}\t{count}\t{hex8(s73)}\t{hex8(s107)}\t"
            f"{'YES' if s73 == TARGET73 else 'NO'} / {'YES' if s107 == TARGET107 else 'NO'}\n"
        )
