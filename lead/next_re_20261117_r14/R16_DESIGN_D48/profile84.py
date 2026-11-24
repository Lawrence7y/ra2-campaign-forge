"""84 个「单值偏移」witness entry 的画像：grade / 名字形态 / 是否已含④。只读。"""
import sys, os, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan

cov = plan.load_coverage()
by = {int(r['entry'], 16): r for r in cov}
rows = []
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'disp_stats.tsv'),
          encoding='utf-8') as f:
    hdr = f.readline().rstrip('\n').split('\t')
    for ln in f:
        c = ln.rstrip('\n').split('\t')
        d = dict(zip(hdr, c))
        if d['unamb_value'] == 'Y':
            rows.append(d)
print('value-unique disps:', len(rows))
g = collections.Counter()
form = collections.Counter()
for d in rows:
    r = by.get(int(d['witness_entry'], 16))
    if not r:
        g['not-in-coverage'] += 1
        continue
    g[r['grade']] += 1
    nm = r['name']
    if '::slot' in nm or '::vslot' in nm:
        form['Class::slotN'] += 1
    elif nm.startswith('sub_'):
        form['sub_XXXXXXXX'] += 1
    else:
        form['真名'] += 1
print('grade:', g)
print('name form:', form)
print('has ④ already:', sum(1 for d in rows if by.get(int(d['witness_entry'], 16)) and
                            plan.RING4 in by[int(d['witness_entry'], 16)]['sem']))
print('\nthe 5 proved ones:')
for d in rows:
    e = int(d['witness_entry'], 16)
    r = by.get(e)
    if r and r['grade'] == '[' + plan.PROVED + ']':
        print('  disp=%s entry=%08X %-16s %s | ④=%s | sites=%s holders=%s'
              % (d['disp_hex'], e, r['sub'], r['name'],
                 'Y' if plan.RING4 in r['sem'] else 'N', d['n_sites'], d['n_tables_live']))
        print('     %s' % r['sem'][:120])
