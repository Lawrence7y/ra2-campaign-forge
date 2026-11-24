import sys,csv,re,collections
from pathlib import Path
sys.path.insert(0,r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K13\work')
import re_lib as R
ROOT=Path(r'D:\Project\ra2-campaign-forge')
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
KEY=re.compile(r'ammo|weapon|target|threat|range|veter|experien|promot|deploy|unload|repair|reload|enter|occup|best|fire|attack|damage|upgrade|rank|elite|score|kill|crate|heal',re.I)
L=['ENTRY\tSIZE\tGRADE\tDIRECT\tLIT\tNAME\tSEM']
cands=[]
for k,r in cov.items():
    if r['subsystem'].strip().upper()!='S10' or k not in atl:continue
    va=int(k,16)
    if r['grade'].strip()=='[已证]' or va in BAN:continue
    a=atl[k]
    try: sz=int(a.get('size','0'),0) if a.get('size') else 0
    except:sz=0
    if sz<=0 or sz>20000:sz=512
    b=R.read(va,min(sz,20000))
    ops=[]
    for ins in R.MD.disasm(b,va):
        if ins.mnemonic.startswith(('cmp','test')) or 'ret' in ins.mnemonic: ops.append(ins.op_str)
    blob=(r['name']+' '+r['one_line_semantics'])
    score=0
    if direct[va]:score+=3
    if lit[va]:score+=2
    if KEY.search(blob):score+=5
    # enum-like immediates near word/dword compares
    imm=[]
    for ins in R.MD.disasm(b,va):
        if ins.mnemonic in ('cmp','mov','push') and re.search(r'\b0x[0-9a-f]+',ins.op_str):
            for m in re.finditer(r'0x([0-9a-f]+)',ins.op_str):
                v=int(m.group(1),16)
                if 0<v<0x200: imm.append(v)
    if len(set(imm))>=3:score+=2
    if score>=5:cands.append((score,va,sz,len(direct[va]),len(lit[va]),r['name'],r['one_line_semantics']))
cands.sort(reverse=True)
for x in cands:L.append('\t'.join(str(v).replace('\t',' ') for v in x))
print('CAND',len(cands))
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/CANDIDATE_RAW.tsv'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
