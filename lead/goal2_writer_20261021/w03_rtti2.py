import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
IB = pe.image_base


def cstr_at_va(v, maxlen=200):
    off = pe.va_to_off(v)
    if off is None:
        return None
    end = pe.data.find(b'\0', off)
    if end < 0 or end - off > maxlen:
        return None
    return pe.data[off:end].decode('latin-1', 'replace')


print('=== raw dword map 0x00804A40 .. 0x00804BC0 ===')
a = 0x00804A40
while a < 0x00804BC0:
    row = []
    for k in range(4):
        d = pe.dword(a + k * 4)
        row.append('%08X:%08X' % (a + k * 4, d if d is not None else 0))
    print('  ' + '  '.join(row))
    a += 16

print()
print('=== probe candidate TypeDescriptors ===')
for cand in (0x00829078, 0x00804A88, 0x00804AC8, 0x00804B08, 0x00804B20, 0x00804B38, 0x00804B50):
    nm = cstr_at_va(cand + 8)
    print('  %08X : name@+8 = %r' % (cand, nm))

print()
print('=== search for .?A strings near 0x00829078 ===')
off = pe.va_to_off(0x00829078)
print('  va_to_off(00829078) =', hex(off) if off else None)
if off:
    print('  bytes:', pe.data[off:off + 96])
    i = pe.data.find(b'.?A', off)
    print('  first .?A at file %s -> VA %08X' % (hex(i) if i >= 0 else None,
                                                 (i + IB) if i >= 0 else 0))

print()
print('=== absolute-VA COL check: find dword == own address (pSelf) ===')
hits = []
for v in range(0x007E1000, 0x00812000 - 24, 4):
    f = [pe.dword(v + k * 4) for k in range(6)]
    if f[5] == v:
        nm = cstr_at_va(f[3] + 8) if f[3] else None
        if nm and nm.startswith('.?A'):
            hits.append((v, f, nm))
print('  absolute-VA COLs found: %d' % len(hits))
for v, f, nm in hits[:10]:
    print('   COL %08X sig=%d off=%d cdOff=%d pTD=%08X pCD=%08X  %s' % (
        v, f[0], f[1], f[2], f[3], f[4], nm))

print()
print('=== RVA COL check (pSelf = self - IB) ===')
hits2 = []
for v in range(0x007E1000, 0x00812000 - 24, 4):
    f = [pe.dword(v + k * 4) for k in range(6)]
    if f[5] == v - IB:
        nm = cstr_at_va(f[3] + IB + 8) if f[3] else None
        if nm and nm.startswith('.?A'):
            hits2.append((v, f, nm))
print('  RVA COLs found: %d' % len(hits2))
for v, f, nm in hits2[:10]:
    print('   COL %08X sig=%d off=%d cdOff=%d pTD=%08X pCD=%08X  %s' % (
        v, f[0], f[1], f[2], f[3], f[4], nm))

print()
print('=== where are .?A strings? (first 12) ===')
i = 0
n = 0
while n < 12:
    i = pe.data.find(b'.?A', i)
    if i < 0:
        break
    # map to VA
    va = None
    for s in pe.sections:
        if s['rawptr'] <= i < s['rawptr'] + s['rawsize']:
            va = s['va'] + (i - s['rawptr'])
            sec = s['name']
            break
    end = pe.data.find(b'\0', i)
    print('  file %06X VA %08X (%s) %r' % (i, va, sec, pe.data[i:end][:70].decode('latin-1', 'replace')))
    i += 1
    n += 1
