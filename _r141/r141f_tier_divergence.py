#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：【规则 D 之二】两套分档为何背离 28/2/3 vs 5/18/9？

r141e 已定集合基数：v5.34 起「部分失联」= 33 条（外部 triage 的 32 是用 v5.33 算的，
因为 F35 在 v5.33 只有 1 条 evidence_path 且全失 => 当时属「全失联」；R139 补 4 条在盘实现后变「部分失联」）。

本脚本只做**一件事**：把「分档」这个主观判断换成可机械复算的代理量，看两套分档的差是否可由代理量解释。
代理量（每个 fid 一个数，全部可机械算）：
  P = 存活路径数 / 总路径数          （证据链在盘覆盖率）
  D = 失联路径中包含 SECTION/VERDICT/PANEL/HANDOFF 这几类「一手文本」的条数
  K = 失联路径中包含 11-22 快照清单里出现过的路径（曾存在）的条数 —— 本脚本不查快照，置 None
判据：若「一手文本失联数 D」能完整分开两套分档，则分歧是**判据定义差**（F41 的「口径差」），
      否则是真错。

反控：把 D 的定义换成「任意失联路径数」（丢掉一手性），看分开度是否下降。
"""
import csv
import io
import json
import os
import re
import collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
FI = os.path.join(ROOT, 'lead', 'next_re_20261117_r14', 'R17_R110_FACTINDEX_V538',
                  'FACT_INDEX.tsv')
EXT = os.path.join(ROOT, '_ext', 'f_partial_triage', 'TRIAGE.tsv')
SUB = os.path.join(ROOT, '_r141', 'sub_triage', 'triage_recompute.tsv')
fails, out = [], {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


PRIMARY = re.compile(r'(SECTION|VERDICT|PANEL|HANDOFF|DELIVERY_SUMMARY|PROGRESS|COVERAGE)')

rows = list(csv.DictReader(io.open(FI, encoding='utf-8'), delimiter='\t'))
rec = {}
for r in rows:
    ps = [q.strip().replace('\\', '/') for q in (r['evidence_paths'] or '').split(';') if q.strip()]
    ps = [q.split('(', 1)[0].strip() for q in ps]
    alive = [q for q in ps if os.path.exists(q)]
    dead = [q for q in ps if not os.path.exists(q)]
    rec[r['fact_id']] = dict(
        n=len(ps), alive=len(alive), dead=len(dead),
        P=round(len(alive) / len(ps), 4) if ps else None,
        D=sum(1 for q in dead if PRIMARY.search(os.path.basename(q))))
partial = [f for f, v in rec.items() if v['dead'] > 0 and v['alive'] > 0]
ck('0.1 部分失联 33 条', len(partial) == 33, len(partial))

ext = {r['fid']: r['verdict'] for r in csv.DictReader(io.open(EXT, encoding='utf-8'), delimiter='\t')}
sub = {r['fact_id']: r['tier'] for r in csv.DictReader(io.open(SUB, encoding='utf-8'), delimiter='\t')}
ck('0.2 外部 triage 32 条', len(ext) == 32, len(ext))
ck('0.3 执行员 33 条', len(sub) == 33, len(sub))

print('\n=== 用「一手文本失联数 D」与「覆盖率 P」看两套分档 ===')
print('  fid   n al dead    P  D   外部triage        执行员#311')
agree = 0
for f in sorted(partial):
    v = rec[f]
    e = ext.get(f, '(不在外部集合)')
    s = sub.get(f, '(缺失)')
    same = (e == s)
    agree += same
    print('  %-4s %-2d %-2d %-4d %-6s %-2d  %-16s %s' % (f, v['n'], v['alive'], v['dead'],
                                                        v['P'], v['D'], e[:16], s))
print('\n  两套分档完全一致的事实项: %d / %d' % (agree, len(partial)))
ck('1.1 两套分档一致的条数很少（< 10）', agree < 10, agree)

# D 的分布 vs 分档
print('\n=== D（一手文本失联数）在两套分档里的分布 ===')
for name, mp in (('外部 triage', ext), ('执行员 #311', sub)):
    dist = collections.defaultdict(list)
    for f in partial:
        if f in mp:
            dist[mp[f]].append(rec[f]['D'])
    print('  %s:' % name)
    for k, v in dist.items():
        print('    %-12s n=%-2d  D 取值集合=%s  D 均值=%.2f' % (
            k, len(v), sorted(set(v)), sum(v) / float(len(v))))
    out[name] = {k: dict(n=len(v), D=sorted(v)) for k, v in dist.items()}

# 分开度：能否找到一条 D 阈值把某一档完整切出来
print('\n=== 分开度检验 ===')
def separable(mp, tier, thresh, op):
    sel = set(f for f in partial if f in mp and mp[f] == tier)
    if not sel:
        return None
    if op == '>=':
        return all(rec[f]['D'] >= thresh for f in sel) and all(rec[f]['D'] < thresh
                                                              for f in partial if f in mp and mp[f] != tier)
    return all(rec[f]['D'] <= thresh for f in sel) and all(rec[f]['D'] > thresh
                                                          for f in partial if f in mp and mp[f] != tier)


found = []
for tier in set(ext.values()):
    for t in range(0, 6):
        for op in ('>=', '<='):
            if separable(ext, tier, t, op):
                found.append((tier, op, t))
print('  外部 triage 的可分离 (档, 算子, 阈值): %s' % found)
ck('1.2 「一手文本失联数 D」单独切不开外部 triage 的三档（说明不是单一维度）',
   len(found) <= 1, found)

# 反控：换成「任意失联路径数」丢掉一手性
def separable_by(mp, tier, key, thresh, op='>='):
    sel = set(f for f in partial if f in mp and mp[f] == tier)
    if not sel:
        return None
    if op == '>=':
        return all(rec[f][key] >= thresh for f in sel) and all(rec[f][key] < thresh
                                                              for f in partial if f in mp and mp[f] != tier)
    return all(rec[f][key] <= thresh for f in sel) and all(rec[f][key] > thresh
                                                          for f in partial if f in mp and mp[f] != tier)


found2 = []
for tier in set(ext.values()):
    for t in range(0, 6):
        for op in ('>=', '<='):
            if separable_by(ext, tier, 'dead', t, op):
                found2.append((tier, op, t))
print('  用「任意失联路径数」的可分离组合: %s' % found2)
ck('N1 丢掉一手性后仍不能分离 => 分歧不在「失联多少条」这个维度',
   len(found2) <= 1, found2)

# 关键：外部 triage 的 5 条「仍可核验」是哪几个
ext_ok = sorted(f for f in partial if ext.get(f) == '仍可核验')
sub_ok = sorted(f for f in partial if sub.get(f) == '仍可核验')
print('\n  外部「仍可核验」5 条: %s' % ext_ok)
print('  执行员「仍可核验」28 条里含上面几条: %s' % [f for f in ext_ok if f in sub_ok])
ck('1.3 外部判「仍可核验」的 5 条，执行员也全判「仍可核验」（子集关系）',
   all(f in sub_ok for f in ext_ok), [f for f in ext_ok if f not in sub_ok])
out['ext_ok'] = ext_ok
out['sub_ok_n'] = len(sub_ok)

out['rec'] = rec
out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(os.path.join(ROOT, '_r141', 'r141f_tier_divergence.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
