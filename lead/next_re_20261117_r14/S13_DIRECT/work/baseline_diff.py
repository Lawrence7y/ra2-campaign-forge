import sys,io,struct,pefile,random,json,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
EXE=r'D:\Project\ra2-campaign-forge\ra2youli\gamemd.exe'
ATL=r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
COV=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
raw=open(EXE,'rb').read()
pe=pefile.PE(EXE)
sec=[s for s in pe.sections if s.Name.rstrip(b'\x00')==b'.text'][0]
base=pe.OPTIONAL_HEADER.ImageBase+sec.VirtualAddress
vsize=sec.Misc_VirtualSize
code=raw[sec.PointerToRawData:sec.PointerToRawData+vsize]

# load strong direct-call index (boundary-verified) from EVIDENCE
strong_targets=set()
idx={}
for ln in open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\all_direct_call_sites.tsv',encoding='utf-8').read().split(chr(10))[1:]:
    if not ln.strip(): continue
    p=ln.split()
    idx.setdefault(p[1],[]).append(p[0])
    strong_targets.add(p[1])

# WEAK: raw E8 byte scan (every byte position, no boundary requirement)
weak_targets=set()
weak_hits=collections.defaultdict(list)
for i in range(len(code)-4):
    if code[i]==0xE8:
        rel=struct.unpack('<i',code[i+1:i+5])[0]
        target=base+i+5+rel
        weak_targets.add('%08X'%target)
        weak_hits['%08X'%target].append(base+i)
print('WEAK distinct targets',len(weak_targets),'STRONG distinct targets',len(strong_targets))

# 129 static entries
static=[]
d=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\direct_analysis.json',encoding='utf-8'))
for x in d['results']: static.append(x['entry'])
print('static entries',len(static))
nweak=sum(1 for e in static if e in weak_hits)
nstrong=sum(1 for e in static if e in strong_targets)
print('static rows with WEAK raw E8 target:',nweak,'with STRONG boundary E8 target:',nstrong,'diff',nweak-nstrong)
for e in static:
    if e in weak_hits: print(' WEAK-ONLY',e,'nsites',len(weak_hits[e]))

# baseline: random 129 entries from atlas, count direct-call hits (strong)
atls=[]
for ln in open(ATL,encoding='utf-8',errors='replace').read().split(chr(10))[1:]:
    p=ln.split()
    if len(p)>=2: atls.append(p[0].upper())
print('atlas entries',len(atls))
random.seed(20261118)
counts=[]
for seed in [20261118,7,99,424242,20260101,1337,271828,161803,314159,42]:
    random.seed(seed)
    samp=random.sample(atls,129)
    c=sum(1 for e in samp if e in strong_targets)
    counts.append(c)
print('RANDOM baseline (129 atlas entries, strong direct criterion) 10 seeds:',counts,'mean=%.2f'%(sum(counts)/len(counts)))
# also baseline from all S13 [静态推断] equivalent pool: all coverage static rows across subsystems
cov_static=[]
for ln in open(COV,encoding='utf-8',errors='replace').read().split(chr(10))[1:]:
    p=ln.split(chr(9))
    if len(p)>=8 and p[4].strip()=='[静态推断]' and p[0].upper() in set(atls): cov_static.append(p[0].upper())
print('coverage static-in-atlas pool',len(cov_static))
counts2=[]
for seed in [20261118,7,99,424242,20260101]:
    random.seed(seed)
    samp=random.sample(cov_static,min(129,len(cov_static)))
    c=sum(1 for e in samp if e in strong_targets)
    counts2.append(c)
print('RANDOM baseline (129 coverage-static entries) 5 seeds:',counts2,'mean=%.2f'%(sum(counts2)/len(counts2)))
