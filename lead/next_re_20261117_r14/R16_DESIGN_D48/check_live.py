"""两件校验：
 1. 活/死表判据能否复现已入账的实证（R14_COMMON §8.1 ㉓：死表 007E43E8 @ 004E6B28，活表 007E43C8 @ 004E6AFD）；
 2. A 集（317 行）在 85 个 disp 上的聚集，以及每个 disp 的 entry 多重度。
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

print('=== 1. 活/死表判据复核（㉓ 实证对照）===')
print('atexit-registered functions detected:', len(text.atexit_fn))
for vt in (0x7E43C8, 0x7E43E8, 0x7EC1D4):
    ins = text.stores.get(vt, [])
    print('\n vt %08X  in_tables=%s  install sites=%d  cls=%s'
          % (vt, vt in mine, len(ins), mine.get(vt, {}).get('cls')))
    for site, disp in ins:
        fn = plan.body_of(asz, starts, site)
        print('   site %08X  fn=%s  atexit=%s  obj_disp=%s'
              % (site, ('%08X' % fn) if fn else '-', (fn in text.atexit_fn) if fn else '?',
                 hex(disp) if disp is not None else '?'))

# 全体统计：装表点落在 atexit 函数体内的比例
n_all = n_atexit = n_unknown = 0
tabs_dead_only = []
for vt in mine:
    ins = text.stores.get(vt, [])
    if not ins:
        continue
    prov = []
    for site, _ in ins:
        fn = plan.body_of(asz, starts, site)
        if fn is None:
            prov.append('unknown')
        elif fn in text.atexit_fn:
            prov.append('atexit')
        else:
            prov.append('ctor')
    n_all += len(prov)
    n_atexit += prov.count('atexit')
    n_unknown += prov.count('unknown')
    if prov and all(p == 'atexit' for p in prov):
        tabs_dead_only.append(vt)
print('\ninstall sites total=%d  atexit-provenance=%d  outside-atlas(unknown)=%d' % (n_all, n_atexit, n_unknown))
print('tables whose every install is atexit-provenance (dead-only) = %d' % len(tabs_dead_only))
for vt in tabs_dead_only[:10]:
    print('   dead-only %08X %s' % (vt, mine[vt]['cls']))

print('\n=== 2. A 集（317 行）按 disp 聚集 ===')
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
base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
disps = set(s['disp'] for s in base_only)
entries_by_disp = collections.defaultdict(set)
for vt, m in maps.items():
    for d, e in m.items():
        if d in disps:
            entries_by_disp[d].add(e)

cov = plan.load_coverage()
cov_by_entry = {int(r['entry'], 16): r for r in cov}
PROVED = '[' + plan.PROVED + ']'
no4 = [r for r in cov if r['grade'] == PROVED and plan.RING4 not in r['sem']]
no4_set = {int(r['entry'], 16) for r in no4}
hit = no4_set & set().union(*entries_by_disp.values())
print('hit rows =', len(hit))

per_disp = collections.Counter()
for d, es in entries_by_disp.items():
    n = len(es & no4_set)
    if n:
        per_disp[d] = n
print('distinct disps carrying a hit:', len(per_disp))
for d, n in per_disp.most_common(15):
    print('  disp %08X (slot %3d): %3d hit rows, %4d entries at that offset'
          % (d, d // 4, n, len(entries_by_disp[d])))
print('\ndisp 0 detail: entries at offset 0 =', len(entries_by_disp.get(0, ())),
      'hit rows =', len(entries_by_disp.get(0, set()) & no4_set))
