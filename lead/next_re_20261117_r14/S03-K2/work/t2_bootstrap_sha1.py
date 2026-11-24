#!/usr/bin/env python3
"""T2: bootstrap registration order + flags.bit0 SHA1 tail verification."""
import sys, os, struct, hashlib
sys.path.insert(0, os.path.dirname(__file__))
from pehelper import *
OUT=[]
def p(s=""):
    OUT.append(str(s))
    try: print(s)
    except UnicodeEncodeError: print(s.encode('ascii','replace').decode())

p("=== MixFileClass::Bootstrap 0x5301A0 (first 160 insns) ===")
for ins in dis(0x5301A0, 0x400, 160):
    p(f"  {ins.address:08X}: {ins.bytes.hex():<20} {ins.mnemonic:8} {ins.op_str}")

p("\n=== flags.bit0 -> trailing SHA1 check (langmd.mix) ===")
path=ROOT+r'\ra2youli\langmd.mix'
with open(path,'rb') as f: data=f.read()
v0,flags,num,body=struct.unpack_from('<HHHI',data,0)
headlen=10
idxlen=num*12
datastart=headlen+idxlen
body_bytes=data[datastart:datastart+body]
tail=data[datastart+body:]
p(f"  flags=0x{flags:04X} num={num} body={body} datastart={datastart} tail_len={len(tail)}")
if len(tail)>=20:
    sha=hashlib.sha1(body_bytes).digest()
    p(f"  sha1(body)={sha.hex()}")
    p(f"  tail      ={tail[:20].hex()}")
    p(f"  EQUAL={sha==tail[:20]}")

p("\n=== new-style encrypted flag scan across all 17 MIX ===")
for fn in sorted(os.listdir(ROOT+r'\ra2youli')):
    if not fn.lower().endswith('.mix'): continue
    d=open(ROOT+r'\ra2youli\\'+fn,'rb').read(16)
    v0,flags,num,body=struct.unpack_from('<HHHI',d,0)
    # decide style: if as-new gives consistent filesize use new, else old
    sz=os.path.getsize(ROOT+r'\ra2youli\\'+fn)
    newrem=sz-(10+num*12)-body-(20 if flags&1 else 0)-(20 if flags&2 else 0)
    oldnum=struct.unpack_from('<H',d,0)[0]; oldbody=struct.unpack_from('<I',d,2)[0]
    oldrem=sz-(6+oldnum*12)-oldbody
    style='new' if abs(newrem)<=20 and abs(newrem)<abs(oldrem) else 'old'
    if style=='new':
        p(f"  {fn:<18} NEW v0={v0} flags=0x{flags:04X} num={num} bit0={flags&1} bit1={(flags>>1)&1} rem={newrem}")

with open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E_T2_bootstrap_sha1.txt'),'w',encoding='utf-8') as f:
    f.write('\n'.join(OUT))
p("\n[written E_T2_bootstrap_sha1.txt]")
