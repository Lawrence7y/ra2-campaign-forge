"""Compute final stats from coverage_delta.tsv -> EVIDENCE/final_stats.txt (UTF-8)."""
import os, collections, json
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.abspath(os.path.join(HERE,'..')); EVID=os.path.join(BASE,'EVIDENCE')
TAB=chr(9)
rows=[]
for ln in open(os.path.join(BASE,'coverage_delta.tsv'),encoding='utf-8').read().splitlines()[1:]:
    p=ln.split(TAB)
    rows.append(p)
res=json.load(open(os.path.join(EVID,'classification_results.json'),encoding='utf-8'))
by_sub=collections.Counter(r[1] for r in rows)
by_grade=collections.Counter(r[4] for r in rows)
by_conf=collections.Counter(r['conf'] for r in res)
hi=by_grade.get('[已证]',0)
lines=[]
lines.append('total_rows=%d'%len(rows))
lines.append('unique_entries=%d'%len(set(r[0] for r in rows)))
lines.append('high_pct=%.4f'%(hi/len(rows)))
lines.append('by_grade='+repr(dict(by_grade)))
lines.append('by_conf='+repr(dict(by_conf)))
lines.append('by_subsystem='+repr(dict(sorted(by_sub.items()))))
lines.append('unclassifiable_low=%d'%by_conf.get('low',0))
lines.append('atlas_gaps_rows=%d'%(len(open(os.path.join(BASE,'atlas_gaps.tsv'),encoding='utf-8').read().splitlines())-1))
out='\n'.join(lines)
open(os.path.join(EVID,'final_stats.txt'),'w',encoding='utf-8').write(out)
print(out)
