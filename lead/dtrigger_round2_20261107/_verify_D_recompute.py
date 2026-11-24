# -*- coding: utf-8 -*-
"""Independent verification of dimension D's numeric claims, from raw corpus.

Deliberately written from scratch (only the manifest-regex / run segmentation
convention copied from the ORIGINAL upstream probe _dtrigger_probe.py:106-154,
which is the authoritative definition), NOT reusing _dD_align.py or _dD_check.py.
Read-only except this script's own output file in the allowed write domain.
"""
import json, re, statistics, hashlib
from collections import Counter
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
S_EST = (ROOT / "lead/dstart_observable_20261107/S_ESTIMATES.json").resolve()
OUT = (ROOT / "lead/dtrigger_round2_20261107/_verify_D_out.txt").resolve()

L = []
def out(s=""):
    L.append(str(s)); print(s)

def nearest_rank(sorted_arr, p):
    return sorted_arr[int(p * (len(sorted_arr) - 1))]

def f3(v): return "N/A" if v is None else "%.3f" % v

# ---- load corpus (own loop) ----
cache = {}
files = sorted(BASE.rglob("measure_w*.json"))
for p in files:
    pr = p.resolve()
    parts = pr.relative_to(BASE).parts
    key = (parts[0] if len(parts) > 1 else "(root)", pr.stem.replace("measure_", ""))
    cache[key] = json.loads(pr.read_text(encoding="utf-8-sig"))
tot = sum(len(d["samples"]["t"]) for d in cache.values())
hz = sorted({d.get("hz") for d in cache.values()})
out("V1 files=%d samples=%d hz=%s" % (len(files), tot, hz))

# ---- manifest windows (same regex as ORIGINAL probe _dtrigger_probe.py:109) ----
win = []
for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m = re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
    if m:
        k = (m[1], m[2])
        if k in cache:
            s = cache[k].get("samples", {})
            ts, fs = s.get("t", []), s.get("f", [])
            if len(ts) >= 2 and any(a != b for a, b in zip(fs, fs[1:])):
                win.append(k)
win = sorted(set(win))
out("V2 moving64 windows=%d" % len(win))

# ---- population A: every frame-number run's onset gap e ----
runs = []
hist_all = []
for trip, w in win:
    ts, fs = cache[(trip, w)]["samples"]["t"], cache[(trip, w)]["samples"]["f"]
    n = len(fs)
    last_edge = 0
    for i in range(1, n):
        if fs[i] != fs[i-1]:
            hist_all.append((ts[i]-ts[last_edge])*1000.0); last_edge = i
    i = 0
    while i < n:
        j = i
        while j+1 < n and fs[j+1] == fs[i]: j += 1
        runs.append((trip, w, i, j,
                     (ts[i]-ts[i-1])*1000.0 if i>0 else None,
                     (ts[j]-ts[i])*1000.0))
        i = j+1
A = sorted(r[4] for r in runs if r[4] is not None)
wfirst = [r for r in runs if r[4] is None]
hist_s = sorted(hist_all)
out("V3 all_runs=%d A_valid=%d window_first=%d" % (len(runs), len(A), len(wfirst)))
out("V4 e: min=%s med=%s P50nr=%s P95=%s P99=%s max=%s" % (
    f3(A[0]), f3(statistics.median(A)), f3(nearest_rank(A,.50)),
    f3(nearest_rank(A,.95)), f3(nearest_rank(A,.99)), f3(A[-1])))
out("V5 e>0=%d/%d e>6=%d e>50=%d e>100=%d" % (
    sum(x>0 for x in A), len(A), sum(x>6 for x in A),
    sum(x>50 for x in A), sum(x>100 for x in A)))
out("V6 hist n=%d P50=%s P95=%s P99=%s" % (
    len(hist_s), f3(nearest_rank(hist_s,.50)), f3(nearest_rank(hist_s,.95)), f3(nearest_rank(hist_s,.99))))

# ---- population B: real events' U ----
events = json.loads(EVENTS.read_text(encoding="utf-8"))
real = [e for e in events if e.get("isRealMatch") is True]
sest = json.loads(S_EST.read_text(encoding="utf-8"))
byid = {r["eventId"]: r for r in sest}
U = []; Uraw = []; qual = Counter(); mism = []
for e in real:
    trip, w, st, et = e["trip"], e["window"], e["startTick"], e["endTick"]
    eid = "%s/%s/%s/%s" % (trip, w, st, et)
    ts = cache[(trip, w)]["samples"]["t"]; t0 = ts[0]
    if st == 0:
        rec = dict(durationMs=e["durationMs"], firstObservedMs=0.0,
                   sLowerBoundMs=0.0, sUpperBoundMs=0.0, sUncertaintyMs=0.0,
                   priorIntervalMs=None, quality="unknown")
    else:
        fo = round((ts[st]-t0)*1000.0, 3); lo = round((ts[st-1]-t0)*1000.0, 3)
        unc = round(fo-lo, 3)
        rec = dict(durationMs=e["durationMs"], firstObservedMs=fo,
                   sLowerBoundMs=lo, sUpperBoundMs=fo, sUncertaintyMs=unc,
                   priorIntervalMs=unc, quality="full" if unc<=6.0 else "bounded")
        U.append(unc); Uraw.append((ts[st]-ts[st-1])*1000.0)
    qual[rec["quality"]] += 1
    b = byid.get(eid)
    if b is None: mism.append((eid,"MISSING"))
    else:
        for k in rec:
            if b.get(k) != rec[k]: mism.append((eid,k,rec[k],b.get(k)))
