#!/usr/bin/env python3
"""Random baseline per R14_COMMON §8.6 clause 4 + task spec.
Pool = S03 [静态推断] rows in coverage.tsv (same subsystem, same grade band).
For every pool row classify:
  ④ = has >=1 direct call site (whole-.text E8 target table, independent of atlas)
  ③b = byte-level detector firing for at least one of the 4 tiers (documented below).
Then compute K=#(④∧③b), analytical E[hits in 7 draws]=7*K/N, and Monte Carlo
(seed=20261119, 2000 draws of 7 without replacement) — report mean hit count.
NOTE: NOT the "random VA hits target" address-arithmetic method (§8.6 clause 4 forbids)."""
import struct, random, json, re
from collections import Counter
from common import DATA, IB, TEXT_VA, TEXT_END, va2off, _MD, capstone

COV = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv"
ATLAS = r"D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv"

# --- load S03 [静态推断] pool ---
pool = []
with open(COV, encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) < 5: continue
        if c[1].strip() == 'S03' and '[静态推断]' in c[4]:
            try: pool.append(int(c[0], 16))
            except Exception: pass
pool = sorted(set(pool))
print(f"S03 [静态推断] pool size N={len(pool)}")

# --- atlas sizes (window bounds only; ret verified separately) ---
size = {}
with open(ATLAS, encoding='utf-8', errors='replace') as f:
    f.readline()
    for line in f:
        c = line.rstrip('\n').split('\t')
        if len(c) < 2: continue
        try: size[int(c[0],16)] = int(c[1])
        except Exception: pass

# --- whole-.text direct-call target set (independent of atlas) ---
off = va2off(TEXT_VA); buf = DATA[off:off+(TEXT_END-TEXT_VA)]
call_targets = Counter()
for ins in _MD.disasm(buf, TEXT_VA):
    if ins.mnemonic == 'call' and ins.size == 5 and ins.bytes[0] == 0xE8:
        rel = struct.unpack('<i', ins.bytes[1:5])[0]
        call_targets[ins.address + 5 + rel] += 1

# vt immediate set = all 4-byte values at [vt-4-? ] ... simpler: collect COL-validated vt bases
vt_set = set()
from common import _pe
RDATA_LO, RDATA_HI = IB + _pe.sections[1].VirtualAddress, IB + _pe.sections[1].VirtualAddress + _pe.sections[1].Misc_VirtualSize
# collect immediate values written to memory that lie in .rdata (candidate vt writes)
vt_imm = Counter()
for ins in _MD.disasm(buf, TEXT_VA):
    if ins.mnemonic == 'mov' and len(ins.bytes) >= 6 and ins.operands and ins.operands[0].type == capstone.x86.X86_OP_MEM:
        imm = struct.unpack('<I', ins.bytes[-4:])[0]
        if RDATA_LO <= imm < RDATA_HI:
            vt_imm[imm] += 1
vt_set = set(vt_imm)

def body_insns(entry):
    sz = size.get(entry, 0)
    if not sz: return []
    return list(_MD.disasm(DATA[va2off(entry):va2off(entry)+sz], entry))

