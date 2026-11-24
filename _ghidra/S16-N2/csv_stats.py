
import csv,sys,json
p=sys.argv[1]
rows=list(csv.reader(open(p,encoding='utf-8-sig',newline='')))
hdr=rows[0]; print('HDR',hdr)
s16=[r for r in rows[1:] if len(r)>4 and r[1].strip().upper()=='S16']
print('S16 coverage rows',len(s16))
from collections import Counter
print('grades',Counter(r[4].strip() for r in s16))
def nm(r): return r[2].strip()
print('named_L',sum(1 for r in s16 if nm(r) and not nm(r).lower().startswith('sub_')))
print('named_S',sum(1 for r in s16 if nm(r) and not nm(r).lower().startswith('sub_') and '::sub_' not in nm(r)))
print('sub_',sum(1 for r in s16 if nm(r).lower().startswith('sub_')))
# list named so we can see N1 merged?
print('N1 check:')
for a in ['00539EB0','0053AE00','0053B410','0053A0E0','0053AE50','006CE2C0','006CE270','006CE280']:
 for r in s16:
  if r[0].upper()==a: print(' ',a,r[2],r[4].strip())
