import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)


def rva2va(r):
    return r & 0xFFFFFFFF if r == 0 else (r + pe.image_base) & 0xFFFFFFFF


def cstr(va):
    off = pe.va_to_off(va)
    if off is None:
        return None
    end = pe.data.find(b'\0', off)
    return pe.data[off:end].decode('latin-1', 'replace')


def demangle_ms(name):
    """Very small subset of MSVC mangling -> readable."""
    if not name.startswith('.?A'):
        return name
    return name


def dump_col(col_va, label=''):
    sig, off, cd, ptd, pcd, pself = [pe.dword(col_va + k) for k in (0, 4, 8, 12, 16, 20)]
    print('--- COL %s @ %08X ---' % (label, col_va))
    print('  signature=%d offset=%d cdOffset=%d selfRVA=%08X (self->VA %08X)' % (
        sig, off, cd, pself, rva2va(pself)))
    td = rva2va(ptd)
    cdv = rva2va(pcd)
    print('  TypeDescriptor VA %08X' % td)
    if td:
        # TypeDescriptor: vftable ptr(4), spare(4), name[]
        nm = cstr(td + 8)
        print('  TypeDescriptor.name = %r' % nm)
    print('  ClassDescriptor VA %08X' % cdv)
    return nm if td else None


print('=== vtable 1 (COL @ 00804AD8) ===')
v1 = 0x007ECBE4
for i in range(8):
    d = pe.dword(v1 + i * 4)
    print('  slot%2d  %08X  @ %08X' % (i, d, v1 + i * 4))
dump_col(pe.dword(0x007ECBE0), 'vtable1')

print()
print('=== vtable 2 (COL @ 00804B08) ===')
v2 = 0x007ECC04
for i in range(10):
    d = pe.dword(v2 + i * 4)
    print('  slot%2d  %08X  @ %08X' % (i, d, v2 + i * 4))
dump_col(pe.dword(0x007ECC00), 'vtable2')

print()
print('=== raw bytes around 007ECBC0 ===')
print(pe.read(0x007ECBB0, 0x90).hex())
