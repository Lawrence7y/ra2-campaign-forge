#!/usr/bin/env python3
"""③b detector implementing D-42 four tiers + rule#1 (multi-guard chain).
Used for (a) baseline strict/loose over S03 [静态推断] pool, (b) per-row feature report.
strict: ③b① = literal jump table only.  loose: ③b① += >=3 mutually-exclusive guard chain.
Both share ③b② error/return, ③b③ memory-shape, ③b④ I/O-loop.
"""
import sys, os, json, csv, random, struct
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
import common as C

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
CLS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\SURVEY_RING24\EVIDENCE\classification.tsv"
BASE = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C7"

# extents from classification (self-written CFG, not atlas)
ext = {}
for r in csv.DictReader(open(CLS, encoding='utf-8'), delimiter='\t'):
    try:
        ext[r['entry']] = (int(r['ext_lo'],16), int(r['ext_hi'],16))
    except Exception:
        pass

def insns_of(entry_hex):
    lo,hi = ext[entry_hex]
    return list(C.disasm_range(lo,hi))

def is_jcc(m):
    return m.startswith('j') and m not in ('jmp',) and not m.startswith('jmp')

def feat(insns):
    addrs = [i.address for i in insns]
    addrs_set = set(addrs)
    f = {'jumptable':False,'guard_chain':False,'errcode':False,'memshape':False,'ioloop':False,
         'n_jcc':0,'jcc_targets':[],'backedge':0,'n_insn':len(insns)}
    # ③b① jump table: indirect jmp with index register or dword ptr [reg*4]
    for i in insns:
        if i.mnemonic == 'jmp':
            if any(op.type==C.capstone.x86.X86_OP_MEM and op.mem.index!=0 for op in i.operands):
                f['jumptable']=True
            if 'dword ptr' in i.op_str and '*' in i.op_str:
                f['jumptable']=True
    # guard chain: collect jcc with in-body immediate targets
    tgts=[]; sites=[]
    for i in insns:
        if is_jcc(i.mnemonic) and i.operands and i.operands[0].type==C.capstone.x86.X86_OP_IMM:
            t=i.operands[0].imm
            if t in addrs_set:
                tgts.append(t); sites.append(i.address)
    f['n_jcc']=len(tgts); f['jcc_targets']=[f"0x{t:08X}" for t in tgts]
    distinct_tgts=set(tgts)
    # >=3 mutually exclusive guards: >=3 distinct jcc sites with >=3 distinct targets
    if len(sites)>=3 and len(distinct_tgts)>=3:
        f['guard_chain']=True
    # backward edges
    for i in insns:
        if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==C.capstone.x86.X86_OP_IMM:
            if i.operands[0].imm <= i.address:
                f['backedge']+=1
    # ③b② falsifiable error/return: (a) cmp/test against -1 or error const followed by jcc->ret/setcc;
    #   (b) GetLastError imported call; (c) tested callee result AND >=2 distinct return constructions.
    for j,i in enumerate(insns):
        o=i.op_str
        if (i.mnemonic=='cmp' and ('-1' in o or '0xd' in o.lower() or '0x9' in o.lower())):
            for k in insns[j+1:j+8]:
                if k.mnemonic.startswith('ret') or k.mnemonic.startswith('set') or is_jcc(k.mnemonic):
                    f['errcode']=True; break
        if i.mnemonic=='call' and '0x7e1200' in o:  # GetLastError
            f['errcode']=True
    # (c) falsifiable-return: a call whose eax is tested within 6 insns, plus >=2 distinct eax returns
    tested_call=False; ret_kinds=set()
    for n,i in enumerate(insns):
        if i.mnemonic=='call' and any(
              k.mnemonic in ('test','cmp') and k.operands and k.operands[0].type==C.capstone.x86.X86_OP_REG
              and k.operands[0].reg==C.capstone.x86.X86_REG_EAX
              for k in insns[n+1:n+7]):
            tested_call=True
        if i.mnemonic=='xor' and len(i.operands)==2 and i.operands[0].type==C.capstone.x86.X86_OP_REG \
           and i.operands[0].reg==C.capstone.x86.X86_REG_EAX and i.operands[1].reg==C.capstone.x86.X86_REG_EAX:
            ret_kinds.add('zero')
        if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==C.capstone.x86.X86_OP_REG \
           and i.operands[0].reg==C.capstone.x86.X86_REG_EAX and i.operands[1].type==C.capstone.x86.X86_OP_IMM:
            ret_kinds.add('imm')
        if i.mnemonic in ('shl','or','add','sbb') and len(i.operands)==2 \
           and i.operands[0].type==C.capstone.x86.X86_OP_REG and i.operands[0].reg==C.capstone.x86.X86_REG_EAX:
            ret_kinds.add('pack')
    if tested_call and len(ret_kinds)>=2:
        f['errcode']=True
    # ③b③ memory shape: >=2 writes of a known .rdata vt immed OR >=10 distinct field writes
    vtw=set(); fieldw=set()
    for i in insns:
        if i.mnemonic=='mov' and len(i.operands)==2 and i.operands[0].type==C.capstone.x86.X86_OP_MEM:
            m=i.operands[0].mem
            if i.operands[1].type==C.capstone.x86.X86_OP_IMM:
                v=i.operands[1].imm
                if 0x7e1000 <= v < 0x812000: vtw.add(v)
            if m.base is not None:
                fieldw.add((m.base, m.disp))
    if len(vtw)>=2 or len(fieldw)>=10: f['memshape']=True
    # ③b④ complete I/O loop: backedge + a call + memory operand (with boundary-ish cmp)
    has_call=any(i.mnemonic=='call' for i in insns)
    has_mem=any(any(op.type==C.capstone.x86.X86_OP_MEM for op in i.operands) for i in insns)
    if f['backedge']>=1 and has_call and has_mem:
        f['ioloop']=True
    return f

