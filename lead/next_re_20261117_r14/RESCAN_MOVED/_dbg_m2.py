# -*- coding: utf-8 -*-
import bisect
import pefile
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
from capstone.x86 import *

pe = pefile.PE(r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe')
IB = pe.OPTIONAL_HEADER.ImageBase
sec = next(s for s in pe.sections if s.Name.rstrip(b'\x00') == b'.text')
VA = IB + sec.VirtualAddress
D = sec.get_data()
md = Cs(CS_ARCH_X86, CS_MODE_32); md.detail = True; md.skipdata = True

atlas = []
for ln in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv', encoding='utf-8').read().splitlines()[1:]:
    p = ln.split('\t')
    if len(p) >= 3:
        atlas.append((int(p[0], 16), int(p[1]), int(p[2])))
atlas.sort()
addrs = [a[0] for a in atlas]
for tgt in (0x442273, 0x4322A if False else 0x40322A, 0x414174):
    i = bisect.bisect_right(addrs, tgt) - 1
    ea, size, ni = atlas[i]
    print('=== site %08X -> func %08X size %d n_instr %d' % (tgt, ea, size, ni))
    ins = list(md.disasm(D[ea - VA:ea - VA + size], ea))
    for x in ins[:120]:
        mark = ' <== SITE' if x.address == tgt else ''
        print('  %08X %-8s %s%s' % (x.address, x.mnemonic, x.op_str, mark))
