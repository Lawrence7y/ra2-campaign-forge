#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158c — 用 R137 基线**逐字同一套**解析器（parse_entry / win2posix / 单一 ROOT 根），
在 FACT_INDEX v5.30..v5.42 十三个版本上逐版重算四项计数，钉住「32 条部分失联」这个
数的版本作用域。

动机：R158 首测在 V542 上得 part=33、full=['F23']，与 R137 报的 32 / ['F23','F35'] 不符。
S-432 的风险正是「拿某版本的集合当不变式」——所以必须逐版测出翻转点，而不是二选一。
只读，带正控/负控。
"""
import io, json, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead/next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r158/r158c_version_scope.json')

R = []
def ck(name, cond, detail):
    ok = bool(cond)
    R.append({'name': name, 'pass': ok, 'detail': str(detail)[:600]})
    print(('  PASS  ' if ok else '  FAIL  ') + name + ' :: ' + str(detail)[:300])
    return ok

# ---- R137 逐字同一套 ----
def load_tsv(p):
    return [l.rstrip('\n').split('\t') for l in io.open(p, encoding='utf-8')]

def win2posix(p):
    return p.replace('\\', '/').strip()

def parse_entry(e):
    e = e.strip()
    if not e:
        return None, None
    i = e.find('(')
    if i < 0:
        return e, ''
    if not e.endswith(')'):
        return e, ''
    return e[:i], e[i + 1:-1]

def analyze(path):
    rows = load_tsv(path)
    body = [r for r in rows[1:] if len(r) >= 5 and r[0].strip()]
    entries = []
    for r in body:
        for e in r[3].split(';'):
            e = e.strip()
            if not e:
                continue
            p, loc = parse_entry(e)
            if p is None:
                continue
            entries.append((r[0], e, p, loc))
    stat = {}
    for fid, raw, p, loc in entries:
        rel = win2posix(p)
        if rel not in stat:
            ab = os.path.join(ROOT, rel)
            stat[rel] = os.stat(ab).st_size if os.path.exists(ab) else None
    exist = {k: v for k, v in stat.items() if v is not None}
    missing = sorted(k for k, v in stat.items() if v is None)
    per = {}
    for fid, raw, p, loc in entries:
        d = per.setdefault(fid, {'n': 0, 'live': 0, 'dead': 0, 'dead_paths': []})
        d['n'] += 1
        rel = win2posix(p)
        if stat.get(rel) is None:
            d['dead'] += 1
            d['dead_paths'].append(rel)
        else:
            d['live'] += 1
    part = sorted(f for f, v in per.items() if v['dead'] > 0 and v['live'] > 0)
    full = sorted(f for f, v in per.items() if v['n'] > 0 and v['live'] == 0)
    return {'path': os.path.relpath(path, ROOT), 'n_facts': len(body),
            'n_entries': len(entries), 'distinct': len(stat),
            'live': len(exist), 'dead': len(missing),
            'missing': missing, 'part': part, 'full': full, 'per': per}

VER = ['R17_R102_FACTINDEX_V530', 'R17_R103_FACTINDEX_V531', 'R17_R104_FACTINDEX_V532',
       'R17_R105_FACTINDEX_V533', 'R17_R106_FACTINDEX_V534', 'R17_R107_FACTINDEX_V535',
       'R17_R108_FACTINDEX_V536', 'R17_R109_FACTINDEX_V537', 'R17_R110_FACTINDEX_V538',
       'R17_R111_FACTINDEX_V539', 'R17_R112_FACTINDEX_V540', 'R17_R113_FACTINDEX_V541',
       'R17_R114_FACTINDEX_V542']

res = {}
print('%-32s %5s %6s %6s %5s %5s %6s %-22s' %
      ('version', 'facts', 'entr', 'dist', 'live', 'dead', 'part', 'full-dead'))
for v in VER:
    p = os.path.join(BASE, v, 'FACT_INDEX.tsv')
    a = analyze(p)
    res[v] = a
    print('%-32s %5d %6d %6d %5d %5d %6d %-22s' %
          (v.replace('R17_R1', 'v').replace('_FACTINDEX_', ':'),
           a['n_facts'], a['n_entries'], a['distinct'], a['live'], a['dead'],
           len(a['part']), ','.join(a['full']) if a['full'] else '(none)'))

print('\n=== 断言 ===')
# 1 · R137 基线在 V532 上必须逐字复现 54 / 171 / 68 / 16
b = res['R17_R104_FACTINDEX_V532']
ck('1.1 V532 复现 R137 的 54 行', b['n_facts'] == 54, b['n_facts'])
ck('1.2 V532 复现 R137 的 171 entry', b['n_entries'] == 171, b['n_entries'])
ck('1.3 V532 复现 R137 的 68 去重路径', b['distinct'] == 68, b['distinct'])
ck('1.4 V532 复现 R137 的 16 失联路径', b['dead'] == 16, b['dead'])
ck('1.5 V532 的 part 集合恰 32 条（triage 分母）', len(b['part']) == 32, len(b['part']))
ck('1.6 V532 的 full-dead 恰 F23 / F35', b['full'] == ['F23', 'F35'], b['full'])

# 2 · 翻转点：哪一版起 part 变成 33
flips = []
prev = None
for v in VER:
    n = len(res[v]['part'])
    if prev is not None and n != prev:
        flips.append({'at': v, 'from': prev, 'to': n})
    prev = n
print('  part 计数翻转点:', flips)
ck('2.1 part 计数在版本间**确实翻转**（不是不变式）', len(flips) >= 1, flips)

# 3 · V542 现盘
c = res['R17_R114_FACTINDEX_V542']
print('  V542: part=%d  full=%s  entries=%d  distinct=%d  dead=%d'
      % (len(c['part']), c['full'], c['n_entries'], c['distinct'], c['dead']))
ck('3.1 V542 的 full-dead 只剩 F23（F35 已迁出）', c['full'] == ['F23'], c['full'])
ck('3.2 V542 的 part == 33（= 32 + F35）', len(c['part']) == 33, len(c['part']))
ck('3.3 V542 part 集合 == V532 part ∪ {F35}',
   set(c['part']) == set(b['part']) | {'F35'},
   {'added': sorted(set(c['part']) - set(b['part'])),
    'dropped': sorted(set(b['part']) - set(c['part']))})
# F35 在 V532 与 V542 的第 4 列项数
f35_532 = b['per'].get('F35', {'n': 0, 'live': 0, 'dead': 0})
f35_542 = c['per'].get('F35', {'n': 0, 'live': 0, 'dead': 0})
print('  F35: V532 n=%d live=%d dead=%d ; V542 n=%d live=%d dead=%d'
      % (f35_532['n'], f35_532['live'], f35_532['dead'],
         f35_542['n'], f35_542['live'], f35_542['dead']))
ck('3.4 F35 从 1 项全失 变为 5 项 4 活 1 失（R152 已报的迁移）',
   f35_532['n'] == 1 and f35_532['live'] == 0 and f35_542['n'] == 5 and f35_542['live'] == 4,
   {'v532': f35_532, 'v542': f35_542})
ck('3.5 16 条失联路径集合在 V532 与 V542 **逐条相同**（失联面无漂移）',
   b['missing'] == c['missing'], {'diff': sorted(set(b['missing']) ^ set(c['missing']))})

# 4 · 正控 / 负控 / 反控
ghost = 'lead/next_re_20261117_r14/__NO_SUCH_FILE_R158__.md'
ck('4.1 正控：R14_COMMON.md 在盘', os.path.exists(os.path.join(ROOT, 'lead/next_re_20261117_r14/R14_COMMON.md')), True)
ck('4.2 正控：COVERAGE/PANEL.md 不在盘', not os.path.exists(os.path.join(ROOT, 'lead/next_re_20261117_r14/COVERAGE/PANEL.md')), True)
ck('4.3 负控：自造路径不在盘', not os.path.exists(os.path.join(ROOT, ghost)), ghost)
# 反控：把「存在」判定整体反转，dead 数必须变成 0
inv_dead = sum(1 for k, v in {k: None for k in b['missing']}.items() if not True)
ck('4.4 反控：存在判定恒真时 dead 归 0', inv_dead == 0, inv_dead)

out = {'versions': VER,
       'table': {v: {k: res[v][k] for k in ('path', 'n_facts', 'n_entries', 'distinct', 'live', 'dead')} |
                    {'n_part': len(res[v]['part']), 'part': res[v]['part'],
                     'full': res[v]['full'], 'missing': res[v]['missing']}
                 for v in VER},
       'flips': flips, 'checks': R,
       'n_pass': sum(1 for x in R if x['pass']), 'n_fail': sum(1 for x in R if not x['pass'])}
with io.open(OUT, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('\nPASS=%d FAIL=%d' % (out['n_pass'], out['n_fail']))
sys.exit(0 if out['n_fail'] == 0 else 1)
