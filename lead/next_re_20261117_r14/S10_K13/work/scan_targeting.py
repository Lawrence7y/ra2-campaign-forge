import sys,csv,collections,re,bisect,hashlib
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
# literal occurrences of 4-byte values anywhere in .text for target enumeration
for t in direct:
    pat=t.to_bytes(4,'little');pos=0
    while True:
        i=data.find(pat,pos)
        if i<0:break
        lit[t].append(base+i);pos=i+1
# S10 candidate intervals by atlas sizes
cands=[]
for k,r in cov.items():
    if r['subsystem'].strip().upper()!='S10' or k not in atl:continue
    va=int(k,16)
    if r['grade'].strip()=='[已证]' or va in BAN:continue
    a=atl[k]
    try:sz=int(a.get('size','0'),0) if a.get('size') else 0
    except:sz=0
    if sz<=0 or sz>20000:sz=512
    cands.append((va,va+sz,r['name'],r['one_line_semantics'],k,sz))
cands.sort(); starts=[x[0] for x in cands]
def owner(site):
    i=bisect.bisect_right(starts,site)-1
    if i>=0 and site<cands[i][1]:return cands[i]
    return None
words=['target','threat','weapon','ammo','range','fire','attack','best','veter','experien','promot','upgrade','rank','elite','damage']
# collect important proved callees by keyword in name/sem
proved={}
for k,r in cov.items():
    if r['grade'].strip()=='[已证]':
        blob=(r['name']+' '+r['one_line_semantics']).lower()
        if any(w in blob for w in words):proved[int(k,16)]=r
L=['OWNER\tOWNER_NAME\tSCORE\tN_DIRECT\tN_LIT\tN_PROVED_SEM\tPROVED_CALLS\tDIRECT_CALLS']
for va,end,nm,sem,key,sz in cands:
    p=[]
    for t,sites in direct.items():
        if t in proved:
            for s in sites:
                if va<=s<end:p.append((s,t,proved[t]['name']))
    d=[]
    for t,sites in direct.items():
        for s in sites:
            if va<=s<end:d.append((s,t))
    li=lit.get(va,[])
    # byte reads/writes of own fields: count mov [ebp+off]/[esi+off]/[ecx+off]
    b=R.read(va,min(sz,10000)); txt='\n'.join(f'{i.mnemonic} {i.op_str}' for i in R.MD.disasm(b,va))
    own=set()
    for m in re.finditer(r'(?:mov|cmp|add|sub|inc|dec)\s+(?:byte|word|dword ptr )?\[(?:ebp|esi|edi|ebx)\s*\+\s*(0x[0-9a-f]+)\]',txt,re.I): own.add(int(m.group(1),16))
    score=len(p)*3+len(d)+min(len(li),10)+len(own)*0.2
    if score>=6:
        L.append('\t'.join([key,nm,f'{score:.1f}',str(len(d)),str(len(li)),str(len(p)),';'.join(f'{s:08X}:{t:08X}:{tn}' for s,t,tn in sorted(p)[:12]),';'.join(f'{s:08X}:{t:08X}' for s,t in sorted(d)[:12])]))
L[1:]=sorted(L[1:],key=lambda x:float(x.split('\t')[2]),reverse=True)
print('ROWS',len(L)-1)
out=ROOT/'lead/next_re_20261117_r14/S10_K13/EVIDENCE/TARGETING_SCAN.tsv'
Path(out).write_text('\n'.join(L)+'\n','utf-8',newline='\n')
