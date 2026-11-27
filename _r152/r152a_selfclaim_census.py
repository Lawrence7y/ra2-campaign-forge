#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R152 A：FACT_INDEX v5.40 内部「自述证据项数 vs 实际项数」一致性普查（只读）。

判据（先定义再统计）：
  实际项数 = 第 4 列按 ';' 切分后的非空 entry 数
  实际失联 = entry 的 '(' 之前部分（win 反斜杠转 posix）在现盘 os.path.exists 为假
扫描自述性断言（statement + limitations 两列）：
  A 类「唯一一项」   —— 断言本条 evidence_paths 只有一项
  B 类「整行证据链失联」—— 断言本条属整行失联
  C 类「N 项」      —— 断言本条 evidence_paths 有 N 项
C 类必须区分「本条」与「别的条」，故只在同句出现 本条/evidence_paths 时计。
正控：F35 第 4 列实测 5 项 4 活 1 失；反控：把条目按字符 ',' 切分应得不同数（证明切分敏感）。
"""
import json, os, re, sys

ROOT = '/home/t628/projects/ra2-campaign-forge'
P = os.path.join(ROOT, 'lead/next_re_20261117_r14/R17_R112_FACTINDEX_V540/FACT_INDEX.tsv')
fails = []


def ck(n, c, d=''):
    print(('  PASS ' if c else '  FAIL ') + n + (('  ' + str(d)) if d else ''))
    if not c:
        fails.append(n)


raw = open(P, 'rb').read()
ck('0.1 v5.40 88,786 B', len(raw) == 88786, len(raw))
import hashlib
ck('0.2 v5.40 sha fabd1e57…',
   hashlib.sha256(raw).hexdigest() == 'fabd1e5702814b5c6f89737d905e40a01da241981c8d84361869b2243821d07a',
   hashlib.sha256(raw).hexdigest()[:16])
lines = raw.decode('utf-8').split('\n')
ck('0.3 54 数据行 + 末尾空串', len(lines) == 56 and lines[-1] == '', len(lines))
rows = [l.split('\t') for l in lines if l.strip()]
hdr, data = rows[0], rows[1:]
ck('0.4 每行 5 列', all(len(r) == 5 for r in data), set(len(r) for r in data))


def entries(cell):
    return [e for e in cell.split(';') if e.strip()]


def path_of(e):
    return e.split('(')[0].strip().replace('\\', '/')


stat = {}
for r in data:
    es = entries(r[3])
    dead = [e for e in es if not os.path.exists(os.path.join(ROOT, path_of(e)))]
    stat[r[0]] = {'grade': r[2], 'n': len(es), 'dead': len(dead),
                  'alive': len(es) - len(dead), 'dead_list': dead}

ck('1.1 证据项总数 178', sum(v['n'] for v in stat.values()) == 178,
   sum(v['n'] for v in stat.values()))
ck('1.2 失联项 43 / 存活 135', sum(v['dead'] for v in stat.values()) == 43
   and sum(v['alive'] for v in stat.values()) == 135,
   (sum(v['dead'] for v in stat.values()), sum(v['alive'] for v in stat.values())))
ck('1.3 整行全失联恰 1 行 = F23',
   [k for k, v in stat.items() if v['n'] == v['dead']] == ['F23'],
   [k for k, v in stat.items() if v['n'] == v['dead']])

# 正控：F35 5 项 4 活 1 失
ck('2.1 正控 F35 = 5 项 / 4 活 / 1 失',
   (stat['F35']['n'], stat['F35']['alive'], stat['F35']['dead']) == (5, 4, 1),
   (stat['F35']['n'], stat['F35']['alive'], stat['F35']['dead']))
# 反控：换成按 ',' 切分，F35 项数必须不同（证明切分敏感、不是恒真）
ck('2.2 反控 F35 按逗号切分 != 5', len([x for x in rows_b.split()]) if False else
   len([x for x in [r for r in data if r[0] == 'F35'][0][3].split(',') if x.strip()]) != 5,
   len([x for x in [r for r in data if r[0] == 'F35'][0][3].split(',') if x.strip()]))

# ---------- 自述断言扫描 ----------
print('\n[3] 自述断言扫描（statement + limitations）')
PAT_UNIQUE = re.compile(r'唯一一项')
PAT_WHOLE = re.compile(r'整行证据链失联')
PAT_N = re.compile(r'(\d+)\s*项')
hits = []
for r in data:
    for colname, col in (('statement', 1), ('limitations', 4)):
        txt = r[col]
        for m in PAT_UNIQUE.finditer(txt):
            hits.append((r[0], colname, 'A-唯一一项', txt[max(0, m.start() - 60):m.start() + 60]))
        for m in PAT_WHOLE.finditer(txt):
            hits.append((r[0], colname, 'B-整行失联', txt[max(0, m.start() - 60):m.start() + 60]))
        for m in PAT_N.finditer(txt):
            ctx = txt[max(0, m.start() - 40):m.start() + 30]
            if 'evidence_paths' in ctx or '本条' in ctx:
                hits.append((r[0], colname, 'C-N项=' + m.group(1), ctx))
for h in hits:
    print('  %-4s %-11s %-14s … %s' % (h[0], h[1], h[2], h[3].replace('\n', ' ')))

print('\n[4] 逐条一致性判定（只判 A/B/C 三类可机械比对的）')
viol = []
for fid, colname, kind, ctx in hits:
    v = stat[fid]
    if kind == 'A-唯一一项':
        ok = (v['n'] == 1)
        print('  %-4s %-11s 断言唯一一项，实际 %d 项 -> %s' % (fid, colname, v['n'], 'OK' if ok else 'CONTRADICTION'))
        if not ok:
            viol.append((fid, colname, 'A', v['n'], ctx))
    elif kind == 'B-整行失联':
        ok = (v['n'] == v['dead'])
        print('  %-4s %-11s 断言整行失联，实际 %d/%d 失 -> %s' % (fid, colname, v['dead'], v['n'], 'OK' if ok else '需看作用域'))
    elif kind.startswith('C-N项='):
        want = int(kind.split('=')[1])
        ok = (v['n'] == want)
        print('  %-4s %-11s 断言 %d 项，实际 %d 项 -> %s' % (fid, colname, want, v['n'], 'OK' if ok else '疑不合'))
out = {'pins': {'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'rows': len(data)},
       'stat': stat,
       'violations': [{'fid': v[0], 'col': v[1], 'kind': v[2], 'actual_n': v[3], 'ctx': v[4]} for v in viol],
       'fails': fails}
json.dump(out, open(os.path.join(ROOT, '_r152/r152a_selfclaim_census.json'), 'w'),
          ensure_ascii=False, indent=1)
print('\nFAILS:', fails if fails else 'none')
sys.exit(1 if fails else 0)
