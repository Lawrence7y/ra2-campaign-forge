#!/usr/bin/env python3
# Random baseline for direct criterion + 18 name-conflict analysis (report-only).
import os,sys,io,json,random,re
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
ROOT=r"D:\Project\ra2-campaign-forge"
OUT=os.path.join(ROOT,"lead","next_re_20261117_r14","S20_DIRECT")
WK=os.path.join(OUT,"work"); EV=os.path.join(OUT,"EVIDENCE")
COV=os.path.join(ROOT,"lead","next_re_20261117_r14","COVERAGE","coverage.tsv")
ATLAS=os.path.join(ROOT,"lead","next_re_20261112_r10","W130_atlas","function_atlas.tsv")
TEXT_VA=0x401000; TEXT_SIZE=0x3E0000

# target set: all distinct addresses targeted by a valid direct E8 call
targets=set()
for l in open(os.path.join(WK,'all_direct_call_sites.tsv'),encoding='utf-8').read().splitlines()[1:]:
    f=l.split('\t'); targets.add(int(f[2],16))
print('distinct direct-call targets:',len(targets),'of',68253,'calls')
# also how many of those targets are 4-byte aligned
print('target aligned4:',sum(1 for t in targets if t%4==0))

N=11
res={}
for seed in range(10):
    rng=random.Random(seed)
    samp=[TEXT_VA+rng.randrange(TEXT_SIZE) for _ in range(N)]
    hits=[s for s in samp if s in targets]
    res[seed]=len(hits)
vals=list(res.values())
print('random baseline false-hits among N=11 per seed (10 seeds):',vals,'mean=',sum(vals)/len(vals))

# baseline variant: sample only 4-aligned addresses (fairer to real entries which are aligned)
res2={}
for seed in range(10):
    rng=random.Random(100+seed)
    samp=[TEXT_VA+(rng.randrange(TEXT_SIZE//4)*4) for _ in range(N)]
    res2[seed]=sum(1 for s in samp if s in targets)
vals2=list(res2.values())
print('random aligned4 baseline N=11:',vals2,'mean=',sum(vals2)/len(vals2))

# 18 genuine name conflicts: collect all coverage rows (all subsystems) + atlas-derived names
entries=['004C54E0','0062DF20','0062E070','0062F230','0070F1D0','0070FD70','00739AC0','00739CD0','0075E950','007610F0','007C978A']
cov_by_entry={}
for l in open(COV,encoding='utf-8').read().splitlines()[1:]:
    if not l.strip():continue
    f=l.split('\t'); a=f[0].upper()
    cov_by_entry.setdefault(a,[]).append(dict(sub=f[1],name=f[2],sem=f[3],grade=f[4]))
cnf={}
for a in entries:
    rows=cov_by_entry.get(a,[])
    names=sorted(set(r['name'] for r in rows))
    cnf[a]=dict(rows=rows,names=names)
    print(a,'coverage names(all sub):',names,'n_rows=',len(rows))

# scan docs/re + re_atlas/kb + COVERAGE for DEFINITE naming lines near the address
# (line that both contains address and a name-like token), report as text
roots=[os.path.join(ROOT,'docs','re'),os.path.join(ROOT,'re_atlas','kb'),
       os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE')]
rgxmap={a:re.compile(r'(?i)(?<![0-9A-F])0?x?'+re.escape(a.lower())+r'(?![0-9A-F])') for a in entries}
namehit={a:[] for a in entries}
for r in roots:
    if not os.path.isdir(r):continue
    for dp,dn,fn in os.walk(r):
        for n in fn:
            if not n.lower().endswith(('.md','.tsv','.txt','.json')):continue
            p=os.path.join(dp,n)
            try:txt=open(p,encoding='utf-8',errors='ignore').read().splitlines()
            except:continue
            for i,l in enumerate(txt,1):
                low=l.lower()
                for a in entries:
                    if rgxmap[a].search(low):
                        # keep only lines that look like a naming/assignment (:: or name= or class)
                        if '::' in l or 'name' in low or 'class' in low or '|' in l:
                            namehit[a].append(p.replace(ROOT+os.sep,'')+':'+str(i)+':'+l[:180])
for a in entries:
    print('\n18 NAME-CANDIDATE lines for',a,':',len(namehit[a]))
    for x in namehit[a][:6]:print('   ',x)

json.dump(dict(distinct_targets=len(targets),baseline_random=res,baseline_aligned=res2,
               baseline_mean=sum(vals)/len(vals),baseline_aligned_mean=sum(vals2)/len(vals2),
               cov_by_entry=cnf,namehit=namehit),
          open(os.path.join(EV,'baseline_and_conflicts.json'),'w',encoding='utf-8'),indent=2,ensure_ascii=False)
print('\nwrote baseline_and_conflicts.json')
