import json, statistics as st
def windows(path, ws=5.0):
    rows=[json.loads(l) for l in open(path,encoding='utf-8')]
    rows=[r for r in rows if r.get('frame') is not None]
    t0=rows[0]['t']; out=[]; i=0; n=len(rows)
    while i<n:
        j=i; base=rows[i]['t']
        while j<n and rows[j]['t']-base<ws: j+=1
        c=rows[i:j]; i=j if j>i else i+1
        if len(c)<10: continue
        df=c[-1]['frame']-c[0]['frame']
        dt=(c[-1]['t']-c[0]['t'])*1000.0
        if df<=0: continue
        out.append(dict(ms=dt/df,
            objects=st.median(x['objects'] for x in c),
            lc=st.median(x['lc_count'] for x in c),
            loco=st.median(x['with_loco'] for x in c),
            tgt=st.median(x['has_target'] for x in c),
            moving=st.median(x['moving'] for x in c),
            mv_max=max(x['moving'] for x in c)))
    return out
def corr(a,b):
    n=len(a)
    if n<3: return float('nan')
    ma=sum(a)/n; mb=sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**0.5
    return num/den if den else float('nan')
for path in ('EVIDENCE/ingame_90s.ndjson','EVIDENCE/ingame_150s.ndjson'):
    w=windows(path)
    print('=== %s : %d windows (5s) ===' % (path, len(w)))
    print('%-5s %9s %8s %6s %6s %6s %6s %7s' % ('#','ms/frame','objects','lc','loco','tgt','moving','mv_max'))
    for k,x in enumerate(w):
        print('%-5d %9.3f %8.0f %6.0f %6.0f %6.0f %6.0f %7.0f' % (k,x['ms'],x['objects'],x['lc'],x['loco'],x['tgt'],x['moving'],x['mv_max']))
    ms=[x['ms'] for x in w]
    print('  ms/frame: min %.3f med %.3f max %.3f  (range %.3f)' % (min(ms),st.median(ms),max(ms),max(ms)-min(ms)))
    for key in ('objects','lc','loco','tgt','moving','mv_max'):
        v=[x[key] for x in w]
        print('  r(ms, %-7s) = %+.4f   (distinct %d)' % (key, corr(ms,v), len(set(v))))
    print()
