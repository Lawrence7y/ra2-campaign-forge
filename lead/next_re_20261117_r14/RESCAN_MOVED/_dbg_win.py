# -*- coding: utf-8 -*-
"""定点反汇编窗口：python _dbg_win.py EA1 EA2 ...（打印前后若干条，用于人工判定）"""
import sys
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

for a in sys.argv[1:]:
    tgt = int(a, 16)
    print('=' * 90)
    for x in md.disasm(D[tgt - 0x30 - VA:tgt + 0x90 - VA], tgt - 0x30):
        mark = '  <<<' if x.address == tgt else ''
        print('%08X  %-16s %-8s %s%s' % (x.address, x.bytes.hex(' '), x.mnemonic, x.op_str, mark))
