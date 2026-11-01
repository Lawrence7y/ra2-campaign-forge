import struct, capstone
blob = open(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe', 'rb').read()
CODE = blob[0x1000:0x1000+0x3E0000]
TVA = 0x401000
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True
insns = {}
i = 0; n = len(CODE)
while i < n:
    off = i
    try:
        for ins in md.disasm(CODE[off:off+16], TVA+off):
            insns[ins.address] = (ins.mnemonic, ins.op_str, ins.size)
            i = ins.address + ins.size - TVA
            break
        else:
            i = off + 1
    except Exception:
        i = off + 1
print('decoded', len(insns))


def dest_reg(ops):
    # 'dword ptr [esi + 0x28], edx'
    inner = ops[ops.index('[')+1:ops.index(']')]
    reg = inner.split(' + ')[0].strip()
    return reg


rows = []
for a, (mn, ops, sz) in sorted(insns.items()):
    if mn != 'mov':
        continue
    if not ops.startswith('dword ptr ['):
        continue
    d = ops[:ops.index(',')]
    for disp in (0x28, 0x30):
        if d.endswith('+' + hex(disp)[2:] + ']'):
            r = dest_reg(d)
            if r not in ('esp', 'ebp'):
                rows.append((a, d, ops, disp))
for r in rows:
    print('0x%08X  [%s]  %s  (disp=0x%x)' % (r[0], r[1][10:-1], r[2], r[3]))
print('total non-esp/ebp dword stores with disp 0x28/0x30:', len(rows))
