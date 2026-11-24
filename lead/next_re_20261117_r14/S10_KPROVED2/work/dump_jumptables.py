"""Dump jump tables + prologue for jump-table candidates."""
from re_core import PE
from func_analyze import disasm_range
import struct

pe=PE()
# (entry, ext_hi, jmp_off, table_addr, index_reg)
JT=[(0x004D74E0,0x004D7CCF,0x5c,0x004d7cd0,'ecx'),
    (0x004D7D50,0x004D8242,0x90,0x004d8244,'ecx'),
    (0x00702D40,0x007031FF,0x2ee,0x00703200,'ecx'),
    (0x00706640,0x00706BB7,0x24,0x00706bb8,'eax'),
    (0x00708C30,0x00708D54,0x1e,0x00708d54,'eax')]

for entry,hi,off,tbl,reg in JT:
    print(f'=========== {entry:08X} jump table @entry+{hex(off)} = dword ptr [{reg}*4 + {hex(tbl)}]')
    insns=disasm_range(pe,entry,hi)
    # print first 60 insns (prologue up to jmp) with absolute and relative
    for ins in insns[:60]:
        print(f'  {ins.address:08X} +{ins.address-entry:04x}: {ins.mnemonic:6s} {ins.op_str}')
        if ins.address-entry>=off+6: break
    # read jump table: print 12 entries from table_addr (and a few before)
    print('  --- table entries (from table_addr, up to 12) ---')
    for i in range(0,12):
        v=pe.u32va(tbl+4*i)
        if v is None: break
        sec=pe.sec_of_va(v)
        mark=' <TEXT' if sec=='.text' else ''
        print(f'    [{i}] @ {tbl+4*i:08X} = {v:08X}{mark}')
    print()
