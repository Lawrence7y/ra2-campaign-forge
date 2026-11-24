# -*- coding: utf-8 -*-
"""Third verification: claims that the delivered scripts merely PRINT rather
than compute, O1 precision arithmetic, coverage of P, and wording scans."""
import json, re
from pathlib import Path

ROOT = Path("D:/Project/ra2-campaign-forge").resolve()
BASE = (ROOT / "out/re_work/work_chain/CONTINUE_20261003/lead/qc161_u0400_trip").resolve()
MANIFEST = (ROOT / "lead/goal3t_nightwatch_20261102/_stall_vs_gap_out.txt").resolve()
EVENTS = (ROOT / "lead/stall_event_def_20261106/STALL_EVENTS.json").resolve()
OUT = (ROOT / "lead/dtrigger_round2_20261107/_verify_D_out3.txt").resolve()
L=[]
def out(s=""):
    L.append(str(s)); print(s)

cache={}
for p in sorted(BASE.rglob("measure_w*.json")):
    pr=p.resolve(); parts=pr.relative_to(BASE).parts
    cache[(parts[0] if len(parts)>1 else "(root)", pr.stem.replace("measure_",""))]=\
        json.loads(pr.read_text(encoding="utf-8-sig"))
win=[]
for line in MANIFEST.read_text(encoding="utf-8-sig").splitlines():
    m=re.match(r"^([a-zA-Z0-9_\(\)]+)\s+(w\d)\s+([0-9\.]+)", line.strip())
    if m:
        k=(m[1],m[2])
        if k in cache:
            s=cache[k]["samples"]
            if len(s["t"])>=2 and any(a!=b for a,b in zip(s["f"],s["f"][1:])): win.append(k)
win=sorted(set(win))
runs=[]
for trip,w in win:
    t,f=cache[(trip,w)]["samples"]["t"],cache[(trip,w)]["samples"]["f"]
    n=len(f); i=0
    while i<n:
        j=i
        while j+1<n and f[j+1]==f[i]: j+=1
        runs.append(dict(trip=trip,w=w,i=i,d=(t[j]-t[i])*1000.0))
        i=j+1
ev=json.loads(EVENTS.read_text(encoding="utf-8"))
real=[e for e in ev if e.get("isRealMatch") is True]
realkey={(e["trip"],e["window"],e["startTick"]) for e in real}
big=[r for r in runs if r["d"]>=100.0]
big_real=[r for r in big if (r["trip"],r["w"],r["i"]) in realkey]
big_nonreal=len(big)-len(big_real)
allreal_big=sum(1 for e in real if any(r["trip"]==e["trip"] and r["w"]==e["window"] and r["i"]==e["startTick"] and r["d"]>=100.0 for r in runs))
out("T1 d_final>=100 runs=%d ; of those matching a real event START = %d ; non-real = %d" % (
    len(big), len(big_real), big_nonreal))
out("T1 real events whose own start-run has d_final>=100 = %d / %d" % (allreal_big, len(real)))
out("T1 CRITERIA_COMPARE.md:197 says 23 isRealMatch=False among d>=100 -> computed=%d" % big_nonreal)

# Is the 1681 in _dD_align_out.txt:50 COMPUTED or just len(real)?
al = (ROOT/"lead/dtrigger_round2_20261107/_dD_align.py").read_text(encoding="utf-8").splitlines()
out("T2 _dD_align.py:288-289 =")
for i in (287,288): out("     %r" % al[i])

# Is B4 (minimal set proof) computed at all?
ck = (ROOT/"lead/dtrigger_round2_20261107/_dD_check.py").read_text(encoding="utf-8").splitlines()
out("T3 _dD_check.py B4 block lines 128-137 (count of out() calls that interpolate a computed value):")
computed=0; literal=0
for i in range(127,137):
    ln=ck[i]
    if "out(" in ln:
        if "%" in ln or ".format" in ln or "f\"" in ln: computed+=1
        else: literal+=1
out("     computed=%d literal_prose=%d" % (computed,literal))
out("T3 B3 block lines 114-125:")
computed=0; literal=0
for i in range(113,125):
    ln=ck[i]
    if "out(" in ln:
        if "%" in ln or ".format" in ln or "f\"" in ln: computed+=1
        else: literal+=1
out("     computed=%d literal_prose=%d" % (computed,literal))

# doc line 6-9 command list vs reply's ranCommands=17
doc=(ROOT/"lead/dtrigger_round2_20261107/_dD_PHYSICAL_S_ALIGNMENT.md").read_text(encoding="utf-8").splitlines()
out("T4 main doc :6-9 command list:")
for i in range(5,9): out("     %r" % doc[i])

# O1 precision: line 126
out("T5 doc:126 = %r" % doc[125])
out("T5 1ms+1ms=2ms -> %.2f%% of 50ms (doc says 2%%)" % (100*2/50))
out("T5 O1+O2+O3 worst-case = 1+1+1+1+1 = 5ms -> %.2f%% of 50ms" % (100*5/50))

# :190 original text
sed=(ROOT/"lead/stall_event_def_20261106/STALL_EVENT_DEFINITION.md").read_text(encoding="utf-8").splitlines()
out("T6 STALL_EVENT_DEFINITION.md:190 = %r" % sed[189])
out("T6 doc:111 (claims :190 orthogonal to S) = %r" % doc[110].strip())

# extrapolation / S_hat-as-S wording scan
dd = sorted((ROOT/"lead/dtrigger_round2_20261107").glob("_dD_*"))
terms = ["方案可行","可行","批准","误报率","低误报","已证明合规","物理采不到","等于物理 S","S_hat = S","S = S_hat"]
out("T7 wording scan:")
for p in dd:
    txt=p.read_text(encoding="utf-8")
    hits={t:txt.count(t) for t in terms if t in txt}
    out("     %s : %s" % (p.name, hits if hits else "{}"))

# P coverage: doc 120 and 130
out("T8 doc:120 = %r" % doc[119].strip())
out("T8 doc:130 = %r" % doc[129].strip())
out("T8 doc:122 = %r" % doc[121].strip())

OUT.write_text("\n".join(L)+"\n", encoding="utf-8")
out("WROTE "+str(OUT))
