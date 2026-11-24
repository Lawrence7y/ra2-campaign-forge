"""核验「结构性不可达 962 行」：用 my-walk 表长 与 P0_CLOSE 的 canonical n_slots 各算一遍。只读。"""
import sys, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan

img = plan.Image(plan.EXE)
text = plan.Text(img)
mine = plan.enumerate_tables(img)
stop = set(mine)
for vt in mine:
    mine[vt]['n_slots'] = plan.table_len(img, vt, stop)
nl = {}
with open(r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_CLOSE\vt_tables.tsv',
          encoding='utf-8-sig') as f:
    for i, ln in enumerate(f):
        if i == 0:
            continue
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 2:
            nl[int(c[0], 16)] = int(c[1])

installs = collections.defaultdict(int)
for imm, lst in text.stores.items():
    if imm in mine:
        installs[imm] += len(lst)
live = [vt for vt in mine if installs.get(vt)]
base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
disps = set(s['disp'] for s in base_only)

cov = plan.load_coverage()
PROVED = '[' + plan.PROVED + ']'
no4 = [r for r in cov if r['grade'] == PROVED and plan.RING4 not in r['sem']]
no4_set = {int(r['entry'], 16) for r in no4}
print('no4 rows = %d' % len(no4))

for label, lens in (('my-walk', lambda vt: mine[vt]['n_slots']),
                    ('canon', lambda vt: nl.get(vt, mine[vt]['n_slots']))):
    reach = set()
    for vt in live:
        n = lens(vt)
        for k in range(n):
            d = k * 4
            if d not in disps:
                continue
            v = img.u32(vt + d)
            if v is not None and plan.TEXT_LO <= v < plan.TEXT_HI:
                reach.add(v)
    hit = no4_set & reach
    print('[%s] reachable entries=%d  no4 hit=%d  structurally unreachable=%d (%.1f%%)'
          % (label, len(reach), len(hit), len(no4) - len(hit),
             100.0 * (len(no4) - len(hit)) / len(no4)))

# 这 962 行是什么：是否虚函数（有 vtable 槽持有）/名字形态
installs_all = collections.defaultdict(list)
for imm, lst in text.stores.items():
    if imm in mine:
        installs_all[imm].extend(lst)
holders = collections.defaultdict(list)
for vt in live:
    for k in range(mine[vt]['n_slots']):
        v = img.u32(vt + k * 4)
        if v is not None and plan.TEXT_LO <= v < plan.TEXT_HI:
            holders[v].append((vt, k * 4))
unreach = [e for e in no4_set if not any(d in disps for _, d in holders.get(e, []))]
print('\nunreachable rows=%d ; of which held by >=1 live vtable slot = %d ; by 0 = %d'
      % (len(unreach), sum(1 for e in unreach if holders.get(e)),
         sum(1 for e in unreach if not holders.get(e))))
form = collections.Counter()
for e in unreach:
    r = {int(x['entry'], 16): x for x in no4}.get(e)
    nm = r['name'] if r else '?'
    if '::slot' in nm or '::vslot' in nm:
        form['Class::slotN'] += 1
    elif nm.startswith('sub_'):
        form['sub_XXXXXXXX'] += 1
    else:
        form['真名'] += 1
print('name form of unreachable:', form)
