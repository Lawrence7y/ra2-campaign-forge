from pathlib import Path
import sys,csv,re
sys.path.insert(0,str(Path(__file__).parent))
from scan_candidates import load,feats
cov,atl,names,pe,data,image,off,string_at,md,dis=load()
prev={'0051D6F0','0051DAF0','0051B1F0','0051BAB0','00522340'}
for r in cov:
 if r['subsystem']!='S10' or r['grade']=='[已证]' or r['entry'].upper() in prev:continue
 e=r['entry'].strip().lower(); va=int(e,16)
 ins=dis(e); txt='\n'.join(f'{m.address:08X} {m.mnemonic} {m.op_str}' for m in ins if m.id)
 import re
 consts={int(x,16) for m in ins if m.id for x in re.findall(r'0x([0-9a-f]+)',m.op_str)}
 hit=[c for c in [0x1b,0x1c,0x1d,0x1e,0x1f,0x20] if c in consts]
 if len(hit)>=2 or '816CAC' in txt.upper():
  f=feats(ins,off,string_at,names)
  writes=';'.join(f'{w[1]}+0x{w[2]:X}' for w in f['writes'])
  known=';'.join(x[1] for x in f['calls'] if x[1] and not x[1].startswith('sub_'))
  print(r['entry'],r['name'],'hits',[hex(x) for x in hit],'writes',writes,'known',known)
