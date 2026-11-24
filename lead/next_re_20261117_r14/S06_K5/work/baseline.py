
import sys,csv,collections,re,hashlib
sys.stdout.reconfigure(encoding='utf-8')
import k5_lib as K
def rows(p): return list(csv.DictReader(open(p,encoding='utf-8',newline=''),delimiter='\t'))
cov=rows(K.COV); atl_rows=rows(K.ATL)
s06=[r for r in cov if r['subsystem'].strip().upper()=='S06']
covmap={K.norm(r['entry']):r for r in s06}
atlset={K.norm(r['entry']) for r in atl_rows}
inter=sorted(set(covmap)&atlset)
grades=collections.Counter(covmap[e]['grade'].strip() for e in inter)
namedL=sum(1 for e in inter if covmap[e]['name'].strip() and not covmap[e]['name'].strip().startswith('sub_'))
proved=grades['[已证]']
thr=(len(inter)+1)//2
print("SHA256="+K.SHA)
print("S06_ROWS=%d  DENOM(coverage∩atlas,case-unified)=%d"%(len(s06),len(inter)))
print("GRADES_ON_DISK=",dict(grades))
print("PROVED_ON_DISK=%d  NAMED_L=%d  PCT=%.4f%%  THRESHOLD_50PCT=%d"%(proved,namedL,100.0*proved/len(inter),thr))
# K4 delta merge (without writing)
k4d=K.R/'lead/next_re_20261117_r14/S06_K4/coverage_delta.tsv'
delta=[r for r in csv.reader(open(k4d,encoding='utf-8',newline=''),delimiter='\t') if len(r)>=6]
k4_entries={K.norm(r[0]) for r in delta}
newly=[e for e in k4_entries if e in covmap and covmap[e]['grade'].strip()!='[已证]']
merged=proved+len(newly)
print("K4_DELTA_ROWS=%d  K4_NEWLIES_POSSIBLE=%d  PROVED_AFTER_K4_MERGE=%d  PCT=%.4f%%"%(len(delta),len(newly),merged,100.0*merged/len(inter)))
# my K5 delta (to be written) - report expected
print("CARD_EXPECTED: denom=848 proved=103 threshold=424; K4 delta=23 -> 126 (14.8585%)")
