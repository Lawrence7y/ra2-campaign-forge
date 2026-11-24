# -*- coding: utf-8 -*-
"""R16_SLOTN_B3 只读：capstone 反汇编定位两个装表点的函数体边界（atlas 缺）。"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
R14 = os.path.dirname(HERE)
PROBE = os.path.join(R14, 'PROBE_802')
sys.path.insert(0, PROBE)
import probe
import capstone
sys.dont_write_bytecode = True
EXE = os.path.join(os.path.dirname(os.path.dirname(R14)), 'ra2youli', 'gamemd.exe')
img = probe.Image(EXE)

def dump(site, back=0x120, fwd=0x90):
    s = int(site, 16)
    lo, hi = s - back, s + fwd
    code = bytes(img.buf[lo-img.base:hi-img.base])
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
    md.detail = True
    md.skipdata = True
    print('==== site', site)
    for ins in md.disasm(code, lo):
        mark = ' <<< INSTALL' if ins.address == s else ''
        if ins.mnemonic in ('ret','retf','push','xor','sub') or ins.address == s or (s-0x30 <= ins.address <= s+0x10):
            print('  %08X: %-20s %-30s%s' % (ins.address, ins.bytes.hex(), ins.mnemonic+' '+ins.op_str, mark))

dump('006AF13D')
dump('006B6C2D')
