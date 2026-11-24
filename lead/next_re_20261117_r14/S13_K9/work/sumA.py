import json
from collections import Counter
hits=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_K9\EVIDENCE\channelA_exact.json'))
print('total exact hits',len(hits),'contig',sum(1 for h in hits if h['pattern']=='contig'))
c=Counter(h['vptr'] for h in hits)
print('distinct vptrs',len(c))
for vp,n in c.most_common(50): print(vp,n)
