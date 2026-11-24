import sys,csv,os,re
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
terms=sys.argv[1:]
for term in terms:
 print('\n###',term)
 hits=[r for r in rows if len(r)>=5 and term.lower() in r[2].lower()]
 for r in hits[:80]: print('\t'.join(r[:5]))
 print('count',len(hits))
