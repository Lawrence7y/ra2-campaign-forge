import json, os, glob, math, statistics

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "**", "measure_w*.json"), recursive=True))
# also root-level
rootfiles = sorted(glob.glob(os.path.join(ROOT, "measure_w*.json")))

print("RECURSIVE files count =", len(files))
print("ROOT-level files count =", len(rootfiles))
# ensure root files are inside recursive set
rf = set(os.path.abspath(x) for x in rootfiles)
rec = set(os.path.abspath(x) for x in files)
print("root subset of recursive?", rf <= rec)
print("recursive==rec", len(rec))

def pctl(sorted_vals, q):
    if not sorted_vals: return None
    if len(sorted_vals)==1: return float(sorted_vals[0])
    idx=(len(sorted_vals)-1)*q
    lo=int(idx); hi=min(lo+1,len(sorted_vals)-1); frac=idx-lo
    return float(sorted_vals[lo]*(1.0-frac)+sorted_vals[hi]*frac)

def relerr(a,b):
    if a is None or b is None:
        return (0.0 if a is None and b is None else float('inf'))
    den = abs(b) if abs(b)>1e-12 else 1e-12
    return abs(a-b)/den

rows=[]
read_fail=0
edges_mismatch=0
edges_missing=0
for fp in files:
    try:
        d=json.load(open(fp,encoding='utf-8'))
    except Exception as e:
        read_fail+=1
        print("READ FAIL", fp, e); continue
    st=d.get("stats",{})
    samples=d.get("samples")
    if isinstance(samples, dict):
        ts=samples.get("t",[]); fs=samples.get("f",[])
    else:
        ts=[]; fs=[]
    n=len(ts)
    # recompute span/logic
    span = (ts[-1]-ts[0]) if n>=2 else None
    logic = (int(fs[-1])-int(fs[0])) if n>=2 else None
    # recompute fps_avg
    fps_avg=None; note_r=""
    if n<2:
        note_r="insufficient samples"
    else:
        if logic<=0:
            note_r="frame not advancing"
        elif (span is not None and span>0):
            fps_avg = logic/span
    # recompute frame_edges from samples
    fe=[]
    prev=None
    for t,f in zip(ts,fs):
        fi=int(f)
        if prev is None or fi!=prev:
            fe.append((fi,t)); prev=fi
    # compare to json frame_edges
    jfe=d.get("frame_edges",None)
    if jfe is None:
        edges_missing+=1
    else:
        ok = len(jfe)==len(fe) and all(abs(a[1]-b[1])<1e-6 and a[0]==b[0] for a,b in zip(jfe,fe))
        if not ok:
            edges_mismatch+=1
    # frame_ms from recomputed edges
    frame_ms=[]; n_multi=0
    for (fa,ta),(fb,tb) in zip(fe,fe[1:]):
        df=fb-fa
        if df==1: frame_ms.append((tb-ta)*1000.0)
        elif df>1: n_multi+=1
    frame_ms_sorted=sorted(frame_ms)
    p50 = pctl(frame_ms_sorted,0.5) if frame_ms_sorted else None
    fps_p50 = (1000.0/p50) if (p50 and p50>0) else None
    # live_fps = logic / active_span ; active = last edge time - first sample time
    live_fps=None; active_s=None; tail_s=None
    if fps_avg is not None and fe:
        active_s = fe[-1][1]-ts[0]
        tail_s = ts[-1]-fe[-1][1]
        if active_s>0: live_fps = logic/active_s
    # gate
    gate=d.get("gate",{})
    units0 = gate.get("units0", None)
    pre_fps15 = gate.get("pre_fps15", None)
    rows.append(dict(
        file=os.path.relpath(fp,ROOT).replace("\\","/"),
        trip=d.get("trip_id"), win=d.get("window"),
        n=n, span=span, logic=logic,
        fps_avg=fps_avg, stats_fps_avg=st.get("fps_avg"),
        fps_p50=fps_p50, stats_fps_p50=st.get("fps_p50"),
        live_fps=live_fps, active_s=active_s, tail_s=tail_s,
        n_gap=len(frame_ms),
        note_r=note_r, stats_note=st.get("note"),
        units0=units0, pre_fps15=pre_fps15,
        max_stall_s=st.get("max_stall_s"),
    ))

print("read_fail=",read_fail,"edges_missing=",edges_missing,"edges_mismatch=",edges_mismatch)
print("total rows=",len(rows))

# --- max rel error of fps_avg recompute vs stats ---
maxre=0.0; maxre_row=None; mism_avg=0
for r in rows:
    re=relerr(r['fps_avg'], r['stats_fps_avg'])
    if re==float('inf') or re>1e-9:
        mism_avg+=1
        if re!=float('inf') or True:
            pass
    if re<1e9 and re>maxre:
        maxre=re; maxre_row=r
