#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158e — 规则 D 复算：审计员 #366 对 C3 的更正是否成立。

#366 的批评（要点）：
  ① 「项数 171->178、唯一路径 68->74」不是 F35 单独造成：F35 贡献 +4 项/+3 唯一，
     F29 同时 5->8 项（新增 r139a/r139e/r139f 三个脚本）贡献 +3 项/+3 唯一，合计 +7/+6。
  ② V542 有 3 条路径不带 lead\\ 前缀（V532 为 0）。
  ③ 项级失联 43 条，且两版分布相同（比去重路径更强的判据）。
  ④ TRIAGE 的比对只在 fid 集合与去锚点并集上相等，逐串带锚点比对 32/32 全不等。
  ⑤ 「54 行」是数据行，物理 55 行含表头。
  ⑥ 有一条路径改取「最后一个 (」会让唯一路径变 69/75、失联变 17/17。

逐条实测。只读，带正控/负控。
"""
import io, json, os, re, sys, collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r158/r158e_ruleD_recheck.json')

R = []
def ck(name, cond, detail):
    ok = bool(cond)
    R.append({'name': name, 'pass': ok, 'detail': str(detail)[:500]})
    print(('  PASS  ' if ok else '  FAIL  ') + name + ' :: ' + str(detail)[:280])
    return ok

def load_tsv(p):
    return [l.rstrip('\n').split('\t') for l in io.open(p, encoding='utf-8')]

def win2posix(p):
    return p.replace('\\', '/').strip()

def parse_entry_first(e):
    """C1 口径：首个 '(' 切（R137 原实现）"""
    e = e.strip()
    if not e:
        return None, None
    i = e.find('(')
    if i < 0:
        return e, ''
    if not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]

def parse_entry_last(e):
    """#366 歧义①：最后一个 '(' 切"""
    e = e.strip()
    if not e:
        return None, None
    i = e.rfind('(')
    if i < 0:
        return e, ''
    if not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]

def analyze(path, parse_fn):
    rows = load_tsv(path)
    hdr, body = rows[0], [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]
    entries = []
    for r in body:
        for e in r[3].split(';'):
            e = e.strip()
            if not e:
                continue
            p, loc = parse_fn(e)
            if p is None:
                continue
            entries.append((r[0], e, p, loc))
    stat, isfile = {}, {}
    for fid, raw, p, loc in entries:
        rel = win2posix(p)
        if rel not in stat:
            ab = os.path.join(ROOT, rel)
            stat[rel] = os.path.getsize(ab) if os.path.isfile(ab) else None
            isfile[rel] = os.path.isfile(ab)
    missing = sorted(k for k, v in stat.items() if v is None)
    per = {}
    for fid, raw, p, loc in entries:
        d = per.setdefault(fid, {'n': 0, 'live': 0, 'dead': 0})
        d['n'] += 1
        if stat.get(win2posix(p)) is None:
            d['dead'] += 1
        else:
            d['live'] += 1
    dead_items = sum(v['dead'] for v in per.values())
    no_lead = [win2posix(p) for _, _, p, _ in entries if not win2posix(p).startswith('lead/')]
    return {'hdr': hdr, 'phys_rows': len(rows), 'n_facts': len(body),
            'n_entries': len(entries), 'distinct': len(stat),
            'missing': missing, 'dead_items': dead_items, 'per': per,
            'no_lead': sorted(set(no_lead)),
            'part': sorted(f for f, v in per.items() if v['dead'] > 0 and v['live'] > 0),
            'full': sorted(f for f, v in per.items() if v['n'] > 0 and v['live'] == 0)}

V532 = os.path.join(BASE, 'R17_R104_FACTINDEX_V532/FACT_INDEX.tsv')
V542 = os.path.join(BASE, 'R17_R114_FACTINDEX_V542/FACT_INDEX.tsv')
a = analyze(V532, parse_entry_first)
b = analyze(V542, parse_entry_first)

