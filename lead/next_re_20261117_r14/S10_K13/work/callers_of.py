import sys,csv,collections,re
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\\Project\\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
with ATL.open(encoding='utf-8-sig',newline='') as f: atl={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
name,base,vsz,rsz,ptr=[s for s in R.sections() if s[0]=='.text'][0]
data=R.PE.__data__[ptr:ptr+rsz]
direct=collections.defaultdict(list)
for ins in R.MD.disasm(data,base):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try:t=int(ins.op_str,16)
        except:continue
        direct[t].append(ins.address)
# intervals all known functions
ivs=[]
for k in set(atl)|set(cov):
    try:va=int(k,16)
    except:continue
    a=atl.get(k)
    try:sz=int(a.get('size','0'),0) if a and a.get('size') else 0
    except:sz=0
    if sz<=0 or sz>20000:sz=512
    ivs.append((va,va+sz,k))
ivs.sort(); starts=[x[0] for x in ivs]
import bisect
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    if i>=0 and site<ivs[i][1]:return ivs[i]
    return None
def desc(k):
    r=cov.get(k)
    return (r['name'] if r else '',r['grade'] if r else '',r['subsystem'] if r else '')
for va in [0x6FB010,0x739EC0,0x519630,0x4D7330,0x51CDB0,0x51D0D0,0x707D20,0x709820,0x7360C0,0x737BA0,0x737C90,0x743A50,0x4D5690]:
    print('\n=== TARGET',f'{va:08X}',desc(f'{va:08X}'.lower()),'===')
    for site in direct.get(va,[]):
        o=owner(site)
        k=o[2] if o else ''
        print(f'  SITE {site:08X} OWNER {k} {desc(k)}')
    pat=va.to_bytes(4,'little'); pos=0; lits=[]
    while True:
        i=data.find(pat,pos)
        if i<0:break
        lits.append(base+i);pos=i+1
    print('  LITERALS',','.join(f'{x:08X}' for x in lits[:40]),'N=',len(lits))
    for site in lits:
        o=owner(site)
        if o: print(f'    LIT_OWNER {site:08X} {o[2]} {desc(o[2])}')