# also flag any where one None other not
flag_avg=[]
for r in rows:
    a,b=r['fps_avg'],r['stats_fps_avg']
    if (a is None)!=(b is None):
        flag_avg.append((r['file'],a,b,r['note_r'],r['stats_note']))
print("== [1] fps_avg recompute vs stats: max relerr =", round(maxre,9), "row=",maxre_row['file'] if maxre_row else None)
print("   mismatch count (relerr>1e-9 or None-mismatch) =", mism_avg, " ; None-mismatch flags:", len(flag_avg))
for x in flag_avg: print("   FLAG", x)

# max rel error of fps_p50 vs stats
maxre50=0.0; flag50=[]
for r in rows:
    a,b=r['fps_p50'],r['stats_fps_p50']
    if (a is None)!=(b is None):
        flag50.append((r['file'],a,b,r['logic'],r['n']))
    if a is not None and b is not None:
        re=relerr(a,b)
        if re>maxre50: maxre50=re
print("== [1c] fps_p50 recompute vs stats: max relerr(non-null)=",round(maxre50,9),"; None-mismatch flags:",len(flag50))
for x in flag50: print("   FLAG", x)

# --- classification ---
computable=[r for r in rows if r['stats_fps_avg'] is not None]
nullw=[r for r in rows if r['stats_fps_avg'] is None]
def notecount(rs):
    c={}
    for r in rs:
        k=r['stats_note'] or "(empty)"
        c[k]=c.get(k,0)+1
    return c
print("== [2] computable (stats.fps_avg not null) =",len(computable),"null =",len(nullw))
print("   null notes breakdown:", notecount(nullw))
print("   computable notes breakdown:", notecount(computable))
# span buckets of null windows
buckets={}
for r in nullw:
    if r['n']<2: k="insufficient"
    else: k=str(round(r['span'],1))
    buckets[k]=buckets.get(k,0)+1
print("   null window span buckets:", buckets)

ge28=[r for r in computable if r['stats_fps_avg']>=28]
lt28=[r for r in computable if r['stats_fps_avg']<28]
print("== [3] fps_avg>=28 =",len(ge28),"  fps_avg<28 =",len(lt28))
# avg<28 & p50>=28
white=[r for r in computable if r['stats_fps_avg']<28 and (r['stats_fps_p50'] is not None and r['stats_fps_p50']>=28)]
print("   avg<28 & p50>=28 =",len(white))
for r in white: print("     ",r['file'],"avg=",round(r['stats_fps_avg'],2),"p50=",round(r['stats_fps_p50'],2),"units0=",r['units0'])
# ge28 all p50>=28 ?
ge28_p50lt=[r for r in ge28 if not (r['stats_fps_p50'] is not None and r['stats_fps_p50']>=28)]
print("   among avg>=28, p50 not >=28 count =",len(ge28_p50lt))
# live<28
live_lt=[r for r in computable if r['live_fps'] is not None and r['live_fps']<28]
live_ge=[r for r in computable if r['live_fps'] is not None and r['live_fps']>=28]
live_null=[r for r in computable if r['live_fps'] is None]
print("   live_fps<28 =",len(live_lt),"  live>=28 =",len(live_ge),"  live null =",len(live_null))
# p50<28
p50_lt=[r for r in computable if r['stats_fps_p50'] is not None and r['stats_fps_p50']<28]
p50_ge=[r for r in computable if r['stats_fps_p50'] is not None and r['stats_fps_p50']>=28]
p50_null=[r for r in computable if r['stats_fps_p50'] is None]
print("   fps_p50<28 =",len(p50_lt),"  p50>=28 =",len(p50_ge),"  p50 null =",len(p50_null))

# live<avg check (structurally)
la=[r for r in computable if r['live_fps'] is not None and r['stats_fps_avg'] is not None and r['live_fps']<r['stats_fps_avg']-1e-9]
print("== [4] live_fps < fps_avg count =",len(la))
# ratio med/p90/max
ratios=[r['live_fps']/r['stats_fps_avg'] for r in computable if r['live_fps'] is not None and r['stats_fps_avg'] is not None and r['stats_fps_avg']>0]
ratios_sorted=sorted(ratios)
print("   ratio count=",len(ratios)," median=",round(pctl(ratios_sorted,0.5),4)," p90=",round(pctl(ratios_sorted,0.9),4)," max=",round(max(ratios),4))

# max fps_avg overall
mx=max(r['stats_fps_avg'] for r in computable)
print("   max fps_avg over computable =",round(mx,4))
p50_over32=[r for r in computable if r['stats_fps_p50'] and r['stats_fps_p50']>32]
print("   computable windows with p50>32 =",len(p50_over32),[ (r['file'],round(r['stats_fps_p50'],2),r['n_gap']) for r in p50_over32])
