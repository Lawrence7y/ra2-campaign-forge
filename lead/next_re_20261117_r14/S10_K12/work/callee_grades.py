
import sys,csv,re
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K12\work')
import re_lib as R
COV=Path(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv')
with COV.open(encoding='utf-8',newline='') as f:
    cov={r['entry'].strip().lower():r for r in csv.DictReader(f,delimiter='\t')}

def g(va):
    r=cov.get(f'{va:08X}'.lower())
    if r: return r['grade'].strip()+' '+r['name'].strip()
    return 'NOT_IN_COV'

funcs={'ROW1':(0x51D6F0,1013),'ROW2':(0x51DAF0,223),'ROW3':(0x51B1F0,347),'ROW4':(0x51BAB0,1239),'ROW5':(0x522340,393)}
vt=0x7EB058
for nm,(a,sz) in funcs.items():
    print('\n===',nm,f'{a:08X}','direct calls / vtable indirect calls ===')
    seen=set()
    for ins in R.MD.disasm(R.read(a,sz),a):
        if ins.mnemonic.startswith('call'):
            op=ins.op_str
            # direct target
            m=re.match(r'0x([0-9a-fA-F]+)',op)
            if m:
                va=int(m.group(1),16)
                key=('D',va)
                if key not in seen:
                    seen.add(key); print(f'  {ins.address:08X} DIRECT {va:08X} -> {g(va)}')
            elif 'ptr [' in op:
                mm=re.search(r'\[\w+ \+ (0x[0-9a-fA-F]+)\]',op)
                if mm:
                    off=int(mm.group(1),16)
                    key=('V',off)
                    if key not in seen:
                        seen.add(key)
                        try: tgt=R.u32(vt+off); tg=f'{tgt:08X}'
                        except: tg='?'
                        print(f'  {ins.address:08X} VT+0x{off:X} -> {tg} {g(tgt) if tg!="?" else ""}')
                else:
                    key=('V?',op)
                    if key not in seen: seen.add(key); print(f'  {ins.address:08X} INDIRECT {op}')
