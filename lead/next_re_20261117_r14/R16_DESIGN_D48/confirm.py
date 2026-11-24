"""边界确认：从每个 atlas 函数入口做递归下降，标出「真指令边界」集合；
然后用它给 `call [reg+disp]` 站点去伪（线性 sweep 会把数据字节误当指令）。
另：更稳健的帧指针统计（前 8 条指令窗口 + 字节加权）。
只读。
"""
import sys, os, collections, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan
import capstone
from capstone import x86 as X

img = plan.Image(plan.EXE)
text = plan.Text(img)
atlas = plan.load_atlas()
t = img.section('.text')
code = t['data']
LO = t['va']
md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
md.detail = True

base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
site_va = set(s['va'] for s in base_only)
starts = sorted(atlas)
asz = [atlas[s] for s in starts]

# 只对「含站点」的函数做递归下降（省时间），其余函数不影响结论
need = set()
for s in base_only:
    f = plan.body_of(asz, starts, s['va'])
    if f is not None:
        need.add(f)
print('functions containing base-only sites:', len(need), '/', len(atlas))

confirmed = set()
bad = 0
for entry in need:
    size = atlas[entry]
    end = entry + size
    work = [entry]
    seen = set()
    guard = 0
    while work and guard < 200000:
        guard += 1
        a = work.pop()
        while entry <= a < end:
            if a in seen:
                break
            seen.add(a)
            o = a - LO
            ins = next(md.disasm(code[o:o + 15], a), None)
            if ins is None or ins.size == 0:
                bad += 1
                break
            confirmed.add(a)
            nx = a + ins.size
            mn = ins.mnemonic
            ops = ins.operands
            if mn == 'ret' or mn == 'retf' or mn == 'int3':
                break
            if mn == 'jmp' and ops and ops[0].type == X.X86_OP_IMM:
                tgt = ops[0].imm & 0xFFFFFFFF
                if entry <= tgt < end:
                    work.append(tgt)
                break
            if mn.startswith('j') and ops and ops[0].type == X.X86_OP_IMM:
                tgt = ops[0].imm & 0xFFFFFFFF
                if entry <= tgt < end:
                    work.append(tgt)
                a = nx
                continue
            a = nx

in_atlas = [s for s in base_only if plan.body_of(asz, starts, s['va']) is not None]
ok = [s for s in in_atlas if s['va'] in confirmed]
print('base_only=%d  in_atlas=%d  descent-confirmed=%d (%.2f%% of in_atlas)  undecodable=%d'
      % (len(base_only), len(in_atlas), len(ok), 100.0 * len(ok) / max(1, len(in_atlas)), bad))

# 用确认过的站点重算关键数（与 plan.py 同口径）
mine = plan.enumerate_tables(img, text)
stop = set(mine)
for vt, tb in mine.items():
    tb['n_slots'] = plan.table_len(img, vt, stop)
installs = collections.defaultdict(int)
for imm, lst in text.stores.items():
    if imm in mine:
        installs[imm] += len(lst)
live = [vt for vt in mine if installs.get(vt)]
maps = {}
for vt in live:
    m = {}
    for k in range(mine[vt]['n_slots']):
        v = img.u32(vt + k * 4)
        if v is not None and plan.TEXT_LO <= v < plan.TEXT_HI:
            m[k * 4] = v
    maps[vt] = m

for label, sites in (('linear-sweep', base_only), ('descent-confirmed', ok)):
    by = collections.defaultdict(int)
    for s in sites:
        by[s['disp']] += 1
    strict = []
    vuniq = []
    for d, n in by.items():
        ents = collections.Counter()
        holders = 0
        for vt, m in maps.items():
            if d in m:
                ents[m[d]] += 1
                holders += 1
        if holders == 1:
            strict.append((d, list(ents)[0]))
        if len(ents) == 1:
            vuniq.append((d, list(ents)[0], holders))
    cov = plan.load_coverage()
    proved = {int(r['entry'], 16) for r in cov if r['grade'] == '[' + plan.PROVED + ']'}
    no4 = {int(r['entry'], 16) for r in cov if r['grade'] == '[' + plan.PROVED + ']'
           and plan.RING4 not in r['sem']}
    print('\n[%s] sites=%d distinct_disp=%d strict=%d value_uniq=%d proved=%d proved_no4=%d'
          % (label, len(sites), len(by), len(strict), len(vuniq),
             sum(1 for _, e, _ in vuniq if e in proved),
             sum(1 for _, e, _ in vuniq if e in no4)))
    print('   strict:', [('%08X' % d, '%08X' % e) for d, e in strict])
    print('   no4 hits:', [('%08X' % d, '%08X' % e) for d, e, h in vuniq if e in no4])

# ---------------------------------------------------------------- 帧指针（稳妥版）
print('\n=== prologue (window=8, byte-weighted) ===')
stat = collections.Counter()
bytes_ = collections.Counter()
for entry, size in atlas.items():
    o = entry - LO
    ins = []
    for k, i in enumerate(md.disasm(code[o:o + 40], entry)):
        ins.append(i)
        if k >= 7:
            break
    mn = [(i.mnemonic, i.op_str) for i in ins]
    fp = False
    for k in range(len(mn) - 1):
        if mn[k] == ('push', 'ebp') and mn[k + 1][0] == 'mov' and mn[k + 1][1] == 'ebp, esp':
            fp = True
            break
    if fp:
        stat['has_ebp_frame'] += 1
        bytes_['has_ebp_frame'] += size or 0
    else:
        stat['no_ebp_frame'] += 1
        bytes_['no_ebp_frame'] += size or 0
for k in ('has_ebp_frame', 'no_ebp_frame'):
    print('  %-16s functions %5d (%.2f%%)  bytes %8d (%.2f%%)'
          % (k, stat[k], 100.0 * stat[k] / len(atlas), bytes_[k],
             100.0 * bytes_[k] / sum(bytes_.values())))
