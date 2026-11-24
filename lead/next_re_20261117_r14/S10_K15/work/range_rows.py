import sys
sys.path.insert(0,r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S10_K15\work")
import common
rows,cov,atl=common.load_rows()
lo,hi=0x70D900,0x70E200
print('ATLAS')
for k,r in sorted(atl.items()):
 if k=='entry': continue
 a=int(k,16)
 if lo<=a<hi: print(k,r[1],r[2])
print('\nCOV')
for r in rows:
 if r[0].startswith('entry'): continue
 a=int(r[0],16)
 if lo<=a<hi: print('\t'.join(r[:5]))
