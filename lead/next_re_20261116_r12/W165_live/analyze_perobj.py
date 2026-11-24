import json, statistics as st
rows=[json.loads(l) for l in open('EVIDENCE/ingame_cpu_120s.ndjson',encoding='utf-8')]
rows=[r for r in rows if r.get('cpu_ms') and r.get('frame') is not None]
t0=rows[0]['t']; W={}
for r in rows:
    W.setdefault(int((r['t']-t0)//10),[]).append(r)
data=[]
for k in sorted(W):
    c=W[k]
    df=c[-1]['frame']-c[0]['frame']; dt=(c[-1]['t']-c[0]['t'])*1000.0
    dcpu=c[-1]['cpu_ms']-c[0]['cpu_ms']
    if df<=0 or dt<=0: continue
    data.append(dict(cpu=dcpu/df, moving=st.median(x['moving'] for x in c),
                     objects=st.median(x['objects'] for x in c)))
print('%-6s %9s %8s %12s %12s' % ('#','cpu/frame','moving','cpu/moving','cpu/objects'))
per_mv=[]; per_ob=[]
for k,x in enumerate(data):
    pm=x['cpu']/x['moving'] if x['moving'] else None
    po=x['cpu']/x['objects'] if x['objects'] else None
    if pm: per_mv.append(pm)
    if po: per_ob.append(po)
    print('%-6d %9.3f %8.0f %12.4f %12.5f' % (k,x['cpu'],x['moving'],pm,po))
print()
print('  每"移动中对象"的 CPU: min %.4f  med %.4f  max %.4f  ms  （极差 %.4f）'
      % (min(per_mv),st.median(per_mv),max(per_mv),max(per_mv)-min(per_mv)))
print('  每"对象"的 CPU      : min %.5f  med %.5f  max %.5f  ms  （极差 %.5f）'
      % (min(per_ob),st.median(per_ob),max(per_ob),max(per_ob)-min(per_ob)))
print()
print('  ⇒ 变异系数（越小越"线性"）:')
for name,v in (('cpu/moving',per_mv),('cpu/objects',per_ob)):
    mu=st.mean(v); sd=st.pstdev(v)
    print('     %-12s mean %.5f  sd %.5f  CV %.3f' % (name,mu,sd,sd/mu if mu else 0))
# 线性拟合 cpu = a*moving + b
xs=[x['moving'] for x in data]; ys=[x['cpu'] for x in data]
n=len(xs); mx=sum(xs)/n; my=sum(ys)/n
a=sum((x-mx)*(y-my) for x,y in zip(xs,ys))/sum((x-mx)**2 for x in xs)
b=my-a*mx
res=[y-(a*x+b) for x,y in zip(xs,ys)]
rmse=(sum(r*r for r in res)/n)**0.5
print()
print('  拟合 cpu/frame ≈ %.4f × moving + %.4f   RMSE %.4f ms  (n=%d)' % (a,b,rmse,n))
