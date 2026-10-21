import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()


def show(lo, hi, title, mark=()):
    print('=== %s [%08X..%08X] ===' % (title, lo, hi))
    ins = pt.disasm_range(pe, md, lo, hi)
    print(pt.fmt(ins, lo=lo, hi=hi, mark=mark))
    print()


# constructor site for VectorClass<PAUTileInsertType> vtable 0x007ECBFC
show(0x00543E60, 0x00543EF0, 'ctor site A (00543E93, 00543EC4)', mark=(0x00543E93, 0x00543EC4))
# the two in-cluster sites
show(0x0054A790, 0x0054A840, 'ctor sites in cluster (0054A7B8, 0054A808)', mark=(0x0054A7B8, 0x0054A808))

print('=== raw bytes at 0054A7B0..0054A840 ===')
print(pe.read(0x0054A7B0, 0x90).hex())
