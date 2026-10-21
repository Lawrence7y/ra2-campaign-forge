import importlib.util, os, struct
HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location('pe_tools', os.path.join(HERE, 'pe_tools.py'))
pt = importlib.util.module_from_spec(spec); spec.loader.exec_module(pt)

EXE = r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
pe = pt.PE(EXE)
md = pt.make_md()


def show(lo, hi, title, mark=()):
    print('=== %s  [%08X..%08X] ===' % (title, lo, hi))
    ins = pt.disasm_range(pe, md, lo, hi)
    print(pt.fmt(ins, lo=lo, hi=hi, mark=mark))
    print()


show(0x007C8B3D, 0x007C8B60, 'free thunk 007C8B3D', mark=(0x007C8B3D,))
show(0x007C93E8, 0x007C9460, 'free body 007C93E8', mark=(0x007C93E8,))

# esi/esp discipline inside the free body
print('=== esi/ebp/esp touching instructions in 007C93E8..007C9460 ===')
ins = pt.disasm_range(pe, md, 0x007C93E8, 0x007C9460)
for i in ins:
    if any(r in i.op_str for r in ('esi', 'esp', 'ebp')) or i.mnemonic in ('push', 'pop', 'ret', 'call'):
        print('  %08X  %-20s %-8s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))

print()
show(0x007CF7BD, 0x007CF880, 'SBH free core 007CF7BD', mark=(0x007CF7BD,))
print('=== esi/esp discipline in 007CF7BD..007CF880 ===')
ins = pt.disasm_range(pe, md, 0x007CF7BD, 0x007CF880)
for i in ins:
    if 'esi' in i.op_str or i.mnemonic in ('push', 'pop', 'ret'):
        print('  %08X  %-20s %-8s %s' % (i.address, i.bytes.hex(), i.mnemonic, i.op_str))
