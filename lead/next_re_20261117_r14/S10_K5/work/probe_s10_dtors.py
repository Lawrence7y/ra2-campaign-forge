#!/usr/bin/env python3
"""Probe all S10 scalar-deleting-dtor candidates found by strict sweep."""
from re_lib import *
import csv
from pathlib import Path
CAND=[0x004E0170,0x00523350,0x005B3A60,0x006B1390,0x006B8140,0x00746E80]
COV=Path(r'D:\Project\ra2-campaign-forge/lead/next_re_20261117_r14/COVERAGE/coverage.tsv')
rows={}
with COV.open('r',encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f,delimiter='\t'): rows[r['entry'].strip().lower()]=r
for va in CAND:
    print('\n===== 0x%08X =====' % va)
    rr=rows.get('%08x'%va)
    print('ROW '+( ('\t'.join([rr['subsystem'],rr['name'],rr['grade']])) if rr else 'NO_ROW'))
    print(fmt_block(va,count=120,stop_ret=True,max_bytes=4096))
    print('-- VA refs / vtable/RTTI --')
    hits=find_vtable_containing(va)
    if not hits: print('  NO_DATA_REF')
    for ref,best in hits:
        print(f'  ref=0x{ref:08X}')
        if best:
            vb,col,tdr,slot=best
            print(f'    vbase=0x{vb:08X} slot={slot} col=0x{col:08X} td=0x{tdr[0]:08X} {tdr[1]}')
        else: print('    no COL/RTTI scan-back')
    print('-- short imm32 calls --')
    for a,imm,m,o in imm32_operands(disasm(va,count=120,stop_ret=True,max_bytes=4096)):
        if m=='call' or imm in (1,4): print(f'  {a:08X} imm=0x{imm:08X} {m} {o}')