def detect_3b(entry):
    """Return set of tiers fired among {'①','②','③','④'}."""
    insns = body_insns(entry)
    if not insns: return set()
    tiers = set()
    addrs = [i.address for i in insns]
    # T1: jump table (indirect jmp with index reg) OR >=3 distinct jcc targets in body
    has_jmptbl = False
    jcc_targets = set()
    for i in insns:
        if i.mnemonic == 'jmp':
            for op in i.operands:
                if op.type == capstone.x86.X86_OP_MEM and op.mem.index != 0:
                    has_jmptbl = True
        if i.mnemonic.startswith('j') and i.mnemonic != 'jmp' and i.operands:
            op = i.operands[0]
            if op.type == capstone.x86.X86_OP_IMM and op.imm in addrs:
                jcc_targets.add(op.imm)
    if has_jmptbl or len(jcc_targets) >= 3:
        tiers.add('①')
    # T2: falsifiable return convention: a call whose eax is tested within 6 insns,
    # and >=2 distinct ret with different eax-setting (xor eax,eax / mov eax,imm / sbb)
    tested_call = False
    eax_set_kinds = set()
    for n, i in enumerate(insns):
        if i.mnemonic == 'call' and any(x.mnemonic in ('test','cmp') for x in insns[n+1:n+7]
                                        if x.operands and x.operands[0].type == capstone.x86.X86_OP_REG
                                        and x.operands[0].reg == capstone.x86.X86_REG_EAX):
            tested_call = True
        if i.mnemonic == 'xor' and len(i.operands)==2 and i.operands[0].reg==capstone.x86.X86_REG_EAX and i.operands[1].reg==capstone.x86.X86_REG_EAX:
            eax_set_kinds.add('zero')
        if i.mnemonic == 'mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_REG and i.operands[0].reg==capstone.x86.X86_REG_EAX and i.operands[1].type==capstone.x86.X86_OP_IMM:
            eax_set_kinds.add('imm')
        if i.mnemonic in ('sbb','or') and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_REG and i.operands[0].reg==capstone.x86.X86_REG_EAX:
            eax_set_kinds.add('sbbor')
    if tested_call and len(eax_set_kinds) >= 2:
        tiers.add('②')
    # T3: memory-shape: >=2 distinct vt-immediate writes OR >=10 distinct field-disp writes
    vtw = set(); fieldw = set()
    for i in insns:
        if i.mnemonic == 'mov' and len(i.operands)==2 and i.operands[0].type==capstone.x86.X86_OP_MEM:
            m = i.operands[0].mem
            if i.operands[1].type == capstone.x86.X86_OP_IMM:
                if i.operands[1].imm in vt_set: vtw.add(i.operands[1].imm)
            fieldw.add((m.base, m.disp))
    if len(vtw) >= 2 or len(fieldw) >= 10:
        tiers.add('③')
    # T4: complete I/O loop: backward branch in body AND >=1 call AND >=1 memory operand
    has_back = False; has_call = False; has_mem = False
    for i in insns:
        if i.mnemonic in ('call',): has_call = True
        if any(o.type==capstone.x86.X86_OP_MEM for o in i.operands): has_mem = True
        if i.mnemonic.startswith('j') and i.operands and i.operands[0].type==capstone.x86.X86_OP_IMM:
            if i.operands[0].imm <= i.address: has_back = True
    if has_back and has_call and has_mem:
        tiers.add('④')
    return tiers

rows = []
for e in pool:
    t = detect_3b(e)
    d4 = call_targets.get(e, 0) > 0
    rows.append({'entry': f"{e:08X}", 'ring4': d4, 'n_direct': call_targets.get(e,0),
                 'tiers': ''.join(sorted(t)), 'ring3b': bool(t), 'hit': bool(t and d4)})

K = sum(1 for r in rows if r['hit'])
n4 = sum(1 for r in rows if r['ring4'])
n3 = sum(1 for r in rows if r['ring3b'])
N = len(rows)
print(f"④ rows={n4}, ③b rows={n3}, ④∧③b rows K={K}, N={N}")
print(f"base rate p=K/N={K}/{N}={K/N:.6f}; analytical E[7]=7*p={7*K/N:.4f}")
print("tier distribution:", Counter(r['tiers'] for r in rows))

# Monte Carlo: seed 20261119, 2000 draws of 7 without replacement
random.seed(20261119)
hits_list = []
for _ in range(2000):
    sample = random.sample(rows, 7)
    hits_list.append(sum(1 for r in sample if r['hit']))
mc_mean = sum(hits_list)/len(hits_list)
print(f"MC(seed=20261119,2000 draws of 7): mean={mc_mean:.4f}; "
      f"distribution={dict(sorted(Counter(hits_list).items()))}")

# also report target rows' detector result for consistency
targets = [0x0065CAC0,0x004324B0,0x00552490,0x006C9890,0x00631CC0,0x0065D150,0x00431E80]
for t in targets:
    tt = detect_3b(t)
    print(f"  target {t:08X}: ④ n_direct={call_targets.get(t,0)} tiers={''.join(sorted(tt))}")

base = r"D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\S03_C4"
json.dump({'pool_size':N,'ring4_rows':n4,'ring3b_rows':n3,'K':K,'base_rate':K/N,
           'analytical_E7':7*K/N,'mc_seed':20261119,'mc_draws':2000,'mc_mean':mc_mean,
           'mc_distribution':{str(k):v for k,v in sorted(Counter(hits_list).items())},
           'tier_distribution':{k:v for k,v in Counter(r['tiers'] for r in rows).items()},
           'rows':rows},
          open(base + r"\EVIDENCE\random_baseline.json",'w',encoding='utf-8'), indent=2)
print("wrote random_baseline.json")
