import sys,csv,re,collections,struct
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
# all functions in image: atlas + coverage keys; assign sites by interval containment to known S10 unproved funcs
s10=[]
for k,r in cov.items():
    if r['subsystem'].strip().upper()!='S10' or k not in atl:continue
    va=int(k,16)
    if r['grade'].strip()=='[已证]' or va in BAN:continue
    a=atl[k]
    try:sz=int(a.get('size','0'),0) if a.get('size') else 0
    except:sz=0
    if sz<=0 or sz>20000:sz=512
    s10.append((va,va+sz,r))
s10.sort()
def owner(site):
    lo,hi=0,len(s10)-1
    # linear backward enough; use bisect
    import bisect
    i=bisect.bisect_right([x[0] for x in s10],site)-1
    if i>=0 and site<s10[i][1]:return s10[i]
    return None
rows=[]
for site in []: pass
# scan all direct call sites in .text, group by call target and owner
for t,sites in direct.items():
    for s in sites:
        o=owner(s)
        if o: rows.append((o[0],t,s))
# call target descriptions
words=['ammo','weapon','target','threat','range','veter','experien','promot','deploy','unload','repair','reload','best','fire','attack','damage','upgrade','rank','elite','score','kill','crate','heal','occup']
L=['OWNER\tOWNER_NAME\tTARGET\tTARGET_NAME\tTARGET_GRADE\tSITE\tKW']
for own,t,s in rows:
    rr=cov.get(f'{own:08X}'.lower()); tr=cov.get(f'{t:08X}'.lower())
    blob=((rr['name'] if rr else '')+' '+(rr['one_line_semantics'] if rr else '')+' '+(tr['name'] if tr else '')+' '+(tr['one_line_semantics'] if tr else '')).lower()
    hit=[w for w in words if w in blob]
    if hit:
        L.append('\t'.join([f'{own:08X}',rr['name'] if rr else '',f'{t:08X}',tr['name'] if tr else '',tr['grade'] if tr else '',f'{s:08X}',','.join(hit)]))
print('CALLROWS',len(rows),'KEYROWS',len(L)-1)
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/CALLER_KEYWORD_SCAN.tsv'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