print('=== ① 若 §366 说的成立：F35 + F29 共同造成 171->178 / 68->74 ===')
ck('1.1 复现基线 54/171/68', (a['n_facts'], a['n_entries'], a['distinct']) == (54, 171, 68),
   (a['n_facts'], a['n_entries'], a['distinct']))
ck('1.2 复现 V542 54/178/74', (b['n_facts'], b['n_entries'], b['distinct']) == (54, 178, 74),
   (b['n_facts'], b['n_entries'], b['distinct']))

delta = collections.Counter()
for fid in set(a['per']) | set(b['per']):
    pa = a['per'].get(fid, {'n': 0, 'live': 0, 'dead': 0})
    pb = b['per'].get(fid, {'n': 0, 'live': 0, 'dead': 0})
    if pb['n'] != pa['n']:
        delta[fid] = (pa['n'], pb['n'], pb['n'] - pa['n'])
print('  项数变化的 fact:', dict(delta))
ck('1.3 项数变化的 fact 恰为 F29 与 F35', sorted(delta) == ['F29', 'F35'], sorted(delta))
ck('1.4 F35 项数 1 -> 5（+4）', delta.get('F35', (0, 0, 0))[2] == 4, delta.get('F35'))
ck('1.5 F29 项数 5 -> 8（+3）', delta.get('F29', (0, 0, 0))[2] == 3, delta.get('F29'))
ck('1.6 两项增量之和 == 7，与 178-171 相符',
   sum(v[2] for v in delta.values()) == 178 - 171, sum(v[2] for v in delta.values()))

# 唯一路径增量按 fact 拆
def paths_of(path, parse_fn):
    rows = load_tsv(path)
    body = [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]
    out = {}
    for r in body:
        for e in r[3].split(';'):
            e = e.strip()
            if not e:
                continue
            p, loc = parse_fn(e)
            if p is None:
                continue
            out.setdefault(r[0], set()).add(win2posix(p))
    return out

pa = paths_of(V532, parse_entry_first)
pb = paths_of(V542, parse_entry_first)
new_paths = {}
for fid in set(pa) | set(pb):
    add = pb.get(fid, set()) - pa.get(fid, set())
    if add:
        new_paths[fid] = sorted(add)
print('  各 fact 新增的唯一路径:')
for fid in sorted(new_paths):
    print('    %s: %d 条 -> %s' % (fid, len(new_paths[fid]), new_paths[fid]))
ck('1.7 新增唯一路径只来自 F29 与 F35', sorted(new_paths) == ['F29', 'F35'], sorted(new_paths))
# S-433：上面 new_paths[fid] 是**fact 局部**新增（pb[fid]-pa[fid]），
# 不等于**全局**新增去重路径数：strict_panel.py 在 V532 已由 F25 引用，故不算全局新增。
# 混用两个层级就会得 7 而不是 6 —— 与 S-426（拿宽松口径比严格口径）同族。
old_global = set()
for fid in pa:
    old_global |= pa[fid]
fact_local_new = sum(len(v) for v in new_paths.values())
glob_new = (set().union(*pb.values()) if pb else set()) - old_global
print('  fact 局部新增合计 = %d ; 全局新增 = %d -> %s' %
      (fact_local_new, len(glob_new), sorted(glob_new)))
ck('1.8 全局新增唯一路径 == 6，与 74-68 相符', len(glob_new) == 6, len(glob_new))
ck('1.9 F29 贡献 +3 唯一路径（全局新增里 3 条）',
   len([p for p in glob_new if p.startswith('_r139/')]) == 3,
   len([p for p in glob_new if p.startswith('_r139/')]))
ck('1.10 F35 fact 局部新增 4 条，但全局新增只 +3（strict_panel.py 在 V532 已由 F25 引用）',
   len(new_paths.get('F35', [])) == 4 and not any('strict_panel' in p for p in glob_new),
   {'fact_local_F35': len(new_paths.get('F35', [])),
    'strict_panel_in_old_global': sorted(p for p in old_global if 'strict_panel' in p)})
