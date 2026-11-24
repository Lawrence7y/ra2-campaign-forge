"""核验：我的表枚举 / 表长 与盘上既有 canonical 产物逐表对比；并取出关键命中行。
只读。"""
import sys, os, json, collections
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan

HERE = os.path.dirname(os.path.abspath(__file__))
CANON = r'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\vtables_canonical.json'
VT_TABLES = r'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\P0_CLOSE\vt_tables.tsv'

img = plan.Image(plan.EXE)
text = plan.Text(img)
mine = plan.enumerate_tables(img, text)
stop = set(mine)
for vt, t in mine.items():
    t['n_slots'] = plan.table_len(img, vt, stop)

canon = json.load(open(CANON, encoding='utf-8'))['vtables']
cset = set(v['vt'] for v in canon)
mine_set = set(mine)
print('mine %d  canonical %d  common %d' % (len(mine), len(cset), len(mine_set & cset)))
print('mine-only:', ['%08X' % v for v in sorted(mine_set - cset)][:20])
print('canon-only:', ['%08X' % v for v in sorted(cset - mine_set)][:20])

nl = {}
with open(VT_TABLES, encoding='utf-8-sig') as f:
    for i, ln in enumerate(f):
        if i == 0:
            continue
        c = ln.rstrip('\n').split('\t')
        if len(c) >= 2:
            nl[int(c[0], 16)] = int(c[1])
print('vt_tables n=%d' % len(nl))
diff = collections.Counter()
for vt in sorted(mine_set & set(nl)):
    diff[mine[vt]['n_slots'] - nl[vt]] += 1
print('slot-length delta (mine - canon) histogram:', diff.most_common(10))
big = [(vt, mine[vt]['n_slots'], nl[vt]) for vt in mine_set & set(nl) if mine[vt]['n_slots'] != nl[vt]]
print('n tables with different length =', len(big))
for vt, a, b in sorted(big, key=lambda x: -abs(x[1] - x[2]))[:10]:
    print('  %08X mine=%d canon=%d  %s' % (vt, a, b, mine[vt]['cls']))

# 用 canonical 表长重算「每 disp 恰好 1 张表 / 值唯一」
cov = plan.load_coverage()
cov_by_entry = {int(r['entry'], 16): r for r in cov}
PROVED = '[' + plan.PROVED + ']'

live = set(mine)   # 下面按装表点判活（与 plan.py 同法）
installs = collections.defaultdict(list)
for imm, lst in text.stores.items():
    if imm in mine:
        installs[imm].extend(lst)
atlas = plan.load_atlas()
starts = sorted(atlas)
asz = [atlas[s] for s in starts]
for vt in mine:
    if installs.get(vt):
        mine[vt]['live'] = True
live_tabs = sorted(vt for vt in mine if mine[vt].get('live'))

def slots(vt, n):
    out = {}
    for k in range(n):
        v = img.u32(vt + k * 4)
        if v is not None and plan.TEXT_LO <= v < plan.TEXT_HI:
            out[k * 4] = v
    return out

maps_mine = {vt: slots(vt, mine[vt]['n_slots']) for vt in live_tabs}
maps_canon = {vt: slots(vt, nl.get(vt, mine[vt]['n_slots'])) for vt in live_tabs}

base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
by = collections.defaultdict(list)
for s in base_only:
    by[s['disp']].append(s)

for name, mp in (('mine-len', maps_mine), ('canon-len', maps_canon)):
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
    no4 = {int(r['entry'], 16) for r in cov if r['grade'] == PROVED and plan.RING4 not in r['sem']}
    proved = {int(r['entry'], 16) for r in cov if r['grade'] == PROVED}
    print('\n[%s] strict=%d value-uniq=%d  hit proved=%d hit proved-no4=%d'
          % (name, len(strict), len(vuniq),
             sum(1 for _, e, _ in vuniq if e in proved),
             sum(1 for _, e, _ in vuniq if e in no4)))
    if name == 'mine-len':
        print(' strict disp(s):', [('%08X' % d, '%08X' % e) for d, e in strict])
        hits = [(d, e, h) for d, e, h in vuniq if e in no4]
        print(' value-uniq hits on proved-no4:')
        for d, e, h in hits:
            r = cov_by_entry[e]
            print('   disp=%08X entry=%08X holders=%d  %s %s | %s'
                  % (d, e, h, r['sub'], r['name'], r['sem'][:70]))
