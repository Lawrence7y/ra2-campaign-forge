#!/usr/bin/env python3
"""T2: MIX lookup chain byte-level evidence (Get_File / Find / list head / binary search)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

def dump_range(start, nbytes, label, cap=80):
    p(f"\n=== {label} @0x{start:X} ===")
    for ins in dis(start, nbytes, cap):
        p(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")

dump_range(0x473D10, 0x70, "CCFileClass::Get_File (slot7)")
dump_range(0x5B4420, 0xC0, "MixFileClass::Find (contains strupr/hash/listhead/binary)")
dump_range(0x5B44B1, 0x70, "Find -> binary search over index")

# Find the global list-head var [0xABEFE0] xrefs (need scan .text for 8B 2D/05 ...)
p("\n=== scan for xrefs to 0xABEFE0 (MIX list head) ===")
import struct
text = read(0x401000, 0x3DF38D)
# patterns: 8b 2d e0 ef ab 00 (mov ebp,[abs]) / 8b 05 / 8b 0d / a1
for pat,name in [(b'\x8b\x2d\xe0\xef\xab\x00','mov ebp,[0xABEFE0]'),
                 (b'\x8b\x05\xe0\xef\xab\x00','mov eax,[0xABEFE0]'),
                 (b'\xa1\xe0\xef\xab\x00','mov eax,[0xABEFE0](a1)'),
                 (b'\x8b\x0d\xe0\xef\xab\x00','mov ecx,[0xABEFE0]')]:
    idx=0
    while True:
        i=text.find(pat,idx)
        if i<0: break
        p(f"  {name} @ 0x{0x401000+i:08X}")
        idx=i+1

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T2_lookup_chain.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T2_lookup_chain.txt]")
