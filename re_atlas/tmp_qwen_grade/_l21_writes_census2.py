import struct, capstone
blob = open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe', 'rb').read()
CODE = blob[0x1000:0x1000+0x3E0000]
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
insns = {}
i = 0; n = len(CODE)
while i < n:
    off = i
    try:
        for ins in md.disasm(CODE[off:off+16], 0x401000+off):
            insns[ins.address] = (ins.mnemonic, ins.op_str, ins.size)
            i = ins.address + ins.size - 0x401000
            break
        else:
            i = off + 1
    except Exception:
        i = off + 1

SPILL = {'esp', 'ebp'}
def base_of(d):
    inner = d[d.index('[')+1:d.index(']')]
    if '*' in inner:
        return None
    parts = inner.split(' + ')
    return parts[0].strip()

def is_field(d, disp):
    if not d.rstrip().endswith('0x%x]' % disp):
        return False
    b = base_of(d)
    return b is not None and b not in SPILL

rows28 = []
rows30 = []
for a, (mn, ops, sz) in sorted(insns.items()):
    if mn != 'mov':
        continue
    if ',' not in ops:
        continue
    d = ops[:ops.index(',')]
    src = ops[ops.index(',')+1:]
    if not d.startswith('dword ptr ['):
        continue
    # source must be a register (value-carrying) or another dword field
    if is_field(d, 0x28):
        rows28.append((a, d, src))
    if is_field(d, 0x30):
        rows30.append((a, d, src))

print('=== dword stores to [reg+0x28] (reg != esp/ebp):', len(rows28), '===')
for a, d, s in rows28:
    print('0x%08X  %s <- %s' % (a, d.strip(), s.strip()))
print()
print('=== dword stores to [reg+0x30]:', len(rows30), '===')
for a, d, s in rows30:
    print('0x%08X  %s <- %s' % (a, d.strip(), s.strip()))