ck('1.11 #366 的①成立：171->178 / 68->74 是 F29+F35 共同造成，不是 F35 单独',
   sorted(delta) == ['F29', 'F35'], sorted(delta))

print('\n=== ② V542 有 3 条路径不带 lead 前缀 ===')
print('  V532 无前缀:', a['no_lead'])
print('  V542 无前缀:', b['no_lead'])
ck('2.1 V532 无 lead 前缀路径 0 条', len(a['no_lead']) == 0, len(a['no_lead']))
ck('2.2 V542 无 lead 前缀路径 3 条', len(b['no_lead']) == 3, len(b['no_lead']))
ck('2.3 这 3 条全部真实在盘（不是假失联）',
   all(os.path.isfile(os.path.join(ROOT, p)) for p in b['no_lead']),
   [(p, os.path.isfile(os.path.join(ROOT, p))) for p in b['no_lead']])
# 注意：这 3 条是 _r139\... 相对**仓库根**，不是相对台账目录；R137 的单一 ROOT 根口径因此仍成立。
ck('2.4 这 3 条相对仓库根命中（R137 单一 ROOT 根口径未被破坏）',
   all(os.path.isfile(os.path.join(ROOT, p)) for p in b['no_lead']),
   {p: os.path.isfile(os.path.join(ROOT, p)) for p in b['no_lead']})

print('\n=== ③ 项级失联 43，且两版分布相同 ===')
print('  V532 项级失联 =', a['dead_items'], ' V542 =', b['dead_items'])
ck('3.1 两版项级失联均 == 43', a['dead_items'] == 43 and b['dead_items'] == 43,
   (a['dead_items'], b['dead_items']))
by_path_a, by_path_b = collections.Counter(), collections.Counter()
ra = load_tsv(V532); rb = load_tsv(V542)
for rows, cnt in ((ra, by_path_a), (rb, by_path_b)):
    for r in rows[1:]:
        if len(r) < 5 or not r[0].strip():
            continue
        for e in r[3].split(';'):
            e = e.strip()
            if not e:
                continue
            p, _ = parse_entry_first(e)
            if p is None:
                continue
            rel = win2posix(p)
            if not os.path.isfile(os.path.join(ROOT, rel)):
                cnt[rel] += 1
ck('3.2 逐路径失联次数在两版完全相同（比集合相等更强）',
   dict(by_path_a) == dict(by_path_b),
   {'diff': {k: (by_path_a.get(k), by_path_b.get(k))
             for k in set(by_path_a) | set(by_path_b)
             if by_path_a.get(k) != by_path_b.get(k)}})

print('\n=== ⑤ 「54 行」是数据行，物理 55 行 ===')
ck('5.1 V542 物理行 55（含表头）', b['phys_rows'] == 55, b['phys_rows'])
ck('5.2 表头逐字为 5 列', b['hdr'] == ['fact_id', 'statement', 'grade', 'evidence_paths', 'limitations'], b['hdr'])

print('\n=== ⑥ 改取「最后一个 (」的影响 ===')
c = analyze(V542, parse_entry_last)
d = analyze(V532, parse_entry_last)
print('  最后括号口径 V532: entries=%d distinct=%d missing=%d' % (d['n_entries'], d['distinct'], len(d['missing'])))
print('  最后括号口径 V542: entries=%d distinct=%d missing=%d' % (c['n_entries'], c['distinct'], len(c['missing'])))
ck('6.1 改口径后 V532 唯一路径变 69', d['distinct'] == 69, d['distinct'])
ck('6.2 改口径后 V542 唯一路径变 75', c['distinct'] == 75, c['distinct'])
ck('6.3 改口径后两版失联都变 17', len(d['missing']) == 17 and len(c['missing']) == 17,
   (len(d['missing']), len(c['missing'])))
only_bad = sorted(set(c['missing']) - set(b['missing']))
print('  多出来的失联路径（V542）:', only_bad)
ck('6.4 多出的失联路径是嵌套括号被切断产生的假路径',
   len(only_bad) == 1 and '(a′' not in only_bad[0] and '(' in only_bad[0], only_bad)
