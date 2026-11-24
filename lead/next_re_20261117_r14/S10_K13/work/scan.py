import sys,csv,re,hashlib,datetime,collections
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
COV=ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATL=ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
BAN={0x51D6F0,0x51DAF0,0x51B1F0,0x51BAB0,0x522340,0x6FCDB0,0x4D8FB0}
with ATL.open(encoding='utf-8-sig',newline='') as f:
    atl={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
with COV.open(encoding='utf-8',newline='') as f:
    cov={r['entry'].strip().lower():r for r in csv.DictReader([f.readline().replace(',','\t')]+list(f),delimiter='\t')}
L=[]
def log(s=''):L.append(str(s))
log('S10_K13 FULL CANDIDATE SCAN')
log('TIME='+datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat())
log('EXE_SHA='+hashlib.sha256(R.EXE.read_bytes()).hexdigest().upper())
log('COV_SHA='+hashlib.sha256(COV.read_bytes()).hexdigest().upper())

# all direct call sites in .text once; both rel32 and short
name,base,vsz,rsz,ptr=[s for s in R.sections() if s[0]=='.text'][0]
data=R.PE.__data__[ptr:ptr+rsz]
direct=collections.defaultdict(list)
for ins in R.MD.disasm(data,base):
    if ins.mnemonic in ('call','jmp') and ins.op_str.startswith('0x'):
        try:t=int(ins.op_str,16)
        except:continue
        if 0x400000<=t<0x900000: direct[t].append((ins.address,ins.mnemonic,ins.bytes.hex(),ins.op_str))
log('DIRECT_TARGETS='+str(len(direct))+' CALL_SITES='+str(sum(len(v) for v in direct.values())))

# all 4-byte VA literal occurrences in .text (for jump tables/vtables indirects)
lit=collections.defaultdict(list)
for t in sorted(direct):
    pat=t.to_bytes(4,'little'); pos=0
    while True:
        i=data.find(pat,pos)
        if i<0:break
        lit[t].append(base+i);pos=i+1

KEY=re.compile(r'ammo|weapon|target|threat|range|veter|experien|promot|deploy|unload|repair|reload|enter|occup|best|fire|attack|damage|upgrade|rank|elite|veteran|score|kill|crate|heal',re.I)

s10=[]
for k,r in cov.items():
    if r['subsystem'].strip().upper()!='S10' or k not in atl: continue
    va=int(k,16)
    if r['grade'].strip()=='[已证]' or va in BAN: continue
    s10.append((va,r))
log('CANDIDATE_S10_UNPROVED_EXCL_BAN='+str(len(s10)))
out=[]
for va,r in s10:
    a=atl[f'{va:08X}'.lower()]
    try: sz=int(a.get('size','0'),0) if a.get('size') else 0
    except: sz=0
    if sz<=0 or sz>20000: sz=512
    b=R.read(va,min(sz,20000))
    txt=''
    for ins in R.MD.disasm(b,va):
        txt+=f'{ins.address:08X}|{ins.bytes.hex()}|{ins.mnemonic}|{ins.op_str}\n'
    dl=direct.get(va,[])
    li=lit.get(va,[])
    score=0; why=[]
    blob=(r['name']+' '+r['one_line_semantics']).lower()
    if KEY.search(blob): score+=6;why.append('name_sem_keyword')
    if dl: score+=3;why.append('direct_callers='+str(len(dl)))
    if li: score+=2;why.append('va_literals='+str(len(li)))
    if len(txt)>4000: score+=1;why.append('large')
    # strings referenced as immediates in push/mov
    strs=[]
    for m in re.finditer(r'(?:push|mov)\s+(?:dword ptr )?(?:0x)?([0-9a-fA-F]{6,8})\b',txt):
        p=int(m.group(1),16)
        if 0x500000<=p<0x900000:
            try:
                s=R.cstring(p,60)
                if len(s)>=3 and all(32<=ord(c)<127 for c in s): strs.append(s)
            except: pass
    if any(KEY.search(s) for s in strs): score+=4;why.append('keyword_string='+';'.join([s for s in strs if KEY.search(s)][:3]))
    if score>=6:
        out.append((score,va,sz,r['grade'],r['name'],r['one_line_semantics'],','.join(why),len(dl),len(li)))
out.sort(reverse=True)
log('SCORE6_COUNT='+str(len(out)))
log('SCORE\tENTRY\tSIZE\tGRADE\tNAME\tSEM\tWHY\tDIRECT_CALLERS\tVA_LITS')
for x in out:
    log('\t'.join(str(v).replace('\t',' ') for v in x))
# also summary counts by name keyword regardless direct caller
kwcnt=collections.Counter()
for va,r in s10:
    blob=(r['name']+' '+r['one_line_semantics']).lower()
    for kw in ['ammo','weapon','target','threat','range','veter','experien','promot','deploy','unload','repair','reload','enter','occup','best','fire','attack','damage','upgrade','rank','elite','score','kill']:
        if kw in blob: kwcnt[kw]+=1
log('KEYWORD_COUNTS='+repr(dict(kwcnt)))
p=str(ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/CANDIDATE_SCAN.tsv')
Path(p).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
print('WROTE',p,'lines',len(L),'candidates',len(out))
