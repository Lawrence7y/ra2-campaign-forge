import json, os, glob
from collections import defaultdict
ROOT="D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files=sorted(glob.glob(os.path.join(ROOT,"**","measure_w*.json"),recursive=True))
def load(fp): return json.load(open(fp,encoding='utf-8'))
def rank(xs):
    idx=sorted(range(len(xs)),key=lambda i:xs[i]); r=[0.0]*len(xs); i=0
    while i<len(idx):
        j=i
        while j+1<len(idx) and xs[idx[j+1]]==xs[idx[i]]: j+=1
        avg=(i+j)/2.0+1
        for k in range(i,j+1): r[idx[k]]=avg
        i=j+1
    return r
def spear(xs,ys):
    if len(xs)<3: return None,len(xs)
    rx,ry=rank(xs),rank(ys); n=len(xs); mx=sum(rx)/n; my=sum(ry)/n
    cov=sum((a-mx)*(b-my) for a,b in zip(rx,ry)); vx=sum((a-mx)**2 for a in rx); vy=sum((b-my)**2 for b in ry)
    return (cov/(vx**0.5*vy**0.5) if vx and vy else None),n

# Build computable rows using verifier's live convention: numerator over frame_edges, denom first->last EDGE
rows=[]
for fp in files:
    d=load(fp); st=d["stats"]; g=d.get("gate") or {}; t=d["samples"]["t"]
    ej=d.get("frame_edges") or []
    if st.get("fps_avg") is None or len(ej)<2: continue
    live_s=ej[-1][1]-ej[0][1]
    if live_s<=0: continue
    live=(ej[-1][0]-ej[0][0])/live_s
    rows.append(dict(name=os.path.relpath(fp,ROOT).replace("\\","/"),trip=d["trip_id"],win=d["window"],
        pre=g.get("pre_fps15"),u=g.get("units0"),avg=st["fps_avg"],p50=st.get("fps_p50"),live=live,live_s=live_s))
print("computable-with-live rows =",len(rows),"  distinct trips in them =",len(set(r['trip'] for r in rows)))
# trip-shared pre_fps15 over these computable rows
same=defaultdict(set)
for r in rows: same[r['trip']].add(r['pre'])
shared=sum(1 for k,v in same.items() if len(v)==1)
print("[E-reconcile] trips(among computable) =",len(same),"  identical pre_fps15 across windows =",shared,"  differing =",len(same)-shared)
# all-files trip grouping (for context)
allsame=defaultdict(set)
for fp in files:
    d=load(fp); allsame[d['trip_id']].add((d.get("gate") or {}).get("pre_fps15"))
print("   [context] ALL-files distinct trips =",len(allsame))
sub=[r for r in rows if r['pre']]
print("[F] rows with non-null pre =",len(sub))
for label,key in [("live","live"),("avg","avg"),("p50","p50")]:
    rho,n=spear([r['pre'] for r in sub],[r[key] for r in sub])
    print(f"  all-window rho(pre,{label}) = {rho:.4f} (n={n})" if rho is not None else f"  rho(pre,{label})=None")
w0=[r for r in sub if r['win']==0]
print("[F-w0] n =",len(w0))
for label,key in [("live","live"),("avg","avg")]:
    rho,n=spear([r['pre'] for r in w0],[r[key] for r in w0])
    print(f"  w0 rho(pre,{label}) = {rho:.4f} (n={n})" if rho is not None else f"  rho(pre,{label})=None")
# per-trip aggregation
per=defaultdict(list)
for r in sub: per[r['trip']].append(r)
tp_pre=[per[k][0]['pre'] for k in per]; tp_live=[sum(x['live'] for x in per[k])/len(per[k]) for k in per]
rho,n=spear(tp_pre,tp_live)
print(f"[F-agg] per-trip independent samples n_趟 = {n}  rho(pre, live_mean) = {rho:.4f}")
# also check pre_fps15 formula identity claim: recompute pre from last 1.5s of window0 samples for a couple trips
MEASURE_SETTLE_S=4.0; MEASURE_GATE_SPAN_S=1.5
def recompute_pre(fp):
    d=load(fp); t=d["samples"]["t"]; f=d["samples"]["f"]
    if len(t)<2: return None
    t0s=t[0]  # window starts at t0? gate samples are the SETTLE window prior to window0, so cannot recompute from window json samples.
    return None
# (gate samples live in a different pre-window; note we can't recompute from stored window samples)
print("[NOTE] pre_fps15 is computed over the settle-window samples (:5184-5191), NOT stored in window JSON => not independently recomputable from these files; qualitative 'same formula & clock as live_fps' verified from source lines only.")
