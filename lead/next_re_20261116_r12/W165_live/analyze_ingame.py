import json, statistics as st
rows=[json.loads(l) for l in open('EVIDENCE/ingame_90s.ndjson',encoding='utf-8')]
# 10 秒窗
t0=rows[0]['t']
win={}
for r in rows:
    w=int((r['t']-t0)//10)
    win.setdefault(w,[]).append(r)
print('%-4s %6s %8s %8s %8s %8s %8s %8s' % ('win','n','dframe','ms/frame','objects','lc','loco','moving'))
data=[]
for w in sorted(win):
    c=win[w]
    df=c[-1]['frame']-c[0]['frame']
    dt=(c[-1]['t']-c[0]['t'])*1000.0
    if df<=0: continue
    ms=dt/df
    row=dict(win=w, ms=ms,
             objects=st.median(x['objects'] for x in c),
             lc=st.median(x['lc_count'] for x in c),
             loco=st.median(x['with_loco'] for x in c),
             moving=st.median(x['moving'] for x in c))
    data.append(row)
    print('%-4d %6d %8d %8.3f %8.0f %8.0f %8.0f %8.0f' % (w,len(c),df,ms,row['objects'],row['lc'],row['loco'],row['moving']))
print()
def corr(a,b):
    n=len(a); ma=sum(a)/n; mb=sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**0.5
    return num/den if den else float('nan')
if len(data)>=3:
    ms=[d['ms'] for d in data]
    for key in ('objects','lc','loco','moving'):
        v=[d[key] for d in data]
        print('  r(ms, %-8s) = %+.4f   (n=%d, 取值集合 %s)' % (key, corr(ms,v), len(v), sorted(set(v))))
