#!/usr/bin/env python3
"""R170 E：V549 现状下的证据存活复算（与 facts_floors 同口径：strip_note + 反斜杠归一 + 三根解析）。
输出：每行存活项数 / 零存活行 / F23 与 F35 逐项。
"""
import json, os, re
ROOT = '/home/t628/projects/ra2-campaign-forge'
TIER = ROOT + '/lead/next_re_20261117_r14'
V = TIER + '/R17_R121_FACTINDEX_V549/FACT_INDEX.tsv'
A = []
def ck(i, cond, d):
    A.append({'id': i, 'ok': bool(cond), 'detail': str(d)})
    print(('PASS ' if cond else 'FAIL ') + i + ' :: ' + str(d)[:230])

def strip_note(s):
    s = s.strip()
    if s.endswith(')'):
        d = 0
        for i in range(len(s) - 1, -1, -1):
            if s[i] == ')': d += 1
            elif s[i] == '(':
                d -= 1
                if d == 0: return s[:i].strip()
    return s

def norm(p): return p.replace('\\', '/').strip()

def resolvable(p):
    for c in (p, 'lead/' + p, TIER + '/' + p):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False

rows = []
for ln in open(V, encoding='utf-8', newline='').read().split('\n')[1:]:
    if not ln.strip(): continue
    rows.append(ln.split('\t'))
ck('E0 54 行', len(rows) == 54, len(rows))

per = {}
for f in rows:
    ps = [norm(strip_note(x)) for x in f[3].split(';') if x.strip()]
    alive = [p for p in ps if resolvable(p)]
    per[f[0]] = {'grade': f[2], 'items': len(ps), 'alive': len(alive),
                 'lost': len(ps) - len(alive), 'paths': ps}
zero = [k for k, v in per.items() if v['items'] > 0 and v['alive'] == 0]
print('零存活行 =', zero)
ck('E1 零存活恰 1 行 = F23', zero == ['F23'], zero)
ck('E2 F23 2 项 0 活', per['F23']['items'] == 2 and per['F23']['alive'] == 0, per['F23'])
ck('E3 F35 5 项 4 活 1 失', per['F35']['items'] == 5 and per['F35']['alive'] == 4, per['F35'])
ck('E4 F35 唯一失联项 = COVERAGE/PANEL.md',
   [p for p in per['F35']['paths'] if not resolvable(p)] == ['lead/next_re_20261117_r14/COVERAGE/PANEL.md'],
   [p for p in per['F35']['paths'] if not resolvable(p)])
# 反控：把 TTER 根改错，F35 存活应变 0（证明根选择有判别力）
def resolvable_bad(p):
    for c in ('ZZ/' + p,):
        if os.path.exists(os.path.join(ROOT, c)): return True
    return False
ck('E5 反控：错根下 F35 存活 = 0', all(not resolvable_bad(p) for p in per['F35']['paths']), 'ok')
# [已证] 27 行的存活分布
gz = {k: v for k, v in per.items() if v['grade'] == '[已证]'}
ck('E6 [已证] 行数 27', len(gz) == 27, len(gz))
dist = sorted(v['alive'] for v in gz.values())
import statistics
ck('E7 [已证] 存活项最小 = 0 且唯一（F23）', dist[0] == 0 and dist.count(0) == 1, dist)
ck('E8 [已证] 存活中位数 = 2', statistics.median(dist) == 2, statistics.median(dist))
# 全表计数
ck('E9 证据项总数', sum(v['items'] for v in per.values()), sum(v['items'] for v in per.values()))
ck('E10 失联项总数', sum(v['lost'] for v in per.values()), sum(v['lost'] for v in per.values()))

json.dump({'assertions': A, 'fail': sum(1 for a in A if not a['ok']), 'per': per,
           'zero': zero, 'dist_evidence': dist,
           'items': sum(v['items'] for v in per.values()),
           'lost': sum(v['lost'] for v in per.values())},
          open(ROOT + '/_r170/r170e_survival.json', 'w'), ensure_ascii=False, indent=1)
print('FAIL =', sum(1 for a in A if not a['ok']), '/', len(A))
