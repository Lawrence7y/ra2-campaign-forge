import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)

RD_LO, RD_HI = 0x007E1000, 0x00812000


def cstr(va):
    off = pe.va_to_off(va)
    if off is None:
        return None
    end = pe.data.find(b'\0', off)
    if end < 0 or end - off > 300:
        return None
    return pe.data[off:end].decode('latin-1', 'replace')


def in_rdata(v):
    return v is not None and RD_LO <= v < RD_HI


def scan_cols():
    cols = []
    for va in range(RD_LO, RD_HI - 24, 4):
        sig, off, cd, ptd, pcd, pself = [pe.dword(va + k) for k in (0, 4, 8, 12, 16, 20)]
        if sig != 0:
            continue
        if off not in (0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64):
            continue
        if cd not in (0, 4, 8, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 52, 56, 60, 64):
            continue
        if not in_rdata(ptd) or not in_rdata(pcd) or pself != va:
            continue
        name = cstr(ptd + 8)
        if not name or not name.startswith('.?A'):
            continue
        cols.append(dict(va=va, offset=off, cd=cd, td=ptd, cdv=pcd, name=name))
    return cols


cols = scan_cols()
print('found %d COL structs' % len(cols))
by_va = {c['va']: c for c in cols}

INTEREST = [0x0054A4F0, 0x0054A5A0, 0x0054A5D0, 0x0054A610, 0x0054A240, 0x0054A4B0,
            0x0054A630, 0x0054A1F0, 0x0054A6E0, 0x0054A220, 0x0054A7B0, 0x0054A800]

print()
print('=== vtables whose slot list contains an INTEREST fn ===')
for c in cols:
    # vtable base sits right after COL: slots start at c.va+24
    slots = []
    va = c.va + 24
    for k in range(40):
        d = pe.dword(va + k * 4)
        if d is None:
            break
        # stop when we hit another COL ptr or non-code
        if d in by_va and k > 0:
            break
        if not (pe.is_text(d) or d == 0):
            break
        slots.append(d)
    if any(s in INTEREST for s in slots):
        print('COL %08X  name=%s  offset=%d' % (c['va'], c['name'], c['offset']))
        for k, s in enumerate(slots):
            mark = '  <== crash fn' if s == 0x0054A4F0 else ''
            print('    slot%2d %08X%s' % (k, s, mark))
        print()
