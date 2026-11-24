import os,re,csv,json
OUT=r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S20_KPROVED'
ROOT=r'D:\Project\ra2-campaign-forge'
SOURCES=[('docs_re',os.path.join(ROOT,'docs','re')),('re_atlas_kb',os.path.join(ROOT,'re_atlas','kb')),('ledger',os.path.join(ROOT,'lead','GOAL_THREE_TARGETS_20261018.md')),('r14_coverage',os.path.join(ROOT,'lead','next_re_20261117_r14','COVERAGE'))]
sel=[]
with open(os.path.join(OUT,'coverage_delta.tsv'),encoding='utf-8') as f:
    next(f)
    for line in f:
        if line.strip(): sel.append(line.split('\t')[0].upper())
pats={e:re.compile(r'(?<![0-9A-Fa-f])(?:0[xX])?'+e+r'(?![0-9A-Fa-f])',re.I) for e in sel}
files=[]
for label,p in SOURCES:
    if os.path.isfile(p): files.append((label,p))
    elif os.path.isdir(p):
        for dp,dn,fn in os.walk(p):
            for n in fn:
                if n.lower().endswith(('.md','.tsv','.txt','.json')): files.append((label,os.path.join(dp,n)))
rows=[]; per={e:0 for e in sel}
for label,p in files:
    try: text=open(p,encoding='utf-8',errors='replace').read()
    except Exception: continue
    lines=text.splitlines()
    for i,line in enumerate(lines,1):
        for e in sel:
            if pats[e].search(line):
                per[e]+=1
                if per[e]<=20:
                    rows.append((e,label,os.path.relpath(p,ROOT).replace('\\','/'),str(i),line[:500].replace('\t',' ')))
with open(os.path.join(OUT,'EVIDENCE','conflict_scan.tsv'),'w',encoding='utf-8',newline='') as f:
    w=csv.writer(f,delimiter='\t',lineterminator='\n'); w.writerow(['entry','source','path','line','matched_line']); w.writerows(rows)
summary=[]
for e in sel: summary.append('%s\t%d'%(e,per[e]))
open(os.path.join(OUT,'EVIDENCE','conflict_scan_summary.tsv'),'w',encoding='utf-8').write('entry\ttotal_hits\n'+'\n'.join(summary)+'\n')
print('FILES_SCANNED',len(files),'HIT_ROWS',len(rows),'ENTRIES_WITH_HITS',sum(1 for e in sel if per[e]))
for e in sel:
    if per[e]: print(e,per[e])
