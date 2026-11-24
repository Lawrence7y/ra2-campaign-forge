import sys,io,json,collections
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
d=json.load(open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S13_DIRECT\EVIDENCE\direct_analysis.json',encoding='utf-8'))
r=d['results']
print('n_sites dist:',dict(collections.Counter(x['n_sites'] for x in r)))
print('rows with n_sites>0:',sum(1 for x in r if x['n_sites']>0))
for x in r:
    if x['n_sites']>0: print(x['entry'],x['name'],'n_sites',x['n_sites'],'selfskip',len(x['self_skipped']))
