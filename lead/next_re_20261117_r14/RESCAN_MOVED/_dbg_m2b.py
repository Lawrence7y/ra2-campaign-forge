# -*- coding: utf-8 -*-
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True
ea, size = 0x0045F230, 2138
ins = list(md.disasm(D[ea - VA:ea - VA + size], ea))
idx = {x.address: i for i, x in enumerate(ins)}
i = idx[0x0045FA39]
for j in range(max(0, i - 6), min(len(ins), i + 26)):
    mark = ''
    if ins[j].address == 0x0045FA39:
        mark = '  <== call'
    if ins[j].address == 0x0045FA76:
        mark += '  <== jcc target'
    print('%04d %08X %-8s %s%s' % (j, ins[j].address, ins[j].mnemonic, ins[j].op_str, mark))
print('target idx', idx.get(0x0045FA76), 'fall-through idx', i + 4)
