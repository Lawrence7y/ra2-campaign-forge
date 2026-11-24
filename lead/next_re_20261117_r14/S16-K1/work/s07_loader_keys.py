"""Step 7: enumerate all string pushes in the loader and pair with next INI-reader call
and first field write. Also scan for AuxBuildings variants globally."""
import sys, os, struct, re
sys.path.insert(0, os.path.dirname(__file__))
from re_lib import *

b=Bin()
ins=disasm_range(b,0x6CEA20,0x6CEA20+1085)
byaddr={i.address:i for i in ins}

INI_READERS={0x5283D0:'ReadDouble',0x5295F0:'ReadBool',0x528A10:'ReadString',
             0x5276D0:'ReadInt',0x474EE0:'ReadAction?',0x7514D0:'SoundIndex?',
             0x7C8D20:'strcmp?',0x4653C0:'ParseList?'}
out=[]
out.append("=== all push <data-VA> in loader with decoded C string ===")
for i in ins:
    if i.id==0: continue
    if i.mnemonic!='push' or not i.op_str.startswith('0x'): continue
    va=int(i.op_str,16)
    if not (0x7E1000<=va<0xB7A000): continue
    try: s=cstr(b,va,80)
    except Exception: continue
    if not s or any(ord(c)<9 for c in s): continue
    out.append(f"  {i.address:08X} push {va:08X}  {s!r}")

out.append("\n=== key -> reader call -> first [ebp+disp] write within 12 insns ===")
for i in ins:
    if i.id==0 or i.mnemonic!='push' or not i.op_str.startswith('0x'): continue
    va=int(i.op_str,16)
    if not (0x7E1000<=va<0xB7A000): continue
    try: s=cstr(b,va,80)
    except Exception: continue
    if not re.fullmatch(r'[A-Za-z][A-Za-z0-9.]{2,40}',s): continue
    k=ins.index(i)
    reader=None
    for j in range(k+1,min(len(ins),k+12)):
        x=ins[j]
        if x.mnemonic=='call' and x.op_str.startswith('0x'):
            t=int(x.op_str,16)
            if t in INI_READERS:
                reader=(x.address,t,INI_READERS[t]); break
    if not reader: continue
    writes=[]
    for j in range(reader[0] and ins.index(byaddr[reader[0]])+1 or 0,
                   min(len(ins),ins.index(byaddr[reader[0]])+18)):
        x=ins[j]
        m=re.match(r'(byte|dword|word) ptr \[ebp \+ (0x[0-9a-f]+)\]',x.op_str)
        if x.mnemonic=='mov' and m:
            writes.append((x.address,m.group(1),int(m.group(2),16),x.bytes.hex()))
            if len(writes)>=3: break
    out.append(f"  key {s:<26s} va={va:08X} push@{i.address:08X} reader={reader[1]:08X}/{reader[2]}@{reader[0]:08X} writes="+"; ".join(f"{a:08X}:[{o:x}]={w}" for a,t,o,w in writes))

out.append("\n=== AuxBuildings string variants globally ===")
for pat in (b'AuxBuildings',b'AuxBuilding',b'SW.AuxBuildings',b'SuperWeapon'):
    hits=find_bytes(b,pat)
    out.append(f"  {pat!r}: {len(hits)} -> "+" ".join(f"{x:08X}" for x in hits[:20]))

text="\n".join(out)
open(os.path.join(os.path.dirname(__file__),'..','EVIDENCE','E07_loader_keys_pairing.txt'),'w',encoding='utf-8').write(text)
print(text)