def passes(f, tier):
    b1 = f['jumptable'] or (tier=='loose' and f['guard_chain'])
    return b1 or f['errcode'] or f['memshape'] or f['ioloop']

# ---- baseline pool: S03 [静态推断] in coverage ----
pool=[]
for line in open(COV, encoding='utf-8', errors='replace'):
    p=line.rstrip('\n').split('\t')
    if len(p)>=5 and p[1]=='S03' and '[静态推断]' in p[4]:
        e=p[0].strip()
        if e in ext: pool.append(e)
pool=sorted(set(pool))
print("S03 [静态推断] pool N =",len(pool))

res={}
for tier in ('strict','loose'):
    passing=[]; feats={}
    for e in pool:
        f=feat(insns_of(e))
        feats[e]=f
        if passes(f,tier): passing.append(e)
    N=len(pool); K=len(passing); p=K/N; E8=8*p
    rnd=random.Random(20261119); trials=2000; hits=0; pset=set(passing)
    dist=Counter()
    for _ in range(trials):
        samp=rnd.sample(pool,8)
        h=sum(1 for e in samp if e in pset); hits+=h; dist[h]+=1
    mc=hits/trials
    res[tier]={'N':N,'K':K,'base_rate':p,'E8':E8,'mc_seed':20261119,'mc_draws':2000,
               'mc_mean':mc,'mc_dist':{str(k):v for k,v in sorted(dist.items())},
               'passing':passing}
    print(f"[{tier}] N={N} K={K} p={p:.6f} E[8]={E8:.4f} MCmean={mc:.4f}")

# per-row feature report for our 9 entries
TARGETS=['004325C0','00473C00','00473CE0','00473FC0','0047AAB0','00631D30','0065CCA0','0065D1F0','00432050']
rowrep={}
for e in TARGETS:
    f=feat(insns_of(e))
    rowrep[e]={'feat':f,'strict':passes(f,'strict'),'loose':passes(f,'loose')}
    print(f"ROW {e}: strict={passes(f,'strict')} loose={passes(f,'loose')} feat={f}")

json.dump({'baseline':res,'rows':rowrep}, open(BASE+r"\EVIDENCE\baselines.json",'w',encoding='utf-8'), indent=2)
print("wrote EVIDENCE/baselines.json")
