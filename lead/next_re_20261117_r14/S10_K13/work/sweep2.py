import sys,csv,re,collections,bisect,struct
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\\Project\\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
BAN={0x51D6F0,0x51DAF0,0x51B1F0,0x51BAB0,0x522340,0x6FCDB0,0x4D8FB0}
with ATL.open(encoding='utf-8-sig',newline='') as f: atl={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f: cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
name,base,vsz,rsz,ptr=[s for s in R.sections() if s[0]=='.text'][0]
data=R.PE.__data__[ptr:ptr+rsz]
# Collect call sites with clean executable disassembly (capstone skipdata=True)
direct=collections.defaultdict(list)
for ins in R.MD.disasm(data,base):
    if ins.mnemonic=='call' and ins.op_str.startswith('0x'):
        try:t=int(ins.op_str,16)
        except:continue
        direct[t].append(ins.address)
lit=collections.defaultdict(list)
for t in direct:
    pat=t.to_bytes(4,'little');pos=0
    while True:
        i=data.find(pat,pos)
        if i<0:break
        lit[t].append(base+i);pos=i+1
s10=[]
for k,r in cov.items():
    if r['subsystem'].strip().upper()!='S10' or k not in atl:continue
    va=int(k,16)
    if r['grade'].strip()=='[已证]' or va in BAN:continue
    a=atl[k]
    try:sz=int(a.get('size','0'),0) if a.get('size') else 0
    except:sz=0
    if sz<=0 or sz>20000:sz=512
    s10.append((va,va+sz,r['name'],f'{va:08X}'))
s10.sort(); starts=[x[0] for x in s10]
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    if i>=0 and site<s10[i][1]:return s10[i]
    return None
# direct and literal/vtable references into S10 functions; plus calls out of S10 functions
L=['OWNER\tOWNER_NAME\tKIND\tSITE\tTARGET\tTARGET_NAME\tTARGET_GRADE\tKW']
words=['ammo','weapon','target','threat','range','veter','experien','promot','deploy','unload','repair','reload','best','fire','attack','damage','upgrade','rank','elite','score','kill','crate','heal','occup','teleport','warp','chron','guard']
def desc(t):
    r=cov.get(f'{t:08X}'.lower())
    return (r['name'] if r else '',r['grade'] if r else '')
for va,end,nm,key in s10:
    # direct calls made by function
    for t in sorted(direct):
        for site in direct[t]:
            if va<=site<end:
                tn,tg=desc(t)
                blob=(nm+' '+tn).lower(); hit=[w for w in words if w in blob]
                if hit:L.append('\t'.join([key,nm,'call',f'{site:08X}',f'{t:08X}',tn,tg,','.join(hit)]))
    # occurrences of this entry as direct call target or literal
    for site in direct.get(va,[]):
        o=owner(site); on=o[2] if o else ''
        if on and on!=nm:
            blob=(on+' '+nm).lower(); hit=[w for w in words if w in blob]
            if hit:L.append('\t'.join([on,'external','called_by',f'{site:08X}',key,nm,'?',','.join(hit)]))
    for site in lit.get(va,[]):
        o=owner(site)
        if o and o[0]!=va:
            L.append('\t'.join([o[2],'external','litref',f'{site:08X}',key,nm,'?','vtable_or_literal']))
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/SWEEP2.tsv'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('ROWS',len(L)-1)
