import os, csv, json, random, collections
ROOT='.'
M='lead/next_re_20261117_r14/R17_R101_TIER_FINAL_4417/tier_final_4417.tsv'
S='lead/next_re_20261117_r14/R17_R72_T1_CLEANSCALE/files_tier_A_snap2.tsv'
F4413='lead/next_re_20261117_r14/R17_R96_TIER_FINAL_4413/tier_final_4413.tsv'
A2='lead/next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'
out={}
with open(M,encoding='utf-8') as f:
    rdr=csv.reader(f,delimiter='\t'); hdr=next(rdr); rows=[r for r in rdr]
out['A0_header']=hdr
out['A1']={'n':len(rows),'sum_bytes':sum(int(r[1]) for r in rows),
          'nf_dist':dict(collections.Counter(len(r) for r in rows))}
# A2 buckets with base lead/
b=collections.Counter(); bl=collections.Counter(); diffs=[]
for rel,bs,src,why in rows:
    p=os.path.join('lead',rel)
    try:
        sz=os.stat(p).st_size
        if sz==int(bs): b['same']+=1; bl['same']+=int(bs)
        else: b['diff']+=1; diffs.append({'rel':rel,'listed':int(bs),'current':sz})
    except FileNotFoundError: b['enoent']+=1; bl['enoent']+=int(bs)
    except Exception as e: b['other:'+type(e).__name__]+=1
out['A2']={'buckets':dict(b),'listed_bytes':dict(bl),'diff_detail':diffs}
out['A2_sumcheck']={'n':sum(b.values()),'bytes':sum(bl.values())+sum(d['current'] for d in diffs)}
# A2 root controls: manifest-external existing files
ctrls=['next_re_20261117_r14/R14_COMMON.md','next_re_20261117_r14/COMPACT_STATE.md',
       'next_re_20261117_r14/DISC_ESTABLISH.tsv',
       'next_re_20261117_r14/R17_R102_FACTINDEX_V530/FACT_INDEX.tsv',
       'next_re_20261117_r14/R17_R72_T1_CLEANSCALE/REPORT.md']
inman=set(r[0] for r in rows)
ctl=[]
for rel in ctrls:
    p=os.path.join('lead',rel)
    ctl.append({'rel':rel,'in_manifest':rel in inman,
                'lead_hit':os.path.exists(p),
                'lead_bytes':os.stat(p).st_size if os.path.exists(p) else None,
                'root_hit':os.path.exists(rel),
                'r14_hit':os.path.exists(os.path.join('lead/next_re_20261117_r14',rel))})
out['A2_controls']=ctl
# A3
d=json.load(open(A2,encoding='utf-8'))
sj=json.dumps(d['bounds']); sjc=json.dumps(d['bounds'],separators=(',',':'))
out['A3']={'stat':os.stat(A2).st_size,
           'keys':{k:type(v).__name__ for k,v in d.items()},
           'bounds_n':len(d['bounds']),'calls_n':len(d['calls']),
           'bounds_dumps_len':len(sj),'bounds_dumps_compact_len':len(sjc),
           'calls_dumps_len':len(json.dumps(d['calls'])),
           'listed':[int(r[1]) for r in rows if r[0]=='next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'],
           'delta':os.stat(A2).st_size-[int(r[1]) for r in rows if r[0]=='next_re_20261117_r14/D41_SUBST/_audit/EVIDENCE/a2_sites.json'][0]}
# A4 sample 30 missing from snapshot col3
snap={}
with open(S,encoding='utf-8') as f:
    rdr=csv.reader(f,delimiter='\t'); sh=next(rdr)
    for r in rdr: snap[r[0]]=r[2]
out['A0_snap_header']=sh
miss=[r[0] for r in rows if not os.path.exists(os.path.join('lead',r[0]))]
random.seed(136)
pick=random.sample(miss,30)
sm=[{'rel':p,'in_snap':p in snap,'snap_bytes':snap.get(p),'manifest_bytes':[int(r[1]) for r in rows if r[0]==p][0]} for p in pick]
for x in sm: x['match']= x['in_snap'] and str(x['snap_bytes'])==str(x['manifest_bytes'])
out['A4']={'missing_n':len(miss),'sample_n':len(pick),
           'hits':sum(1 for x in sm if x['match']),'sample':sm}
# A5
with open(F4413,encoding='utf-8') as f:
    rdr=csv.reader(f,delimiter='\t'); h4413=next(rdr); rows4413=[r for r in rdr]
out['A0_4413_header']=h4413
b627=[r for r in rows if r[2]=='rejudge_R53_对象抄本']
out['A5']={'manifest_627_n':len(b627),'manifest_627_bytes':sum(int(r[1]) for r in b627),
           'f24_claimed_627_bytes':29944200,
           'claimed_minus_manifest':29944200-sum(int(r[1]) for r in b627),
           'bounds_delta':16711118,
           'f4413_rows':len(rows4413),'f4413_sum':sum(int(r[1]) for r in rows4413),
           'f4413_rejudge_n':sum(1 for r in rows4413 if any('rejudge' in c or '对象抄本' in c for c in r)),
           'f4413_rejudge_bytes':sum(int(r[1]) for r in rows4413 if any('rejudge' in c or '对象抄本' in c for c in r))}
print(json.dumps(out,ensure_ascii=False,indent=1))
