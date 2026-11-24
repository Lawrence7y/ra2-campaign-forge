
import csv, hashlib, json, math, re, collections
from pathlib import Path
import pefile, capstone

ROOT = Path(r'D:\Project\ra2-campaign-forge')
EXE = ROOT/'ra2youli'/'gamemd.exe'
COV = ROOT/'lead/next_re_20261117_r14/COVERAGE/coverage.tsv'
ATLAS = ROOT/'lead/next_re_20261112_r10/W130_atlas/function_atlas.tsv'
OUT = ROOT/'lead/next_re_20261117_r14/SURVEY_RING24'

raw = EXE.read_bytes()
sha = hashlib.sha256(raw).hexdigest().upper()

lines = COV.read_text(encoding='utf-8-sig').splitlines()
hdr = lines[0].split(',')
FIELDS = hdr
cov=[]
for line in lines[1:]:
    if not line.strip(): continue
    q=line.split('\t'); q+=['']*(len(FIELDS)-len(q))
    cov.append(dict(zip(FIELDS,q[:len(FIELDS)])))

al = ATLAS.read_text(encoding='utf-8-sig').splitlines()
ah = al[0].split('\t')
atlas={}
for line in al[1:]:
    if not line.strip(): continue
    q=line.split('\t'); q+=['']*(len(ah)-len(q))
    r=dict(zip(ah,q[:len(ah)]))
    atlas[r['entry'].strip().upper().replace('0X','')]=r
print('atlas header', ah, 'rows', len(atlas))
print('cov rows', len(cov), 'grades', collections.Counter(r['grade'] for r in cov))

def norm(e): return e.strip().upper().replace('0X','')
def named_L(n):
    n=(n or '').strip(); return bool(n) and not n.upper().startswith('SUB_')
def named_S(n):
    if not named_L(n): return False
    u=n.strip().upper()
    return not re.search(r'::SUB_[0-9A-F]{8}$', u)
pat_slot=re.compile(r'::(?:V?SLOT)[0-9]+$', re.I)

metrics={}
for i in range(1,22):
    s=f'S{i:02d}'
    rs=[r for r in cov if r['subsystem'].strip().upper()==s and norm(r['entry']) in atlas]
    n=len(rs); proved=sum(r['grade'].strip()=='[已证]' for r in rs)
    static=sum(r['grade'].strip()=='[静态推断]' for r in rs)
    unproved=sum(r['grade'].strip()=='[未证]' for r in rs)
    metrics[s]=dict(n=n,proved=proved,static=static,unproved=unproved,
        named_L=sum(named_L(r['name']) for r in rs), named_S=sum(named_S(r['name']) for r in rs),
        threshold=math.ceil(n/2), gap=max(0,math.ceil(n/2)-proved))
tot_static=sum(v['static'] for v in metrics.values())
tot_gap=sum(v['gap'] for v in metrics.values())
print('total static(nonS22)', tot_static, 'total proved gap', tot_gap)
for s,v in metrics.items(): print(s, v)

# --- capstone scan
cs=capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32); cs.detail=True; cs.skipdata=True
pe=pefile.PE(data=raw, fast_load=True); ib=pe.OPTIONAL_HEADER.ImageBase
secs=[]
for s in pe.sections:
    nm=s.Name.rstrip(b'\0').decode('latin1')
    secs.append(dict(name=nm, va=ib+s.VirtualAddress, vs=s.Misc_VirtualSize, rs=s.SizeOfRawData, ptr=s.PointerToRawData))
txt=[s for s in secs if s['name']=='.text'][0]
code=raw[txt['ptr']:txt['ptr']+txt['vs']]
n_ins=0; n_e8=0
for ins in cs.disasm(code, txt['va']):
    n_ins+=1
    if ins.mnemonic=='call' and ins.size==5 and ins.bytes[0]==0xE8: n_e8+=1
print('text VirtualSize', txt['vs'], 'instructions', n_ins, 'E8@boundary', n_e8)

res=dict(sha256=sha, expected='73201CC021497C9567742F718BF1DC78C22E9AE16C7E7365354B65F3FCF67476',
  cov_rows=len(cov), atlas_rows=len(atlas), metrics=metrics, tot_static=tot_static, tot_gap=tot_gap,
  text_vsize=txt['vs'], instructions=n_ins, e8=n_e8,
  capstone=capstone.__version__, pefile=pefile.__version__)
(OUT/'work'/'step0.json').write_text(json.dumps(res,ensure_ascii=False,indent=2),encoding='utf-8')
