import sys, struct
import pefile

PATH = r"D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe"
pe = pefile.PE(PATH, fast_load=True)
IB = pe.OPTIONAL_HEADER.ImageBase

secs = []
for s in pe.sections:
    nm = s.Name.rstrip(b'\x00').decode('latin-1')
    va = IB + s.VirtualAddress
    data = s.get_data()
    secs.append((nm, va, s.Misc_VirtualSize, data))

def seg(va):
    for nm, sva, vs, data in secs:
        if sva <= va < sva + vs:
            return nm, data, va - sva
    return None, None, None

def u32(va):
    nm, data, off = seg(va)
    if data is None or off + 4 > len(data):
        return None
    return struct.unpack_from('<I', data, off)[0]

def cstr(va, maxlen=200):
    nm, data, off = seg(va)
    if data is None:
        return None
    end = data.find(b'\x00', off, min(off + maxlen, len(data)))
    if end < 0:
        return None
    raw = data[off:end]
    try:
        return raw.decode('ascii')
    except UnicodeDecodeError:
        return raw.decode('latin-1')

def valid_col(col):
    """COL in .rdata, [col+0xC]=TD in .rdata/.data, TD+8 inline name .?AV/.?AU"""
    nm, _, _ = seg(col)
    if nm not in ('.rdata', '.data'):
        return None
    td = u32(col + 0xC)
    if td is None:
        return None
    nm2, _, _ = seg(td)
    if nm2 not in ('.rdata', '.data'):
        return None
    name = cstr(td + 8)
    if not name or not (name.startswith('.?AV') or name.startswith('.?AU')):
        return None
    return (td, name)

# find all RTTI vtable starts V in .rdata where [V-4] is a valid COL
vt_starts = []  # (V, td, name)
for nm, sva, vs, data in secs:
    if nm != '.rdata':
        continue
    # scan aligned dwords
    for off in range(0, vs - 4, 4):
        V = sva + off
        col = u32(V - 4)
        if col is None:
            continue
        r = valid_col(col)
        if r:
            td, name = r
            vt_starts.append((V, col, td, name))

vt_starts.sort()
print("N_RTTI_VT_STARTS=%d" % len(vt_starts))

entries = [int(x, 16) for x in sys.argv[1:]]
for entry in entries:
    hits = []
    for V, col, td, name in vt_starts:
        # walk slots until next COL boundary or non-text ptr
        for s in range(0, 400):
            sv = u32(V + 4 * s)
            if sv is None:
                break
            snm, _, _ = seg(sv)
            if snm != '.text':
                break
            if sv == entry:
                hits.append((V, s, col, td, name))
    print("ENTRY=%08X HITS=%d" % (entry, len(hits)))
    for V, s, col, td, name in hits:
        print("  vt=%08X slot=%d col=%08X td=%08X name=%s" % (V, s, col, td, name))
