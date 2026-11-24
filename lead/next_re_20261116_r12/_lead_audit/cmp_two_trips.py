import json, statistics as st
FILES={
 "range1":  r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\_archive_range1\trip_range1_r1\run.ndjson",
 "c2_near": r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W110_crash\out\_archive_c2\trip_c2_near_r1\run.ndjson",
}
def wins(path, ws=10.0, mn=30, mx=200.0):
    rows=[]
    with open(path,encoding='utf-8',errors='replace') as f:
        for line in f:
            if '"sample"' not in line: continue
            try: o=json.loads(line)
            except: continue
            if o.get('kind')!='sample' or o.get('read_status')!='ok': continue
            t=o.get('t_perf_ns') or o.get('t_mono_ns')
            if t is None:
                ts=o.get('t_monotonic'); t=int(round(float(ts)*1e9)) if ts is not None else None
            if t is None: continue
            rows.append((int(t),o.get('frame'),o.get('A8ED50'),o.get('win_cpu_ms')))
    rows.sort(key=lambda r:r[0])
    if not rows: return []
    t0=rows[0][0]; span=ws*1e9; out=[]; i=0; n=len(rows)
    while i<n:
        j=i; base=rows[i][0]
        while j<n and rows[j][0]-base<span: j+=1
        c=rows[i:j]; i=j if j>i else i+1
        if len(c)<mn: continue
        df=c[-1][1]-c[0][1]
        if df<=0: continue
        dt=(c[-1][0]-c[0][0])/1e6
        ms=dt/df
        if ms>mx: continue
        cpu=(c[-1][3]-c[0][3]) if (c[-1][3] is not None and c[0][3] is not None) else None
        out.append(dict(idx=int(round((c[0][0]-t0)/span)), ms=ms, b=st.mean(x[2] for x in c),
                        cpu=(cpu/df if cpu else None), n=len(c)))
    return out
print('%-9s %4s %8s %8s %10s %10s' % ('trip','win','b_mean','wall','cpu/f','duty'))
for label,p in FILES.items():
    w=wins(p)
    tot_b=max((x['b'] for x in w), default=0)
    for x in w[:6]:
        duty = (x['cpu']/x['ms']) if x['cpu'] else None
        print('%-9s %4d %8.2f %8.2f %10s %10s' % (label, x['idx'], x['b'], x['ms'],
            ('%.2f'%x['cpu']) if x['cpu'] else '-', ('%.4f'%duty) if duty else '-'))
    print('   -> 峰 b_mean=%.1f  n_win=%d' % (tot_b, len(w)))
    print()
