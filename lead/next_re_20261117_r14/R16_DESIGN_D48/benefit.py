"""收益侧：两条路的可达上限（只读）。
 A. 「若链闭合」（需要逐站点寄存器溯源）：1,279 无④ 行里，有多少 entry 曾经出现在
    「某个有 call [reg+disp] 站点的 disp」对应的活表槽位上 —— 这是上界，不含可达性。
 B. 「降级形态」（单值偏移）：见 confirm.py / disp_stats.tsv，实为 ≤2。
 C. 逐类分布：这 A 集合按 4GAP 的来源类别与名字形态分布。
"""
import sys, os, collections, json
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan

img = plan.Image(plan.EXE)
text = plan.Text(img)
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

base_only = [s for s in text.sites if s['base'] and not s['index'] and s['base'] not in ('esp', 'ebp')]
disps = set(s['disp'] for s in base_only)
print('live tables=%d  distinct disp=%d' % (len(live), len(disps)))

# A. 每个 disp 上的全部 entry（不分唯一性）
entries_by_disp = collections.defaultdict(set)
for vt, m in maps.items():
    for d, e in m.items():
        if d in disps:
            entries_by_disp[d].add(e)
all_e = set()
for s in entries_by_disp.values():
    all_e |= s
print('entries reachable via ANY dispatched offset =', len(all_e))

cov = plan.load_coverage()
cov_by_entry = {int(r['entry'], 16): r for r in cov}
PROVED = '[' + plan.PROVED + ']'
proved = [r for r in cov if r['grade'] == PROVED]
no4 = [r for r in proved if plan.RING4 not in r['sem']]
no4_set = {int(r['entry'], 16) for r in no4}

hit = no4_set & all_e
print('no4 rows=%d  of which entry is on a dispatched offset = %d (%.2f%%)'
      % (len(no4), len(hit), 100.0 * len(hit) / len(no4)))

# C. 分布
by_sub = collections.Counter(cov_by_entry[e]['sub'] for e in hit)
print('by subsystem:', by_sub.most_common())
pat = collections.Counter()
for e in hit:
    nm = cov_by_entry[e]['name']
    if '::slot' in nm or '::vslot' in nm:
        pat['Class::slotN 占位名'] += 1
    elif nm.startswith('sub_'):
        pat['sub_XXXXXXXX'] += 1
    else:
        pat['真名'] += 1
print('name form:', pat.most_common())

# 每个 disp 支持多少个 entry（说明「一个 disp 通常对应很多 entry」）
mult = collections.Counter(len(s) for s in entries_by_disp.values())
print('per-disp entry multiplicity histogram (top):', sorted(mult.items())[:12], '... max', max(mult))

# 另外：如果只要求「该 disp 的 entry 集合 = 1 张表的那个值」（即 holder 唯一性）
#       与「值唯一」的差别，见 disp_stats.tsv 的两列。

# 若链闭合，需要在多少个站点上做静态溯源才能吃到这些行？
need_sites = collections.defaultdict(int)
for s in base_only:
    need_sites[s['disp']] += 1
d_needed = set()
for e in hit:
    for d, es in entries_by_disp.items():
        if e in es:
            d_needed.add(d)
print('disp values that would have to be resolved for the A-set: %d' % len(d_needed))
print('call sites under them: %d' % sum(need_sites[d] for d in d_needed))
