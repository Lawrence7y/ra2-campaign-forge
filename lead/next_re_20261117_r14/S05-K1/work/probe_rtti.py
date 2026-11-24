import pefile, struct, os

P = os.path.join('D:', os.sep, 'Project', 'ra2-campaign-forge', 'ra2youli', 'gamemd.exe')
pe = pefile.PE(P)
IB = pe.OPTIONAL_HEADER.ImageBase
secs = []
for s in pe.sections:
    name = s.Name.rstrip(b'\0').decode('ascii', 'replace')
    secs.append((name, s.VirtualAddress + IB, s.Misc_VirtualSize, s.PointerToRawData, s.SizeOfRawData))
for s in secs:
    print('SEC %-10s VA=%08X VS=%08X raw=%08X RS=%08X' % s)

_f = open(P, 'rb')
_data = _f.read()

def off(va):
    for n, vb, vs, pr, rs in secs:
        if vb <= va < vb + max(vs, rs):
            d = va - vb
            if d < rs:
                return pr + d
    return None

def rd(va):
    o = off(va)
    if o is None or o + 4 > len(_data):
        return None
    return struct.unpack_from('<I', _data, o)[0]

def rdstr(va, n=100):
    o = off(va)
    if o is None:
        return None
    b = _data[o:o+n]
    return b.split(b'\0')[0].decode('ascii', 'replace')

targets = [
    ('AbstractClass', 0x7E1F50), ('ObjectClass', 0x7EF060),
    ('TechnoClass', 0x7F4960), ('FootClass', 0x7E8C94),
    ('BuildingClass', 0x7E3EBC), ('UnitClass', 0x7F5C70),
    ('InfantryClass', 0x7EB058), ('AircraftClass', 0x7E22A4),
]
for name, vt in targets:
    col = rd(vt - 4)
    td = rd(col + 0xC) if col else None
    cd = rd(col + 0x10) if col else None
    nm = rdstr(td + 8) if td else None
    print('%-15s vt=%08X col=%s td=%s cd=%s name=%s' % (
        name, vt,
        ('%08X' % col) if col else None,
        ('%08X' % td) if td else None,
        ('%08X' % cd) if cd else None,
        nm))
