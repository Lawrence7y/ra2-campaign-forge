import json, os, glob

ROOT = "D:/Project/ra2-campaign-forge/out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip"
files = sorted(glob.glob(os.path.join(ROOT, "**", "measure_w*.json"), recursive=True))

def load(fp): return json.load(open(fp,encoding='utf-8'))

# ============ V1-A4 : archive_T34/measure_w0.json sampling gap ============
fp = os.path.join(ROOT,"archive_T34","measure_w0.json")
d = load(fp)
s = d["samples"]; ts=s["t"]; fs=s["f"]
n=len(ts); span=ts[-1]-ts[0]; logic=int(fs[-1])-int(fs[0])
hz=n/span
dts=[ts[i+1]-ts[i] for i in range(n-1)]
gt10=[x for x in dts if x>0.010]
# cumulative gap: sum of (dt - nominal) over dt>10ms ; nominal = median or mean interval
import statistics as stt
nominal=stt.median(dts)
cumgap=sum(x-nominal for x in gt10)
maxsingle=max(dts)
per_sec=[0]*25
for i,f in enumerate(fs):
    idx=int(ts[i]-ts[0])
    if 0<=idx<25: per_sec[idx]+= (int(f))
# per-second frame ADVANCE
adv=[]
prev=int(fs[0])
sec_frames=[[] for _ in range(25)]
for i,f in enumerate(fs):
    idx=int(ts[i]-ts[0])
    if 0<=idx<25: sec_frames[idx].append(int(f))
# compute per-second net advance using last frame seen in each second
lastf=int(fs[0]); advs=[]
for k in range(25):
    if sec_frames[k]:
        cur=sec_frames[k][-1]; advs.append((k,cur-lastf)); lastf=cur
    else:
        advs.append((k,0))
print("== [A4] archive_T34/w0 :")
print("  samples n =",n," span =",round(span,6)," hz_effective =",round(hz,1))
print("  dt>10ms count =",len(gt10),"  cumulative gap (sum dt-median over dt>10ms) =",round(cumgap,6),"  max single dt =",round(maxsingle,6))
print("  median dt (nominal) =",round(nominal,6))
print("  logic =",logic," first frame =",int(fs[0])," last frame =",int(fs[-1]))
print("  per-second net advance:", [f"{k}:{a}" for k,a in advs])
print("  json.stats fps_avg=",d["stats"]["fps_avg"],"max_stall_s=",d["stats"]["max_stall_s"],"n_multi_advance=",d["stats"]["n_multi_advance"],"n_edges=",d["stats"]["n_edges"])

# ============ V1-A5 : census of zero-advance windows with measured span>20s ============
cnt=0
cnt_all=0
census=[]
for x in files:
    dd=load(x)
    smp=dd["samples"]
    t=smp["t"]; f=smp["f"]
    if len(t)<2: continue
    sp=t[-1]-t[0]
    note=dd["stats"].get("note","")
    if note=="frame not advancing":
        cnt_all+=1
        if sp>20:
            cnt+=1
            census.append((os.path.relpath(x,ROOT).replace("\\","/"), round(sp,3), dd["stats"].get("logic_frames")))
print("== [A5] census : note='frame not advancing' windows total =",cnt_all," ; of those with measured span>20s =",cnt)

# the reset window details
fp2=os.path.join(ROOT,"l1_20261023e4","measure_w1.json")
d2=load(fp2)
s2=d2["samples"]; t2=s2["t"]; f2=s2["f"]
n2=len(t2); sp2=t2[-1]-t2[0]; logic2=int(f2[-1])-int(f2[0])
fe=[]; prev=None
t0=t2[0]
for tt,ff in zip(t2,f2):
    fi=int(ff)
    if prev is None or fi!=prev:
        fe.append((fi,tt-t0)); prev=fi
# frame_ms df==1
fms=[]; nmulti=0
for (fa,ta),(fb,tb) in zip(fe,fe[1:]):
    df=fb-fa
    if df==1: fms.append((tb-ta)*1000)
    elif df>1: nmulti+=1
fms_s=sorted(fms)
def pctl(sv,q):
    if not sv: return None
    if len(sv)==1: return float(sv[0])
    idx=(len(sv)-1)*q; lo=int(idx); hi=min(lo+1,len(sv)-1); fr=idx-lo
    return float(sv[lo]*(1-fr)+sv[hi]*fr)
p50=pctl(fms_s,0.5); fps50=1000/p50 if p50 else None
# find reset: frame goes up then drops to 0
print("== [A5-reset] l1_20261023e4/w1:")
print("  n =",n2," span =",round(sp2,6)," logic =",logic2," n_edges(recomputed) =",len(fe)," (json n_edges=",d2['stats']['n_edges'],")")
print("  frame_edges f sequence head/tail:", [a[0] for a in fe[:6]],"...",[a[0] for a in fe[-6:]])
# first rising phase
# find where it resets to 0
reset_idx=None
for i,(fv,tt) in enumerate(fe):
    if i>0 and fv<fe[i-1][0]:
        reset_idx=i; break
print("  first max frame before reset =", max(a[0] for a in fe[:reset_idx]) if reset_idx else None,
      " reset at t_rel =", round(fe[reset_idx][1],3) if reset_idx else None,
      " value after reset =", fe[reset_idx][0] if reset_idx else None)
# pre-reset fps
if reset_idx:
    # rise phase: from first edge to the edge right before reset
    rise_edges=fe[:reset_idx]
    if len(rise_edges)>=2:
        rspan=rise_edges[-1][1]-rise_edges[0][1]
        radv=rise_edges[-1][0]-rise_edges[0][0]
        print("  rise phase: dur=",round(rspan,3),"adv=",radv,"=> fps=",round(radv/rspan,2) if rspan>0 else None)
    # post reset stall length
    print("  post-reset last edge t_rel =", round(fe[-1][1],3)," final frame =", fe[-1][0])
print("  recomputed fps_p50 =", round(fps50,4) if fps50 else None, " (json stats fps_p50=", d2['stats']['fps_p50'],")")

# ============ pre_fps15 duplicate counting across windows within a trip ============
from collections import defaultdict
bytrip=defaultdict(list)
for x in files:
    dd=load(x)
    bytrip[dd.get("trip_id")].append((os.path.basename(x), dd.get("gate",{}).get("pre_fps15"), dd.get("gate",{}).get("units0")))
trips_with_3=0; trips_identical=0; mismatch=[]
for trip,lst in bytrip.items():
    vals=[v for _,v,_ in lst]
    nnz=[v for v in vals if v is not None]
    if len(vals)>=2:
        trips_with_3+=1
        uniq=set(round(v,9) for v in nnz)
        if len(uniq)<=1 and None not in vals:
            trips_identical+=1
        else:
            mismatch.append((trip,vals,len(lst)))
print("== [A5-dup] distinct trips =",len(bytrip)," ; trips with >=2 windows =",trips_with_3," ; trips where all windows share identical non-null pre_fps15 =",trips_identical)
print("   mismatch trips:",mismatch[:10])
print("   window counts per trip distribution:", sorted(set(len(v) for v in bytrip.values())))
