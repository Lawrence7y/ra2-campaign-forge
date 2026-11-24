#!/usr/bin/env python3
"""T2: complete Find disasm (list traversal order) + old-style MIX header check."""
import sys, os, struct
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

p("=== Find 0x5B4430 full (0x4430..0x45C0) ===")
for ins in dis(0x5B4430, 0x1A0, 140):
    p(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")

p("\n=== old-style MIX header check (theme.mix / thememd.mix) ===")
for fn in ['theme.mix','thememd.mix','expandmd98.mix']:
    path=ROOT+'\\ra2youli\\'+fn
    with open(path,'rb') as f: h=f.read(64)
    num=struct.unpack_from('<H',h,0)[0]
    body=struct.unpack_from('<I',h,2)[0]
    sz=os.path.getsize(path)
    # old style: u16 num + u32 body => index at 6, tail maybe
    rem = sz - (6 + num*12) - body
    p(f"  {fn}: num(u16@0)={num} body(u32@2)={body} filesize={sz} rem(after 6+12n+body)={rem}")
    # new style interpretation
    v0,flags,n2,b2=struct.unpack_from('<HHHI',h,0)
    rem2=sz-(10+n2*12)-b2-(20 if flags&1 else 0)-(20 if flags&2 else 0)
    p(f"     as-new: v0={v0} flags={flags:#x} num={n2} body={b2} rem2={rem2}")

p("\n=== MIX bootstrap / registration: find writes to 0xABEFE0 ===")
text=read(0x401000,0x3DF38D)
for pat in [b'\xa3\xe0\xef\xab\x00', b'\x89\x05\xe0\xef\xab\x00', b'\x89\x0d\xe0\xef\xab\x00']:
    idx=0
    while True:
        i=text.find(pat,idx)
        if i<0: break
        p(f"  write @0x{0x401000+i:08X}: {pat.hex()}")
        idx=i+1

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T2_findorder_header.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T2_findorder_header.txt]")
