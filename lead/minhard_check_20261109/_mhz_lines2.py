# _mhz_lines2.py — targeted line dumps for section 4/5 evidence (this session)
import os, sys
ROOT = r"D:\Project\ra2-campaign-forge"
def rp(rel): return os.path.join(ROOT, rel.replace("/", os.sep))
def ls(rel):
    with open(rp(rel), "rb") as f: return f.read().decode("utf-8").splitlines()
O=[]
def p(s=""): O.append(str(s))

RANGES = [
 ("lead/s604_refsync_full_20261109/S604_REFSYNC_FULL.md", 283, 325),
 ("lead/s604_verdict_entry_20261109/S604_VERDICT_ENTRY_DRAFT.md", 88, 132),
 ("lead/ledger_bound_20261109/_lb2_TEMPLATE.md", 148, 163),
 ("lead/ledger_bound_20261109/LEDGER_BOUND_VOLUME.md", 40, 50),
 ("lead/ledger_bound_20261109/_lb_BOUND_VOLUME.md", 290, 300),
 ("lead/minhard_check_20261109/_mh_MINHARD_CHECK.md", 181, 190),
 ("lead/minhard_check_20261109/_mh_MINHARD_CHECK.md", 274, 281),
 ("lead/minhard_check_20261109/_mh_MINHARD_CHECK.md", 143, 160),
]
for rel, a, b in RANGES:
    L=ls(rel)
    p(f"==== {rel} :{a}-{b} (total {len(L)}) ====")
    for n in range(a, min(b, len(L))+1):
        p(f"  :{n}: {L[n-1]}")

# writer claim check: 21 件? 20?
WD=rp("lead/minhard_check_20261109")
p("")
p("==== write-domain file counts (this session) ====")
for pref in ["_mh_", "_mhv_", "_mhz_"]:
    fs=sorted(f for f in os.listdir(WD) if f.startswith(pref))
    p(f"  {pref} count={len(fs)}")
    p(f"    {fs}")
p(f"  MINHARD_SET_CHECK.md exists={os.path.isfile(os.path.join(WD,'MINHARD_SET_CHECK.md'))}")

sys.stdout.write("\n".join(O)+"\n")
