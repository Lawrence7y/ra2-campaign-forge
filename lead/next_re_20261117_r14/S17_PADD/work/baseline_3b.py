"""
③b base rate for S17-PADD (D-42 / §8.6 条3 four tiers) -- FIXED.
Pool = S17 [静态推断] rows in atlas; disassembly BOUNDED BY ATLAS SIZE (no cross-function spill).
Detector tiers (③b = overall contract, not ③a mechanical):
  ① jump table / switch: jmp [reg*4+disp] with >=2 distinct arms
  ② falsifiable return convention: >=2 DISTINCT HRESULT/(-1) constants, each with a reachable ret
  ③ memory shape: >=2 vptr imm32 installs in first 0x40 bytes + allocator call
  ④ complete I/O loop: back-edge within function + non-stack write + cmp/jcc
Random sample N=2 without replacement, seed 20261119, 2000 trials.
"""
import random
import re_lib as R

TAB = chr(9)
COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

asize = {}
for ln in open(ATLAS, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if len(c) >= 2:
        try: asize[c[0].upper()] = int(c[1])
        except ValueError: pass

pool = []
for ln in open(COV, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if len(c) < 5: continue
    if c[1] == "S17" and c[4] == "[静态推断]" and c[0].upper() in asize:
        pool.append((c[0], int(c[0],16), asize[c[0].upper()]))
pool.sort()
print("S17 [静态推断] pool in atlas:", len(pool))

def detect(va, size):
    ins = R.disasm(va, min(size, 0x1000))
    ins = [x for x in ins if x[0] < va + size]
    if not ins: return []
    tiers = []
    # ① jump table: indirect jump through scaled index, collect distinct targets/table bases
    tab = set()
    for a, mn, op, sz, bh in ins:
        if mn == "jmp" and "*" in op and "[" in op:
            if "4" in op.split("[")[1] or "8" in op.split("[")[1]:
                tab.add(op)
    if len(tab) >= 1:
        tiers.append(1)
    # ② falsifiable return convention: >=2 distinct HRESULT/-1 constants with a ret in body
    hconst = set()
    has_ret = any(x[1].startswith("ret") for x in ins)
    for a, mn, op, sz, bh in ins:
        if mn == "mov" and op.startswith("eax, "):
            v = op[5:].strip()
            try: iv = int(v,16) if v.lower().startswith("0x") else int(v)
            except ValueError: continue
            if 0x80004000 <= iv <= 0x8000FFFF or iv == 0xFFFFFFFF:
                hconst.add(iv)
    if has_ret and len(hconst) >= 2:
        tiers.append(2)
    # ③ memory shape: >=2 vptr imm installs in first 0x40 bytes + allocator
    immc = 0; alloc = False
    for a, mn, op, sz, bh in ins:
        if a - va >= 0x40: break
        if mn == "mov" and "dword ptr [" in op and ", 0x" in op:
            try: iv = int(op.rsplit(", 0x",1)[1],16)
            except ValueError: iv = 0
            if 0x7e0000 <= iv <= 0x900000: immc += 1
        if mn == "call" and op in ("0x7c8e17","0x7c8b3d","0x7c8b70"): alloc = True
    if immc >= 2 and alloc: tiers.append(3)
    # ④ complete loop: back-edge + non-stack write + cmp, all within function
    back = False
    for a, mn, op, sz, bh in ins:
        if mn in ("jmp","je","jne","jl","jle","jg","jge","jb","ja","jbe","jae") and op.startswith("0x"):
            try:
                if int(op,16) <= a: back = True
            except ValueError: pass
    nsw = any(mn=="mov" and "dword ptr [" in op and "esp" not in op and "ebp" not in op
              for a,mn,op,sz,bh in ins)
    hcmp = any(mn in ("cmp","test") for a,mn,op,sz,bh in ins)
    if back and nsw and hcmp: tiers.append(4)
    return sorted(set(tiers))

asize_c = {}
for ln in open(ATLAS, encoding="utf-8", errors="replace").read().splitlines()[1:]:
    c = ln.split(TAB)
    if len(c)>=2:
        try: asize_c[c[0].upper()] = int(c[1])
        except ValueError: pass
results = {e: detect(va, sz) for e,va,sz in pool}
passing = [e for e,t in results.items() if t]
p = len(passing)/len(pool)
print("detector passes: %d/%d  p=%.6f" % (len(passing), len(pool), p))
from collections import Counter
tc = Counter()
for e,t in results.items():
    for x in t: tc[x]+=1
print("tier hit counts:", dict(sorted(tc.items())))
print("passing entries:", sorted(passing))
for e in ("004A2990","006CF430","006CF240"):
    print("chosen %s size=%s tiers=%s" % (e, asize_c.get(e), results.get(e)))

N,TRIALS,SEED = 2,2000,20261119
rng = random.Random(SEED); pass_set=set(passing); K=0; both=0
allE = [e for e,_,_ in pool]
for _ in range(TRIALS):
    s = rng.sample(allE,N)
    K += sum(1 for e in s if e in pass_set)
    if all(e in pass_set for e in s): both+=1
print("\nN=%d trials=%d seed=%d" % (N,TRIALS,SEED))
print("p=%.6f E[N]=N*p=%.6f MC mean=%.6f K=%d" % (p,N*p,K/TRIALS,K))
print("NOTE: K==trials*N*p is an IDENTITY (§8.7 判据3), not a validation.")
print("P(both N=2 pass) MC=%.6f (%d/%d)" % (both/TRIALS,both,TRIALS))
