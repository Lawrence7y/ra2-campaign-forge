#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：【规则 D 之三·决定性检验】「仍可核验/需重建/不可核验」三分档能不能机械复现？

r141f 已证：D（一手文本失联数）与「任意失联路径数」都不能分离外部 triage 的三档。
本脚本做最后一击 —— **同键不同档检验**：
  若存在两个事实项，它们的「失联路径指纹」完全同型（同样的文件 basename 集合、同样的存活数），
  却被判成不同档，则任何「只看路径结构」的函数都无法复现该分档 ⇒ 分档依赖人工判读。
  反之（不存在同型不同档），则分档可能仍有机械解，只是我还没找到 —— 那样必须如实写「未取得」。

指纹定义（三档粒度，逐级加严）：
  FP1 = 失联路径的 basename 多重集
  FP2 = FP1 + 存活路径数
  FP3 = FP2 + 每条失联路径的 (事项N/§N) 小节定位串，去掉数字后
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


LOC = re.compile(r'\(([^)]*)\)')
DIG = re.compile(r'[0-9]+')


def splitp(s):
    ps = [q.strip().replace('\\', '/') for q in (s or '').split(';') if q.strip()]
    return ps


def base_of(p):
    return os.path.basename(p.split('(', 1)[0].strip())


def loc_of(p):
    m = LOC.search(p)
    return DIG.sub('#', m.group(1)) if m else ''


rows = list(csv.DictReader(io.open(FI, encoding='utf-8'), delimiter='\t'))
rec = {}
for r in rows:
    ps = splitp(r['evidence_paths'])
    alive = [q for q in ps if os.path.exists(q.split('(', 1)[0].strip())]
    dead = [q for q in ps if not os.path.exists(q.split('(', 1)[0].strip())]
    rec[r['fact_id']] = dict(alive=alive, dead=dead)


def fp(f, level):
    v = rec[f]
    b = tuple(sorted(base_of(d) for d in v['dead']))
    if level == 1:
        return b
    if level == 2:
        return (b, len(v['alive']))
    return (b, len(v['alive']), tuple(sorted(loc_of(d) for d in v['dead'])))


for name, path, idcol, tiercol in (
        ('外部 triage', EXT, 'fid', 'verdict'),
        ('执行员 #311', SUB, 'fact_id', 'tier')):
    mp = {r[idcol]: r[tiercol] for r in csv.DictReader(io.open(path, encoding='utf-8'),
                                                      delimiter='\t')}
    print('\n=== %s：同键不同档检验 ===' % name)
    for lvl in (1, 2, 3):
        groups = collections.defaultdict(set)
        members = collections.defaultdict(list)
        for f, t in mp.items():
            if f in rec:
                k = fp(f, lvl)
                groups[k].add(t)
                members[k].append((f, t))
        conflict = {k: v for k, v in groups.items() if len(v) > 1}
        print('  FP%d：共 %d 个指纹，其中 %d 个指纹跨 >1 档' % (lvl, len(groups), len(conflict)))
        for k, ts in sorted(conflict.items(), key=lambda x: -len(x[1]))[:4]:
            print('     指纹 %s' % (str(k)[:90],))
            print('       成员: %s' % members[k])
        out['%s_FP%d_conflict' % (name, lvl)] = len(conflict)
        out['%s_FP%d_groups' % (name, lvl)] = len(groups)

# 具体到最具判别力的例子：单失一件 VERDICT.md / 单失一件 SECTION.md
print('\n=== 单件失联却跨档的具体反例 ===')
for basename in ('VERDICT.md', 'SECTION.md', 'PANEL.md', 'DELIVERY_SUMMARY.md'):
    ext_mp = {r['fid']: r['verdict'] for r in csv.DictReader(io.open(EXT, encoding='utf-8'),
                                                            delimiter='\t')}
    got = []
    for f, t in sorted(ext_mp.items()):
        if f not in rec:
            continue
        d = rec[f]['dead']
        if len(d) == 1 and base_of(d[0]) == basename:
            got.append((f, t, len(rec[f]['alive'])))
    if got:
        tiers = set(t for _, t, _ in got)
        print('  只失 1 件 %-20s => %s   跨 %d 档: %s' % (
            basename, got, len(tiers), sorted(tiers)))
        out['single_%s' % basename] = [dict(fid=f, tier=t, alive=a) for f, t, a in got]

# 结论性断言
ext_mp = {r['fid']: r['verdict'] for r in csv.DictReader(io.open(EXT, encoding='utf-8'),
                                                        delimiter='\t')}
verdict_single = [t for f, t in ext_mp.items()
                  if f in rec and len(rec[f]['dead']) == 1
                  and base_of(rec[f]['dead'][0]) == 'VERDICT.md']
ck('1.1 只失 1 件 VERDICT.md 的事实项里出现 >1 种档位（同键不同档）',
   len(set(verdict_single)) > 1, collections.Counter(verdict_single))
sec_single = [t for f, t in ext_mp.items()
              if f in rec and len(rec[f]['dead']) == 1
              and base_of(rec[f]['dead'][0]) == 'SECTION.md']
ck('1.2 只失 1 件 SECTION.md 的事实项里出现 >1 种档位（同键不同档）',
   len(set(sec_single)) > 1, collections.Counter(sec_single))
ck('1.3 因此 FP1/FP2/FP3 三级指纹都无法复现外部 triage 的三档',
   out['外部 triage_FP1_conflict'] > 0 and out['外部 triage_FP2_conflict'] > 0
   and out['外部 triage_FP3_conflict'] > 0,
   (out['外部 triage_FP1_conflict'], out['外部 triage_FP2_conflict'],
    out['外部 triage_FP3_conflict']))

out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(os.path.join(ROOT, '_r141', 'r141g_tier_reproducibility.json'), 'w',
                    encoding='utf-8'), ensure_ascii=False, indent=1)
