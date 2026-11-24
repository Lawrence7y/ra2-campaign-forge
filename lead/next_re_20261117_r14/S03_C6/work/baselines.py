"""③b random baseline over S03 [静态推断] pool.
seed 20261119, 2000 trials, sample 8 rows without replacement.
Pool = coverage.tsv S03 grade [静态推断] AND entry in classification (has extent).
Detector tiers (照 D-42 / R14_COMMON 8.6 条3 / C5 baselines.py):
  loose  : ③b① includes D-42 detail#1 (>=3 mutually-exclusive jcc guards, >=3 distinct
           taken targets, >=3 distinct guard sites) OR jumptable; plus ③b②③④.
  strict : ③b① only jumptable (indirect jmp with index scale); plus ③b②③④.
Report K=pool rows passing, p=K/N, E[8]=8*p, MC mean. Identity K_report = 8*mean(=p).
"""
import os, sys, json, csv, random
sys.path.insert(0, os.path.dirname(__file__))
import common as C

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"

pool = []
for line in open(COV, encoding="utf-8"):
    p = line.rstrip("\n").split("\t")
    if len(p) >= 8 and p[1] == 'S03' and (p[4] == '[静态推断]' or '静态' in p[4]):
        pool.append(p[0])
ext = {}
for r in csv.DictReader(open(CLS, encoding="utf-8"), delimiter="\t"):
    try: ext[r['entry']] = (int(r['ext_lo'],16), int(r['ext_hi'],16))
    except Exception: pass
pool = [e for e in pool if e in ext]
print("pool N =", len(pool))

def get_insns(entry):
    lo, hi = ext[entry]; off = C.va2off(lo); size = hi - lo
    if off is None or size <= 0: return []
    return list(C.md().disasm(C._data[off:off+size], lo))

def has_jumptable(insns):
    for i in insns:
        if i.mnemonic == 'jmp' and 'dword ptr' in i.op_str and '*' in i.op_str:
            return True
    return False

def has_guard_chain_loose(insns):
    guards = []
    for i in insns:
        if i.mnemonic.startswith('j') and i.mnemonic != 'jmp':
            try: t = int(i.op_str, 16)
            except Exception: continue
            guards.append((i.address, t, i.mnemonic))
    if len(guards) < 3: return False
    if len(set(t for _,t,_ in guards)) < 3: return False
    if len(set(a for a,_,_ in guards)) < 3: return False
    return True

def has_errcode(insns):
    for j,i in enumerate(insns):
        if i.mnemonic == 'cmp' and i.op_str.strip().endswith('-1'):
            for k in insns[j+1:j+6]:
                if k.mnemonic.startswith('ret') or k.mnemonic.startswith('set') or k.mnemonic.startswith('j'):
                    return True
    return False

def has_ioloop(insns):
    back = False; io = False
    for i in insns:
        if i.mnemonic.startswith('j') and i.mnemonic != 'jmp':
            try:
                t = int(i.op_str,16)
                if t <= i.address: back = True
            except Exception: pass
        if i.mnemonic == 'call': io = True
    return back and io and len(insns) >= 20

def has_memshape(insns):
    vtwrites = 0
    for i in insns:
        if i.mnemonic == 'mov' and 'dword ptr' in i.op_str and ('0x7e' in i.op_str or '0x7f' in i.op_str):
            vtwrites += 1
    return vtwrites >= 2

def detect(entry, tier):
    insns = get_insns(entry)
    if not insns: return False, {}
    common3 = has_errcode(insns) or has_ioloop(insns) or has_memshape(insns)
    jt = has_jumptable(insns)
    b1 = jt if tier == 'strict' else (jt or has_guard_chain_loose(insns))
    feats = {'jumptable':jt, 'guardchain_loose':has_guard_chain_loose(insns),
             'errcode':has_errcode(insns), 'ioloop':has_ioloop(insns),
             'memshape':has_memshape(insns), 'n_insn':len(insns)}
    return (b1 or common3), feats

res = {}
for tier in ('loose','strict'):
    passing = []
    for e in pool:
        ok, feat = detect(e, tier)
        if ok: passing.append(e)
    N = len(pool); K = len(passing); p = K/N; E8 = 8*p
    rnd = random.Random(20261119); trials = 2000; hits = 0
    pset = set(passing)
    for _ in range(trials):
        samp = rnd.sample(pool, 8)
        hits += sum(1 for e in samp if e in pset)
    mc = hits/trials
    res[tier] = {"N":N,"K":K,"p":p,"E8":E8,"mc_mean":mc,"passing":passing,
                 "identity_K_eq_rows_x_mean":{"rows":8,"mean":p,"rows_x_mean":8*p,
                 "K_report_E8":E8,"ok":abs(8*p-E8)<1e-12}}
    print("[%s] N=%d K=%d p=%.6f E[8]=%.6f MC_mean=%.6f K==8*p:%s" %
          (tier,N,K,p,E8,mc,abs(8*p-E8)<1e-12))

json.dump(res, open(os.path.join(os.path.dirname(__file__),"..","EVIDENCE","baselines.json"),"w",encoding="utf-8"), indent=2)
print("wrote EVIDENCE/baselines.json")
