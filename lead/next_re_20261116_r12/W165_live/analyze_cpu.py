import json, statistics as st
rows=[json.loads(l) for l in open('EVIDENCE/ingame_cpu_120s.ndjson',encoding='utf-8')]
rows=[r for r in rows if r.get('cpu_ms') and r.get('frame') is not None]
print('samples =', len(rows))
def windows(ws=10.0):
    t0=rows[0]['t']; out=[]; i=0; n=len(rows)
    while i<n:
        j=i; base=rows[i]['t']
        while j<n and rows[j]['t']-base<ws: j+=1
        c=rows[i:j]; i=j if j>i else i+1
        if len(c)<10: continue
        df=c[-1]['frame']-c[0]['frame']
        dt=(c[-1]['t']-c[0]['t'])*1000.0
        dcpu=c[-1]['cpu_ms']-c[0]['cpu_ms']
        if df<=0 or dt<=0: continue
        out.append(dict(ms=dt/df, cpu=dcpu/df, duty=dcpu/dt,
            objects=st.median(x['objects'] for x in c),
            lc=st.median(x['lc_count'] for x in c),
            loco=st.median(x['with_loco'] for x in c),
            tgt=st.median(x['has_target'] for x in c),
            moving=st.median(x['moving'] for x in c)))
    return out
w=windows()
print('windows =', len(w))
print('%-4s %9s %9s %8s %8s %6s %6s %6s %6s' % ('#','ms/frame','cpu/frame','duty','objects','lc','loco','tgt','moving'))
for k,x in enumerate(w):
    print('%-4d %9.3f %9.3f %8.4f %8.0f %6.0f %6.0f %6.0f %6.0f' % (
        k,x['ms'],x['cpu'],x['duty'],x['objects'],x['lc'],x['loco'],x['tgt'],x['moving']))
def corr(a,b):
    n=len(a)
    if n<3: return float('nan')
    ma=sum(a)/n; mb=sum(b)/n
    num=sum((x-ma)*(y-mb) for x,y in zip(a,b))
    den=(sum((x-ma)**2 for x in a)*sum((y-mb)**2 for y in b))**0.5
    return num/den if den else float('nan')
print()
cpu=[x['cpu'] for x in w]; ms=[x['ms'] for x in w]
print('  cpu/frame: min %.3f med %.3f max %.3f  (range %.3f ms)' % (min(cpu),st.median(cpu),max(cpu),max(cpu)-min(cpu)))
print('  ms/frame : min %.3f med %.3f max %.3f  (range %.3f ms)' % (min(ms),st.median(ms),max(ms),max(ms)-min(ms)))
for key in ('objects','lc','loco','tgt','moving'):
    v=[x[key] for x in w]
    print('  r(cpu, %-7s) = %+.4f   r(ms, %-7s) = %+.4f   (distinct %d)' % (key,corr(cpu,v),key,corr(ms,v),len(set(v))))
