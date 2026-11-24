import json, os, glob
from collections import defaultdict

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "**", "measure_w*.json"), recursive=True))

def load(fp): return json.load(open(fp,encoding='utf-8'))

rows=[]
for fp in files:
    d=load(fp); s=d["samples"]; ts=s["t"]; fs=s["f"]
    st=d["stats"]
    avg=st.get("fps_avg"); p50=st.get("fps_p50"); u=st and d.get("gate",{}).get("units0")
    rows.append(dict(file=os.path.relpath(fp,ROOT).replace("\\","/"), trip=d.get("trip_id"),
        avg=avg, p50=p50, units0=u, f0=int(fs[0]) if len(fs) else None, fN=int(fs[-1]) if len(fs) else None))

comp=[r for r in rows if r['avg'] is not None]
# ---- units0 bins ----
def binof(u):
    if u is None: return "None"
    if u<300: return "0-300"
    if u<700: return "300-700"
    if u<1000: return "700-1000"
    if u<=1400: return "1000-1400"
    return ">1400"
order=["0-300","300-700","700-1000","1000-1400",">1400","None"]
print("== [G] units0 binning over 63 computable windows ==")
print("  bin : windows | avg<28 | p50<28 | whitewashed(avg<28 & p50>=28)")
for b in order:
    sub=[r for r in comp if binof(r['units0'])==b]
    if not sub: 
        print(f"  {b}: (empty)"); continue
    a_lt=[r for r in sub if r['avg']<28]
    p_lt=[r for r in sub if r['p50'] is not None and r['p50']<28]
    white=[r for r in sub if r['avg']<28 and (r['p50'] is not None and r['p50']>=28)]
    print(f"  {b}: {len(sub)} | {len(a_lt)} | {len(p_lt)} | {len(white)}")
print("  max units0 over computable =", max((r['units0'] for r in comp if r['units0'] is not None), default=None))

# ---- pre_fps15 trip detail (all trips incl. those with null) ----
bytrip=defaultdict(list)
for fp in files:
    d=load(fp)
    bytrip[d.get("trip_id")].append(d.get("gate",{}).get("pre_fps15"))
cnt3=cnt2=cnt1=0
ident_ge2=0; tot_ge2=0; null_present=0
for trip,vals in bytrip.items():
    if len(vals)==3: cnt3+=1
    elif len(vals)==2: cnt2+=1
    else: cnt1+=1
    if len(vals)>=2:
        tot_ge2+=1
        if None in vals: null_present+=1
        else:
            if len(set(round(v,9) for v in vals))<=1: ident_ge2+=1
print("== [E] trip grouping ==")
print("  distinct trips =",len(bytrip),"  3-window trips=",cnt3,"  2-window=",cnt2,"  1-window=",cnt1)
print("  trips>=2 windows:",tot_ge2,"  of those all-identical non-null:",ident_ge2,"  containing a null pre_fps15:",null_present)
# also trips that have all 3 windows and identical & non-null
c3id=sum(1 for trip,vals in bytrip.items() if len(vals)==3 and None not in vals and len(set(round(v,9) for v in vals))<=1)
print("  trips with exactly 3 windows AND identical non-null pre_fps15 =",c3id)

# ---- T32 / T34 continuation-window freeze ----
for trip in ["QC161-U0400-T32","QC161-U0400-T34","QC161-U0400-T38"]:
    sub=[r for r in rows if r['trip']==trip]
    sub=sorted(sub, key=lambda r: r['file'])
    line=f"  {trip}: "
    for r in sub:
        line+=f"{os.path.basename(r['file'])} {r['f0']}->{r['fN']}(avg={round(r['avg'],2) if r['avg'] else r['avg']})  "
    print("== [C] cont-window:",line)
