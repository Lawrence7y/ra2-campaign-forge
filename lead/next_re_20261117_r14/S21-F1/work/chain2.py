import sys
sys.path.insert(0, r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S21-F1\work")
import ra2 as R
import audit_lib as A

calls,jmps,stats=A.sweep_calls(R.BIN)
print("=== callers of MapSeed & Scenario functions ===")
for t in [0x597760,0x597A30,0x597D50,0x597D60,0x5AC270,0x53AD00,0x53C280,0x686B20,0x687F10,0x689470]:
    s=calls.get(t,[])
    print(f"  {t:08X}: {len(s)} -> {[hex(x) for x in s[:12]]}")

# find real entry containing 0x52F260: scan all call/jmp targets near 0x52E000-0x52F400
print("\n=== call/jmp targets in 0x52E000..0x52F400 (real entries) ===")
tgt=set()
for t,lst in calls.items():
    for s in lst:
        if 0x52E000<=s<0x52F500: tgt.add(s)
for t,lst in jmps.items():
    for s in lst:
        if 0x52E000<=s<0x52F500: tgt.add(s)
# include the target addresses themselves that fall in region
for t in list(calls)+list(jmps):
    if 0x52E000<=t<0x52F500: tgt.add(t)
for t in sorted(tgt):
    print(f"  {t:08X}")

# sweep_disps for campaign globals
print("\n=== disps referencing 0xa83cfc / 0xa83d08 / 0xa8f7a8 ===")
for g in [0xa83cfc, 0xa83d08, 0xa8f7a8, 0xa83d00]:
    f=A.sweep_disps(R.BIN,g)
    print(f"  global {g:08X}: {len(f)} refs")
    for x in f[:20]:
        print(f"     {x['va']:08X} {x['insn']}")

# victory/defeat strings
print("\n=== strings containing victory/defeat/mission/score (near code refs) ===")
data=R.BIN.pe.__data__
import re
for kw in [b"Victory",b"Defeat",b"MISSION",b"Mission",b"mission",b"SCORE",b"Score",b"score"]:
    idxs=[m.start() for m in re.finditer(re.escape(kw),data)]
    print(f"  {kw.decode()}: {len(idxs)} occurrences (first 5 off={idxs[:5]})")
