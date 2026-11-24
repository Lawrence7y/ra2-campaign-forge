#!/usr/bin/env python3
"""R107 exec common helpers: PE mapping, function-start finding, linear disasm, backward tracking.

Run: python3 _r107/_exec/r107_lib.py  (self-test: print function start for each of the 7 dec sites)
"""
import sys, os, struct

REPO = '/home/t628/projects/ra2-campaign-forge'
EXE = os.path.join(REPO, 'ra2bench/gamemd.exe')
sys.path.insert(0, os.path.join(REPO, '_r104/vendor'))

import pefile, capstone
from capstone import Cs, CS_ARCH_X86, CS_MODE_32
import iced_x86

PE = pefile.PE(EXE, fast_load=True)
DATA = open(EXE, 'rb').read()
IMAGEBASE = PE.OPTIONAL_HEADER.ImageBase
_S = {s.Name.decode().rstrip('\0'): s for s in PE.sections}


def sec_of(va):
    rva = va - IMAGEBASE
    for name, s in _S.items():
        if s.VirtualAddress <= rva < s.VirtualAddress + max(s.Misc_VirtualSize, s.SizeOfRawData):
            return name, s
    return None, None


def va2off(va):
    name, s = sec_of(va)
    if s is None:
        raise ValueError('va not mapped: %x' % va)
    return s.PointerToRawData + (va - IMAGEBASE - s.VirtualAddress)


def off2va(off):
    for name, s in _S.items():
        if s.PointerToRawData <= off < s.PointerToRawData + s.SizeOfRawData:
            return IMAGEBASE + s.VirtualAddress + (off - s.PointerToRawData)
    return None


def rd(va, n):
    o = va2off(va)
    return DATA[o:o + n]


TEXT = _S['.text']
TEXT_VA = IMAGEBASE + TEXT.VirtualAddress
TEXT_END = TEXT_VA + TEXT.Misc_VirtualSize

_md = Cs(CS_ARCH_X86, CS_MODE_32)
_md.detail = False


def dis(va, nbytes):
    """linear disasm lite from va for nbytes"""
    return list(_md.disasm(rd(va, nbytes), va))


def find_func_start(target):
    """Find the function start containing target: nearest preceding run of >=2 0xCC bytes,
    then returns list of candidates (byte after the run) that linearly disassemble across target."""
    o = va2off(target)
    cands = []
    i = o - 1
    while i > va2off(TEXT_VA) + 2:
        if DATA[i] == 0xCC and DATA[i - 1] == 0xCC:
            # skip back to start of the CC run
            j = i
            while j > 0 and DATA[j] == 0xCC:
                j -= 1
            cands.append(off2va(j + 1))
            if len(cands) >= 6:
                break
            i = j - 1
        else:
            i -= 1
    good = []
    for c in cands:
        ins = dis(c, target - c + 16)
        starts = [x.address for x in ins]
        if target in starts:
            good.append((c, ins))
    return good


def ins_str(x):
    return '%08x %-24s %s %s' % (x.address, x.bytes.hex(), x.mnemonic, x.op_str)


if __name__ == '__main__':
    TABS = [(0x4c8114, 46, 0x4c6ccd), (0x69b15c, 4, 0x69af2c), (0x6a92c4, 3, 0x6a8e0c),
            (0x6dfdec, 145, 0x6dd8da), (0x708d54, 5, 0x708c44), (0x728e08, 7, 0x728c0d),
            (0x7291ac, 7, 0x728e62)]
    for base, n, dec in TABS:
        g = find_func_start(dec)
        print('table %08x n=%d dec=%08x funcstarts=%s' % (base, n, dec, [hex(c) for c, _ in g]))
