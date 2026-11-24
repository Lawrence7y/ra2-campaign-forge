import sys,csv,collections,bisect
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
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
BAN={0x51D6F0,0x51DAF0,0x51B1F0,0x51BAB0,0x522340,0x6FCDB0,0x4D8FB0}
# intervals for S10 unproved from coverage (entry+atlas sizes not needed: use coverage's next entry as upper)
s10=[]
for k,r in cov.items():
    if r['subsystem'].strip().upper()!='S10' or r['grade'].strip()=='[已证]':continue
    try:va=int(k,16)
    except:continue
    if va in BAN:continue
    s10.append((va,k,r['name']))
s10.sort(); starts=[x[0] for x in s10]
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    # upper bound next S10 unproved start
    if i>=0 and (i+1==len(s10) or site<s10[i+1][0]): return s10[i]
    return None
rows=[]
for target,sites in direct.items():
    tr=cov.get(f'{target:08X}'.lower())
    if not tr or tr['grade'].strip()!='[已证]':continue
    for site in sites:
        o=owner(site)
        if not o:continue
        rows.append((o[0],o[2],target,tr['name'],site))
# count unique external proved callees per owner and dump owners with >=2
c=collections.Counter((a,b) for a,b,_,_,_ in rows)
L=['OWNER\tOWNER_NAME\tN_PROVED_CALLEES\tCALLEES']
for (a,b),n in sorted(c.items(),key=lambda x:(-x[1],x[0][0])):
    if n>=2:
        cal=sorted({f'{t:08X}:{tn}' for aa,bb,t,tn,_ in rows if aa==a and bb==b})
        L.append(f'{a:08X}\t{b}\t{n}\t'+';'.join(cal))
print('OWNERS_WITH_2PLUS',len(L)-1,'ROWS',len(rows))
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/RING4_ALL_CALLEES.tsv'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
