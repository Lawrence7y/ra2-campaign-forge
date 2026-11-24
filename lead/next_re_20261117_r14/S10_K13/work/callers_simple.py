import sys,csv,collections,bisect
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\\next_re_20261117_r14\\S10_K13\\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
name,base,vsz,rsz,ptr=[s for s in R.sections() if s[0]=='.text'][0]
data=R.PE.__data__[ptr:ptr+rsz]
direct=collections.defaultdict(list)
for ins in R.MD.disasm(data,base):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try:t=int(ins.op_str,16)
        except:continue
        direct[t].append(ins.address)
ivs=[]
for k,r in cov.items():
    try:va=int(k,16)
    except:continue
    ivs.append((va,k,r['name'],r['grade']))
ivs.sort(); starts=[x[0] for x in ivs]
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    if i>=0 and site<ivs[i][0]+0x2000:return ivs[i]
    return None
for va in [0x4D85D0,0x4D7330,0x741970,0x517FA0,0x739EC0,0x519630]:
 print('\n===',f'{va:08X}','===')
 for s in direct.get(va,[]):
  o=owner(s); print(f'{s:08X}',o if o else 'NO_OWNER')
