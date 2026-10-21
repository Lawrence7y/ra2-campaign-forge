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


# The static instance at 0x00AA1078 -- proves the field layout.
print('=== static instance VectorClass<PAUTileInsertType> at 0x00AA1078 ===')
for k in range(0, 0x18, 4):
    a = 0x00AA1078 + k
    d = pe.dword(a)
    print('  +0x%02X @%08X = %s' % (k, a, ('%08X' % d) if d is not None else '--unmapped--'))
print()

show(0x0054A840, 0x0054A8A0, 'ctor / copy-ctor tail (0054A850..)', mark=(0x0054A850, 0x0054A878, 0x0054A88D))
show(0x0054A180, 0x0054A1D0, 'ctor candidate (0054A190..)', mark=(0x0054A190,))
show(0x0054A5A0, 0x0054A620, 'slots 3/4 (0054A5A0, 0054A5D0)', mark=(0x0054A5A0, 0x0054A5D0))

print('=== virtual-dispatch sites for vtable slot 2 (call [reg+8]) ===')
ins = pt.disasm_range(pe, md, pe.text_lo, 0x007E1000)
n = 0
for i in ins:
    if i.mnemonic == 'call' and '[' in i.op_str and '+ 8]' in i.op_str:
        n += 1
        if n <= 30:
            print('  %08X  %-8s %s' % (i.address, i.mnemonic, i.op_str))
print('  total call [reg+8] sites: %d' % n)

print()
print('=== all call [reg+disp] with disp in {0,4,8,0xC} count ===')
from collections import Counter
c = Counter()
for i in ins:
    if i.mnemonic == 'call' and '[' in i.op_str:
        d = i.op_str.split('+')[-1].split(']')[0].strip() if '+' in i.op_str else '0'
        c[d] += 1
for k in sorted(c, key=lambda x: (len(x), x))[:20]:
    print('   +%s : %d' % (k, c[k]))
