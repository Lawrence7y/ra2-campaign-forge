import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
IB = pe.image_base

print('=== raw dwords at COL 00804AD8 ===')
for k in range(0, 40, 4):
    print('  %08X = %08X' % (0x00804AD8 + k, pe.dword(0x00804AD8 + k)))

print()
print('=== raw bytes 00804AD0..00804B80 ===')
print(pe.read(0x00804AD0, 0xB0).hex())

print()
print('=== interpret 00804AD8 as COL with RVAs ===')
sig, off, cd, ptd, pcd, pself = [pe.dword(0x00804AD8 + k) for k in (0, 4, 8, 12, 16, 20)]
print('sig=%d off=%d cdOff=%d ptdRVA=%08X pcdRVA=%08X pselfRVA=%08X' % (sig, off, cd, ptd, pcd, pself))
print('pself+IB = %08X  (COL at 00804AD8? %s)' % ((pself + IB) & 0xFFFFFFFF, (pself + IB) & 0xFFFFFFFF == 0x00804AD8))
tdva = (ptd + IB) & 0xFFFFFFFF
print('TypeDescriptor VA %08X' % tdva)
off_ = pe.va_to_off(tdva)
print('  bytes:', pe.data[off_:off_ + 64])
print('  name:', pe.data[off_ + 8:pe.data.find(b"\0", off_ + 8)].decode('latin-1', 'replace'))
