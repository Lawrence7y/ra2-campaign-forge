#!/usr/bin/env python3
"""Probe 005B3A60 and ctor/vtable/RTTI closure."""
import sys
from re_lib import *
TARGET=0x005B3A60
CTOR=0x005B2DA0
print('=== TARGET BYTES ===')
print(dump_bytes(TARGET,192))
print('\n=== TARGET DISASM ENTRY TO RET ===')
print(fmt_block(TARGET,count=200,stop_ret=True,max_bytes=1024))
print('\n=== CTOR DISASM FIRST 160 INSTRUCTIONS ===')
print(fmt_block(CTOR,count=160,stop_ret=False,max_bytes=4096))
print('\n=== TARGET IMM32 OPERANDS ===')
for x in imm32_operands(disasm(TARGET,count=200,stop_ret=True,max_bytes=1024)):
    print(f'{x[0]:08X} imm=0x{x[1]:08X} {x[2]} {x[3]}')
print('\n=== CTOR IMM32 OPERANDS ===')
for x in imm32_operands(disasm(CTOR,count=160,stop_ret=False,max_bytes=4096)):
    print(f'{x[0]:08X} imm=0x{x[1]:08X} {x[2]} {x[3]}')
print('\n=== DWORD REFS TO TARGET ===')
refs=find_rdata_dword_refs(TARGET)
for r in refs:
    print(f'ref@0x{r:08X} sect={section_of(r)}')
    for p in range(r-4, r-4*40, -4):
        try: col=u32(p); rr=rtti_from_col(col)
        except Exception: continue
        if rr:
            print(f'  vbase=0x{p+4:08X} slot={(r-(p+4))//4} col=0x{col:08X} td=0x{rr[0]:08X} {rr[1]}')
            break
print('\n=== KNOWN VT/RTTI ===')
for a in [0x007EDCC0,0x007EDCA4,0x007EDC9C,0x007EDC94,0x805D28,0x817B18]:
    print(f'0x{a:08X}: col={u32(a-4):08X} first={u32(a):08X}', end=' ')
    try:
        rr=rtti_from_col(u32(a-4));
        if rr: print(f'td=0x{rr[0]:08X} {rr[1]}')
        else: print('no-rtti')
    except Exception as e: print('err',e)
for td in [0x817B18]:
    print(f'TD+8 @{td+8:08X}={cstr(td+8)}')
