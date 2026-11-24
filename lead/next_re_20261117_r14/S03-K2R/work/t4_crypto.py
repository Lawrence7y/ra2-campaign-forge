#!/usr/bin/env python3
"""T4: compression/encryption byte-level scan (imports, constants, key funcs)."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

p("=== DLL imports (compression/encryption candidates) ===")
for entry in pe.DIRECTORY_ENTRY_IMPORT:
    dll=entry.dll.decode('latin1')
    if any(k in dll.lower() for k in ('blow','crypt','zlib','lz','zip','pack')):
        p(f"  {dll}")
        for imp in entry.imports:
            p(f"    {imp.name.decode('latin1') if imp.name else hex(imp.address)} @ {imp.address:08X}")

p("\n=== string hits: LZO/LZ/Blowfish/RSA/crypt ===")
text=read(0x401000,0x3DF38D); data=read(0x812000,0x367BE4)
for blob,base,nm in [(text,0x401000,'text'),(data,0x812000,'data')]:
    import re
    for pat in [rb'Blowfish',rb'blowfish',rb'LZO',rb'lzo',rb'compress',rb'Compress',rb'RSA',rb'PKStraw',rb'encrypt',rb'decrypt']:
        for m in re.finditer(pat,blob):
            p(f"  {nm} {pat.decode()} @ 0x{base+m.start():08X}: {blob[m.start():m.start()+40]!r}")
            break

p("\n=== encryption flags bit1 handler @0x5B3D00..0x5B3D30 ===")
for ins in dis(0x5B3D00,0x40,20):
    p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic:8} {ins.op_str}")

p("\n=== RSA exponent constant @0x52A6AF area ===")
for ins in dis(0x52A690,0x40,20):
    p(f"  {ins.address:08X}: {ins.bytes.hex():<18} {ins.mnemonic:8} {ins.op_str}")
p(f"  u32 @0x52A6AF = 0x{u32(0x52A6AF):08X}")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T4_crypto.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T4_crypto.txt]")
