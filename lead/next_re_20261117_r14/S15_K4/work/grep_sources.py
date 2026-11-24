#!/usr/bin/env python3
import pathlib,re,sys
ROOT=pathlib.Path(r'D:\Project\ra2-campaign-forge')
TARGETS=['006D0F00','006D6070','006E1830','006E2A10','006E2AA0','006E4790','006E47C0','006E6310','006EA3E0','006F1920','0070F120','0071FA30','00721270','00726910','00727AA0','0072DDB0','0072DEF0','00751590','00752460','00763610','00763690']
pats={t:re.compile(r'(?:0x)?0*'+t[2:],re.I) for t in TARGETS}
kw=re.compile(r'FindByNameOrCreate|FindOrCreate|FindByNameOrID|CreateOrFind|FindOrAdd',re.I)
root=pathlib.Path(sys.argv[1]) if len(sys.argv)>1 else ROOT
maxhits=int(sys.argv[2]) if len(sys.argv)>2 else 40
hits={t:[] for t in TARGETS}; kh=[]
for p in root.rglob('*'):
    if not p.is_file(): continue
    if any(x in p.parts for x in ('.git','_ghidra','_ghidra_proj')): continue
    if p.suffix.lower() not in {'.md','.txt','.tsv','.h','.hpp','.cpp','.c','.py','.json','.log','.out','.ini'}: continue
    try:
        if p.stat().st_size>20_000_000: continue
        with p.open('r',encoding='utf-8',errors='replace') as f:
            for ln,line in enumerate(f,1):
                for t,rex in pats.items():
                    if rex.search(line) and len(hits[t])<maxhits: hits[t].append((str(p.relative_to(ROOT)),ln,line.rstrip()[:220]))
                if kw.search(line) and len(kh)<300: kh.append((str(p.relative_to(ROOT)),ln,line.rstrip()[:220]))
    except Exception: pass
for t in TARGETS:
    print('\n== %s hits=%d'%(t,len(hits[t])))
    for x in hits[t][:12]: print('%s:%d: %s'%x)
print('\n== keyword hits=%d'%len(kh))
for x in kh[:120]: print('%s:%d: %s'%x)
