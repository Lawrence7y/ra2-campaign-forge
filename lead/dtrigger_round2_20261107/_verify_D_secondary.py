# -*- coding: utf-8 -*-
"""Secondary verification: all 15 fingerprints, line counts, extreme-event
location, strict multiset containment, and the O1 precision arithmetic."""
import hashlib, json, re, statistics
from collections import Counter
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
OUT = (ROOT / "lead/dtrigger_round2_20261107/_verify_D_out2.txt").resolve()

L = []
def out(s=""):
    L.append(str(s)); print(s)

# --- 1. all 15 objects listed in _dD_align_out.txt:6-20 ---
d = (ROOT/"lead/dtrigger_round2_20261107/_dD_align_out.txt").read_text(encoding="utf-8")
claimed = {}
for m in re.finditer(r"被核对象 SHA256 = ([0-9a-f]{64})，字节数 = (\d+)\s+<-\s+(\S+)", d):
    claimed[m[3]] = (m[1], int(m[2]))
out("S1 objects declared in _dD_align_out.txt = %d" % len(claimed))
allok = True
for rel,(sha,n) in sorted(claimed.items()):
    b = (ROOT/rel).read_bytes()
    ok = hashlib.sha256(b).hexdigest()==sha and len(b)==n
    allok &= ok
    out("   OK=%s %s bytes=%d" % (ok, rel, len(b)))
out("S1 ALL 15 MATCH = %s" % allok)

# --- 2. line counts of cited files / outputs ---
for rel in ["lead/dstart_observable_20261107/S_UNCERTAINTY.md",
            "lead/dtrigger_round2_20261107/_dD_align_out.txt",
            "lead/dtrigger_round2_20261107/_dD_check_out.txt",
            "lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md"]:
    txt = (ROOT/rel).read_text(encoding="utf-8")
    out("S2 %s lines(splitlines)=%d has_7.3=%s has_160/201_ref=%s" % (
        rel, len(txt.splitlines()), "7.3" in txt, ("160" in txt or "201" in txt)))

# --- 3. extreme 488.616 location ---
cache = {}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr=p.resolve(); parts=pr.relative_to(BASE).parts
    cache[(parts[0] if len(parts)>1 else "(root)", pr.stem.replace("measure_",""))] = \
        json.loads(pr.read_text(encoding="utf-8-sig"))
ts = cache[("l3_20261031hb","w1")]["samples"]["t"]
fs = cache[("l3_20261031hb","w1")]["samples"]["f"]
gaps = [(i, (ts[i]-ts[i-1])*1000.0) for i in range(1,len(ts))]
mx = max(gaps, key=lambda x:x[1])
out("S3 l3_20261031hb/w1 max adjacent gap at sample[%d] = %.3f ms (f:%s->%s)" % (
    mx[0], mx[1], fs[mx[0]-1], fs[mx[0]]))
out("S3 t[1376]=%.6f t[1377]=%.6f f[1376]=%s f[1377]=%s" % (
    ts[1376], ts[1377], fs[1376], fs[1377]))

# --- 4. strict multiset containment B <= A (counter subtraction) ---
win=[]
for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m=re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
    if m:
        k=(m[1],m[2])
        if k in cache:
            s=cache[k]["samples"]; t,f=s["t"],s["f"]
            if len(t)>=2 and any(a!=b for a,b in zip(f,f[1:])): win.append(k)
win=sorted(set(win))
Avals=[]; runidx={}
for trip,w in win:
    t,f=cache[(trip,w)]["samples"]["t"],cache[(trip,w)]["samples"]["f"]
    n=len(f); i=0
    while i<n:
        j=i
        while j+1<n and f[j+1]==f[i]: j+=1
        if i>0:
            g=(t[i]-t[i-1])*1000.0; Avals.append(g); runidx[(trip,w,i)]=g
        i=j+1
ev=json.loads(EVENTS.read_text(encoding="utf-8"))
real=[e for e in ev if e.get("isRealMatch") is True]
Bvals=[]
for e in real:
    if e["startTick"]>0:
        k=(e["trip"],e["window"],e["startTick"])
        Bvals.append(runidx[k])   # by positional identity, not by value lookup
ca, cb = Counter(Avals), Counter(Bvals)
missing = sum(max(0, cb[v]-ca[v]) for v in cb)
out("S4 strict multiset B<=A: excess_count=%d (0 means true sub-multiset)" % missing)
out("S4 len(A)=%d len(B)=%d distinct B values=%d" % (len(Avals),len(Bvals),len(cb)))
out("S4 real events whose (trip,window) is NOT in the 64 windows = %d" % (
    sum(1 for e in real if (e["trip"],e["window"]) not in win)))

# --- 5. O1 precision arithmetic in _dD_PHYSICAL_S_ALIGNMENT.md:126 ---
out("S5 1ms/50ms = %.2f%% ; (1ms+1ms)/50ms = %.2f%% ; (1+1+1)ms/50ms = %.2f%%" % (
    100*1/50, 100*2/50, 100*3/50))
out("S5 doc line 126 says '合计 <= :177 的 50 ms 预算的 2%' -- check against above")

# --- 6. contradiction inside _dD_check_out.txt ---
ck = (ROOT/"lead/dtrigger_round2_20261107/_dD_check_out.txt").read_text(encoding="utf-8").splitlines()
out("S6 _dD_check_out.txt:12 = %r" % ck[11])
out("S6 _dD_check_out.txt:19 = %r" % ck[18])
out("S6 _dD_check.py:91 = %r" % (
    (ROOT/"lead/dtrigger_round2_20261107/_dD_check.py").read_text(encoding="utf-8").splitlines()[90]))
out("S6 main doc line 72 = %r" % (
    (ROOT/"lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md").read_text(encoding="utf-8").splitlines()[71]))

# --- 7. exact wording of D-2 vs upstream ---
cc = (ROOT/"lead/dtrigger_compare_20261107/CRITERIA_COMPARE.md").read_text(encoding="utf-8").splitlines()
for ln in (35,145,147,216,219):
    out("S7 CRITERIA_COMPARE.md:%d = %r" % (ln, cc[ln-1].strip()))
out("S7 _dD_check_out.txt:39 = %r" % ck[38])
sup = (ROOT/"lead/dtrigger_compare_20261107/_dtrigger_supplement_out.txt").read_text(encoding="utf-8").splitlines()
out("S7 supplement:33 = %r" % sup[32])

OUT.write_text("\n".join(L)+"\n", encoding="utf-8")
out("WROTE "+str(OUT))
