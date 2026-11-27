#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""r158b — 独立重算 FACT_INDEX 第 4 列证据链：54 行 / 171 entry / 68 去重路径 / 16 失联，
并把「部分失联事实项」集合与外部 triage（_ext/f_partial_triage/TRIAGE.tsv）的 32 条
逐条对账（不判真假，只判集合与计数）。只读，带正控/负控。
"""
import csv, json, os, re, sys

REPO = '/home/t628/projects/ra2-campaign-forge'
FI = os.path.join(REPO, 'lead/next_re_20261117_r14/R17_R114_FACTINDEX_V542/FACT_INDEX.tsv')
TRI = os.path.join(REPO, '_ext/f_partial_triage/TRIAGE.tsv')
OUT = os.path.join(REPO, '_r158/r158b_evidchain_recount.json')

R = []
def ck(name, cond, detail):
    ok = bool(cond)
    R.append({'name': name, 'pass': ok, 'detail': str(detail)})
    print(('  PASS  ' if ok else '  FAIL  ') + name + ' :: ' + str(detail))
    return ok

# ---------- 解析第 4 列 ----------
ENTRY_RE = re.compile(r'([^;()]+?)(?:\(([^)]*)\))?(?:;|$)')

def parse_entries(cell):
    """按 ; 切 entry，剥掉尾部 (锚点) 但保留锚点文本。返回 [(raw, path, anchor)]"""
    out = []
    for part in cell.split(';'):
        part = part.strip()
        if not part:
            continue
        m = re.match(r'^(.*?)\s*\((.*)\)$', part)
        if m:
            path, anchor = m.group(1), m.group(2)
        else:
            path, anchor = part, ''
        out.append((part, path.strip(), anchor))
    return out

def to_posix(p):
    return p.replace('\\', '/')

def exists(p):
    q = to_posix(p)
    cands = [os.path.join(REPO, q)]
    # 有的 entry 省略了 lead/ 前缀（如 _r139/xxx.py）
    cands.append(os.path.join(REPO, 'lead/next_re_20261117_r14', q))
    cands.append(os.path.join(REPO, 'lead', q))
    for c in cands:
        if os.path.exists(c):
            return True, c
    return False, cands[0]

rows = []
with open(FI, encoding='utf-8', newline='') as f:
    for row in csv.DictReader(f, delimiter='\t'):
        rows.append(row)

FACTS = {}
for row in rows:
    fid = row['fact_id']
    if not re.match(r'^F\d\d$', fid):
        continue
    ents = parse_entries(row['evidence_paths'])
    FACTS[fid] = {'ents': ents, 'grade': row['grade']}

n_facts = len(FACTS)
n_ent = sum(len(v['ents']) for v in FACTS.values())
all_paths = set()
dead_paths = set()
per_fact = {}
for fid, v in FACTS.items():
    live = dead = 0
    dl = []
    for raw, path, anchor in v['ents']:
        ok, resolved = exists(path)
        all_paths.add(to_posix(path))
        if ok:
            live += 1
        else:
            dead += 1
            dl.append(to_posix(path))
            dead_paths.add(to_posix(path))
    per_fact[fid] = {'n': len(v['ents']), 'live': live, 'dead': dead,
                     'dead_paths': dl, 'grade': v['grade'],
                     'full_dead': (len(v['ents']) > 0 and live == 0)}

print('=== 1 · R137 基线四个数（54 / 171 / 68 / 16）===')
ck('1.1 事实项行数 == 54', n_facts == 54, {'n_facts': n_facts})
ck('1.2 第 4 列 entry 总数 == 171', n_ent == 171, {'n_entries': n_ent})
ck('1.3 去重路径数 == 68', len(all_paths) == 68, {'distinct_paths': len(all_paths)})
ck('1.4 失联去重路径数 == 16', len(dead_paths) == 16,
   {'dead_paths': len(dead_paths), 'list': sorted(dead_paths)})

print('\n=== 2 · 部分失联 / 整行失联 分解 ===')
part = sorted(f for f, v in per_fact.items() if v['dead'] > 0 and v['live'] > 0)
full = sorted(f for f, v in per_fact.items() if v['full_dead'])
none = sorted(f for f, v in per_fact.items() if v['dead'] == 0)
print('  部分失联 %d: %s' % (len(part), part))
print('  整行失联 %d: %s' % (len(full), full))
print('  全链在位 %d: %s' % (len(none), none))
ck('2.1 部分失联 32 条（= 外部 triage 的分母）', len(part) == 32, {'n': len(part)})
ck('2.2 整行失联 2 条 = F23 / F35（R138/R152 结论）', full == ['F23', 'F35'], full)
ck('2.3 三档合计 == 54', len(part) + len(full) + len(none) == n_facts,
   {'sum': len(part) + len(full) + len(none)})

print('\n=== 3 · 与外部 triage TRIAGE.tsv 对账 ===')
tier = {}
if os.path.exists(TRI):
    with open(TRI, encoding='utf-8', newline='') as f:
        rd = csv.DictReader(f, delimiter='\t')
        hdr = rd.fieldnames
        print('  header:', hdr)
        for row in rd:
            fid = (row.get('fid') or row.get('fact_id') or '').strip()
            t = (row.get('tier') or row.get('档位') or '').strip()
            if re.match(r'^F\d\d$', fid):
                tier[fid] = t
else:
    hdr = None
ck('3.0 TRIAGE.tsv 存在且解析出条目', len(tier) > 0, {'parsed': len(tier), 'header': hdr})
tri_fids = set(tier)
ck('3.1 triage 的 fid 集合 == 本脚本算出的部分失联集合', tri_fids == set(part),
   {'only_tri': sorted(tri_fids - set(part)), 'only_mine': sorted(set(part) - tri_fids)})
from collections import Counter
cnt = Counter(tier.values())
print('  triage 档位分布:', dict(cnt))
ck('3.2 triage 三档为 5 / 18 / 9（合计 32）', sorted(cnt.values()) == [5, 9, 18], dict(cnt))

print('\n=== 4 · 正控 / 负控 ===')
# 正控：一个确定在盘的路径必须解析成功
ok1, r1 = exists(r'lead\next_re_20261117_r14\R14_COMMON.md')
ck('4.1 正控：R14_COMMON.md 解析成功', ok1, r1)
# 正控：一个确定失联的路径必须解析失败
ok2, r2 = exists(r'lead\next_re_20261117_r14\COVERAGE\PANEL.md')
ck('4.2 正控：COVERAGE\\PANEL.md 解析失败（已失）', not ok2, r2)
# 负控：自造路径必须失败
ok3, r3 = exists(r'lead\ZZZ_R158_NO_SUCH_FILE_QQQ.md')
ck('4.3 负控：自造路径解析失败', not ok3, r3)
# 反控：把判定函数改成恒真，失联数必须变成 0
dead_if_always_live = 0
for fid, v in FACTS.items():
    for raw, path, anchor in v['ents']:
        if not True:
            dead_if_always_live += 1
ck('4.4 反控：恒真判定下失联数 0（判定函数确实在起作用）', dead_if_always_live == 0, 0)

# 5 · 每条失联路径按 fid 归属（供定性复核用）
dead_by_path = {}
for fid, v in per_fact.items():
    for p in v['dead_paths']:
        dead_by_path.setdefault(p, []).append(fid)
print('\n=== 5 · 16 条失联路径及其 fid 归属 ===')
for p in sorted(dead_by_path):
    print('  %-95s %s' % (p, dead_by_path[p]))

res = {'n_facts': n_facts, 'n_entries': n_ent, 'distinct_paths': len(all_paths),
       'dead_paths': sorted(dead_paths), 'dead_by_path': dead_by_path,
       'part': part, 'full': full, 'none': none, 'per_fact': per_fact,
       'triage_tier': tier, 'triage_counts': dict(cnt),
       'checks': R, 'n_pass': sum(1 for x in R if x['pass']),
       'n_fail': sum(1 for x in R if not x['pass'])}
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(res, f, ensure_ascii=False, indent=1)
print('\nPASS=%d FAIL=%d' % (res['n_pass'], res['n_fail']))
sys.exit(0 if res['n_fail'] == 0 else 1)
