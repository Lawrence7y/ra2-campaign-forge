"""口径敏感性：宽（所有有 imm 装表点的 RTTI 表）/ 窄（装表点落在已知非 atexit 函数内）。
对两种口径分别算 strict / value 两个判据，看结论是否翻转。只读。
"""
import sys, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan

img = plan.Image(plan.EXE)
text = plan.Text(img)
mine = plan.enumerate_tables(img, text)
stop = set(mine)
for vt in mine:
    mine[vt]['n_slots'] = plan.table_len(img, vt, stop)
atlas = plan.load_atlas()
starts = sorted(atlas)
asz = [atlas[s] for s in starts]

installs = collections.defaultdict(list)
for imm, lst in text.stores.items():
    if imm in mine:
        installs[imm].extend(lst)

wide, narrow, n_ctor = [], [], 0
for vt, ins in installs.items():
    wide.append(vt)
    ok = False
    for site, _ in ins:
        fn = plan.body_of(asz, starts, site)
        if fn is not None and fn not in text.atexit_fn:
            ok = True
            n_ctor += 1
            break
    if ok:
        narrow.append(vt)
print('tables: all-with-install(wide)=%d  ctor-provenance(narrow)=%d' % (len(wide), len(narrow)))
print('install sites inside known non-atexit funcs =', n_ctor)

def maps_for(tabs):
    out = {}
    for vt in tabs:
        m = {}
        for k in range(mine[vt]['n_slots']):
            v = img.u32(vt + k * 4)
            if v is not None and plan.TEXT_LO <= v < plan.TEXT_HI:
                m[k * 4] = v
        out[vt] = m
    return out

base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
by = collections.defaultdict(int)
for s in base_only:
    by[s['disp']] += 1

cov = plan.load_coverage()
cov_by_entry = {int(r['entry'], 16): r for r in cov}
PROVED = '[' + plan.PROVED + ']'
proved = {int(r['entry'], 16) for r in cov if r['grade'] == PROVED}
no4 = {int(r['entry'], 16) for r in cov if r['grade'] == PROVED and plan.RING4 not in r['sem']}

for label, tabs in (('wide(所有装表点)', wide), ('narrow(ctor 内装表)', narrow)):
    mp = maps_for(tabs)
    strict, vuniq = [], []
    for d in by:
        ents = collections.Counter()
        holders = 0
        for vt, m in mp.items():
            if d in m:
                ents[m[d]] += 1
                holders += 1
        if holders == 1:
            strict.append((d, list(ents)[0]))
        if len(ents) == 1:
            vuniq.append((d, list(ents)[0], holders))
    print('\n[%s] tables=%d strict=%d value_uniq=%d' % (label, len(tabs), len(strict), len(vuniq)))
    print('   strict disps:', [('%08X' % d, '%08X' % e) for d, e in strict])
    print('   value-uniq -> proved=%d  proved_no4=%d'
          % (sum(1 for _, e, _ in vuniq if e in proved),
             sum(1 for _, e, _ in vuniq if e in no4)))
    print('   no4 hits:', [('%08X' % d, '%08X' % e) for d, e, _ in vuniq if e in no4])

# 每个 disp 的 holders 分布（宽口径），说明「严格判据为什么只命中 1 个」
mp = maps_for(wide)
hd = collections.Counter()
for d in by:
    holders = sum(1 for vt, m in mp.items() if d in m)
    hd[holders] += 1
print('\nholders histogram (wide):', sorted(hd.items())[:16], '...')
print('disps with exactly 1 holder:', hd[1], ' with 2:', hd[2])