U.sort(); Uraw.sort()
out("V7 events_all=%d real=%d sest=%d mismatch=%d/%d" % (
    len(events), len(real), len(sest), len(mism), len(real)))
out("V8 quality full=%d bounded=%d unknown=%d sum=%d" % (
    qual["full"], qual["bounded"], qual["unknown"], sum(qual.values())))
out("V9 U(n=%d): min=%s med=%s P95=%s P99=%s max=%s" % (
    len(U), f3(U[0]), f3(statistics.median(U)), f3(nearest_rank(U,.95)),
    f3(nearest_rank(U,.99)), f3(U[-1])))
out("V10 U>6=%d U>50=%d U>100=%d U>48=%d U>49=%d U>51=%d" % (
    sum(x>6 for x in U), sum(x>50 for x in U), sum(x>100 for x in U),
    sum(x>48 for x in U), sum(x>49 for x in U), sum(x>51 for x in U)))

# ---- set relations ----
og_counter = Counter(A)
contained = sum(1 for u in Uraw if og_counter.get(u,0)>0)
runidx = {(r[0],r[1],r[2]): r[4] for r in runs}
pair = 0; pairn = 0
for e in real:
    if e["startTick"]>0:
        pairn += 1
        k=(e["trip"],e["window"],e["startTick"])
        ts=cache[(e["trip"],e["window"])]["samples"]["t"]
        if k in runidx and runidx[k] is not None and \
           abs(runidx[k]-(ts[e["startTick"]]-ts[e["startTick"]-1])*1000.0)<1e-9:
            pair += 1
unk = [e for e in real if e["startTick"]==0]
wfk = {(r[0],r[1]) for r in wfirst}
out("V11 contained=%d/%d pair_equal=%d/%d" % (contained,len(Uraw),pair,pairn))
out("V12 startTick0 real=%d in_wf=%d" % (len(unk), sum((e["trip"],e["window"]) in wfk for e in unk)))
out("V13 d_final>=100 runs=%d real=%d delta=%d" % (
    sum(r[5]>=100 for r in runs), len(real), sum(r[5]>=100 for r in runs)-len(real)))
realkeys={(e["trip"],e["window"],e["startTick"]) for e in real}
out("V14 A e>50=%d of which real=%d" % (
    sum(x>50 for x in A), sum(1 for r in runs if r[4] is not None and r[4]>50 and (r[0],r[1],r[2]) in realkeys)))
BA = 100.0*len(U)/len(A)
enr50 = (sum(x>50 for x in U)/len(U))/(sum(x>50 for x in A)/len(A))
out("V15 B/A=%.4f%% enrichment(e>50)=%.4fx" % (BA,enr50))

# ---- independent check of the DISCIPLINE / CLAIM sensitivity ----
# Does the "B subset A" claim depend on array sorting (i.e. is it multiset containment
# of values, or positional identity)? Verify positional identity separately.
posok=0
for e in real:
    if e["startTick"]>0:
        k=(e["trip"],e["window"],e["startTick"])
        if k in runidx and runidx[k] is not None: posok+=1
out("V16 positional (trip,win,startTick) present in runs = %d/%d" % (posok, pairn))

# ---- discipline scan of _dD_* files for forbidden tokens ----
forbid = ["gamemd.exe","ra2loader","YURI.exe","taskkill","OpenProcess",
          "ReadProcessMemory","WriteProcessMemory","VirtualAllocEx",
          "CreateRemoteThread","SetWindowsHookEx","TerminateProcess",
          "SuspendThread","StackWalk","MiniDump","ctypes"]
dd = sorted((ROOT/"lead/dtrigger_round2_20261107").glob("_dD_*"))
out("V17 discipline scan over %d _dD_ files:" % len(dd))
for p in dd:
    txt = p.read_text(encoding="utf-8", errors="replace")
    hits = [t for t in forbid if t.lower() in txt.lower()]
    out("    %s : %s" % (p.name, "CLEAN" if not hits else "HITS="+repr(hits)))

OUT.write_text("\n".join(L)+"\n", encoding="utf-8")
out("WROTE "+str(OUT))