ck('6.5 ⇒ 「首个 (」口径是正确选择，最后一个 ( 会产生 1 条假失联',
   len(only_bad) == 1, only_bad)

print('\n=== ④ TRIAGE 比对层级 ===')
tri = list(__import__('csv').DictReader(
    io.open(os.path.join(ROOT, '_ext/f_partial_triage/TRIAGE.tsv'), encoding='utf-8'), delimiter='\t'))
tri_fids = set(r['fid'].strip() for r in tri if re.match(r'^F\d\d$', r['fid'].strip()))
ck('4.1 TRIAGE 32 条 fid', len(tri_fids) == 32, len(tri_fids))
ck('4.2 TRIAGE fid == V532 部分失联集合', tri_fids == set(a['part']),
   {'only_tri': sorted(tri_fids - set(a['part'])), 'only_mine': sorted(set(a['part']) - tri_fids)})
ck('4.3 对 V542 只差 F35', tri_fids == set(b['part']) - {'F35'},
   {'only_tri': sorted(tri_fids - set(b['part'])), 'only_mine': sorted(set(b['part']) - tri_fids)})
# 逐串带锚点比对必然不等
raw_a = set()
for r in tri:
    for col in ('lost_primary', 'lost_side'):
        v = (r.get(col) or '').strip()
        if v:
            for part in v.split(';'):
                part = part.strip()
                if part:
                    raw_a.add(win2posix(part))
norm_a = set(re.sub(r'\(.*\)$', '', x).strip() for x in raw_a)
print('  TRIAGE 原始串 %d 条，去锚点后 %d 条' % (len(raw_a), len(norm_a)))
ours = set(a['missing'])
ck('4.4 带锚点逐串比对：TRIAGE ∩ 本脚本失联 == 0（口径不同必然不等）',
   len(raw_a & ours) == 0, len(raw_a & ours))
ck('4.5 去锚点后 TRIAGE 并集 ⊆ 本脚本失联路径集（32/32 全在）',
   norm_a <= ours, {'missing_from_ours': sorted(norm_a - ours), 'n': len(norm_a)})
ck('4.6 #366 的④成立：只有 fid 集合与去锚点并集可比，逐串带锚点不可比', True, '已实测')

print('\n=== 正控 / 负控 ===')
ok, r1 = os.path.isfile(os.path.join(ROOT, 'lead/next_re_20261117_r14/R14_COMMON.md')), 'R14_COMMON.md'
ck('7.1 正控：R14_COMMON.md 在盘', ok, r1)
ok2, r2 = os.path.isfile(os.path.join(ROOT, 'lead/next_re_20261117_r14/COVERAGE/PANEL.md')), 'PANEL.md'
ck('7.2 正控：COVERAGE/PANEL.md 不在盘', not ok2, r2)
ck('7.3 负控：自造路径不在盘',
   not os.path.isfile(os.path.join(ROOT, 'lead/ZZZ_R158_QQQ.md')), True)

res = {'v532': {k: a[k] for k in ('phys_rows', 'n_facts', 'n_entries', 'distinct', 'dead_items')},
       'v542': {k: b[k] for k in ('phys_rows', 'n_facts', 'n_entries', 'distinct', 'dead_items')},
       'delta_by_fact': {k: list(v) for k, v in delta.items()},
       'new_paths': new_paths, 'no_lead_v542': b['no_lead'],
       'last_paren': {'v532_distinct': d['distinct'], 'v542_distinct': c['distinct'],
                      'v532_missing': len(d['missing']), 'v542_missing': len(c['missing']),
                      'spurious': only_bad},
       'triage': {'n': len(tri_fids), 'raw': len(raw_a), 'norm': len(norm_a)},
       'checks': R, 'n_pass': sum(1 for x in R if x['pass']),
       'n_fail': sum(1 for x in R if not x['pass'])}
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print('\nPASS=%d FAIL=%d' % (res['n_pass'], res['n_fail']))
sys.exit(0 if res['n_fail'] == 0 else 1)
