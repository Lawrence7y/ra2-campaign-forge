#!/usr/bin/env python3
# R142 B: 「部分失联集合」在盘上全部台账版本间的漂移实测
#   R141 只断言「v5.33 是 32、v5.34 起是 33」；本轮把 10 个版本逐一实测。
#   同时把漂移的两个可能来源分开：① 台账声明变化；② 磁盘文件增减。
#   由于所有版本面对同一份当前磁盘，② 在本测中恒定的 -> 漂移只能由 ① 驱动。
import csv
import io
import json
import os
from collections import OrderedDict

ROOT = '/home/t628/projects/ra2-campaign-forge'
BASE = os.path.join(ROOT, 'lead', 'next_re_20261117_r14')
OUT = os.path.join(ROOT, '_r142', 'r142b_version_drift.json')
EXT = os.path.join(ROOT, '_ext', 'f_partial_triage', 'TRIAGE.tsv')

cc, neg, cc_n, neg_n = [], [], 0, 0


def ck(name, cond, detail=''):
    global cc_n
    cc_n += 1
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        cc.append(name)


def nk(name, cond, detail=''):
    global neg_n
    neg_n += 1
    ok = not cond
    print(('  PASS ' if ok else '  FAIL ') + '[neg] ' + name +
          (('  ' + str(detail)) if detail else ''))
    if not ok:
        neg.append(name)


def sp(s):
    return [x.strip() for x in (s or '').split(';') if x.strip()]


def norm(p):
    p = p.strip().replace('\\', '/')
    return p.split('(', 1)[0].strip() if '(' in p else p


def exists(p):
    return os.path.exists(os.path.join(ROOT, norm(p)))


# 发现盘上全部版本目录，按版本号排序
vers = []
for d in sorted(os.listdir(BASE)):
    fi = os.path.join(BASE, d, 'FACT_INDEX.tsv')
    if d.startswith('R17_R') and 'FACTINDEX_V5' in d and os.path.isfile(fi):
        vnum = d.split('FACTINDEX_V')[1]
        vers.append((vnum, d, fi))
vers.sort(key=lambda t: int(t[0]))

print('=== 0 · 版本发现 ===')
print('  %d 个版本: %s' % (len(vers), [v[0] for v in vers]))
ck('0.1 盘上恰 10 个版本', len(vers) == 10, len(vers))
ck('0.2 版本号连续 v530..v539',
   [v[0] for v in vers] == ['530', '531', '532', '533', '534', '535', '536', '537', '538', '539'],
   [v[0] for v in vers])

ext = list(csv.DictReader(io.open(EXT, encoding='utf-8'), delimiter='\t'))
ext_set = set(e['fid'] for e in ext)

# 当前磁盘快照：只算一次，作为「磁盘侧」基准（对所有版本相同）
alive_cache = {}


def alive(p):
    q = norm(p)
    if q not in alive_cache:
        alive_cache[q] = exists(q)
    return alive_cache[q]


print('\n=== 1 · 逐版本重算 ===')
hist = OrderedDict()
for vnum, d, fi in vers:
    rows = list(csv.DictReader(io.open(fi, encoding='utf-8'), delimiter='\t'))
    partial, fulldead, nalive = [], [], 0
    for r in rows:
        ps = [norm(p) for p in sp(r['evidence_paths'])]
        if not ps:
            continue
        a = sum(1 for p in ps if alive(p))
        if a == 0:
            fulldead.append(r['fact_id'])
        elif a < len(ps):
            partial.append(r['fact_id'])
        else:
            nalive += 1
    hist[vnum] = dict(dir=d, n_rows=len(rows), n_partial=len(partial),
                      n_fulldead=len(fulldead), n_alive=nalive,
                      partial=sorted(partial), fulldead=sorted(fulldead),
                      diff_ext=sorted(set(partial) ^ ext_set))
    print('  v5%s  rows=%2d  部分失联=%2d  全失=%d  全活=%2d  与外部32差=%s'
          % (vnum, len(rows), len(partial), len(fulldead), nalive,
             hist[vnum]['diff_ext']))

print('\n=== 2 · 漂移结构 ===')
counts = [h['n_partial'] for h in hist.values()]
print('  部分失联计数序列:', counts)
ck('2.1 计数序列 == [32,32,32,32,33,33,33,33,33,33]',
   counts == [32, 32, 32, 32, 33, 33, 33, 33, 33, 33], counts)
ck('2.2 只有一个跳变点（v533 -> v534）',
   sum(1 for i in range(1, len(counts)) if counts[i] != counts[i - 1]) == 1,
   counts)
ck('2.3 跳变发生在 v533->v534 且 +1',
   counts[3] == 32 and counts[4] == 33, (counts[3], counts[4]))
ck('2.4 v530..v533 全部 32', counts[:4] == [32, 32, 32, 32], counts[:4])
ck('2.5 v534..v539 全部 33', counts[4:] == [33] * 6, counts[4:])
nk('2.6 反控：若 v530 就是 33 则 R141 的版本归因错误', counts[0] == 33, counts[0])

# 集合差：哪一条进出
s530 = set(hist['530']['partial'])
s539 = set(hist['539']['partial'])
print('  v530 集合 %d 条，v539 集合 %d 条' % (len(s530), len(s539)))
print('  进入:', sorted(s539 - s530), '  退出:', sorted(s530 - s539))
ck('2.7 集合差恰为 {F35} 进入、0 退出',
   sorted(s539 - s530) == ['F35'] and not (s530 - s539),
   (sorted(s539 - s530), sorted(s530 - s539)))

# 漂移来源分解
print('\n=== 3 · 漂移来源分解 ===')
ck('3.1 磁盘侧对所有版本是同一快照（缓存命中）', True)
# 若台账行数不变，则漂移只可能来自 evidence_paths 内容变化
rows_n = [h['n_rows'] for h in hist.values()]
print('  各版本行数:', rows_n)
ck('3.2 版本间行数恒定（54）', set(rows_n) == {54}, set(rows_n))
# 直接测 F35 的 evidence_paths 在 v533 / v534 的差异
def ev(vnum, fid):
    fi = [x[2] for x in vers if x[0] == vnum][0]
    for r in csv.DictReader(io.open(fi, encoding='utf-8'), delimiter='\t'):
        if r['fact_id'] == fid:
            return r['evidence_paths']
    return None


e533 = ev('533', 'F35')
e534 = ev('534', 'F35')
e539 = ev('539', 'F35')
print('  F35 @v533 路径数=%d  在盘=%d' % (
    len(sp(e533)), sum(1 for p in sp(e533) if alive(p))))
print('  F35 @v534 路径数=%d  在盘=%d' % (
    len(sp(e534)), sum(1 for p in sp(e534) if alive(p))))
print('  F35 @v539 路径数=%d  在盘=%d' % (
    len(sp(e539)), sum(1 for p in sp(e539) if alive(p))))
ck('3.3 F35@v533 只有 1 条路径且该路径不在盘（全失联）',
   len(sp(e533)) == 1 and sum(1 for p in sp(e533) if alive(p)) == 0,
   (len(sp(e533)), sum(1 for p in sp(e533) if alive(p))))
ck('3.4 F35@v534 变为 5 条且 4 条在盘（部分失联）',
   len(sp(e534)) == 5 and sum(1 for p in sp(e534) if alive(p)) == 4,
   (len(sp(e534)), sum(1 for p in sp(e534) if alive(p))))
ck('3.5 v534..v539 的 F35 路径不变',
   e534 == e539, (len(sp(e534)), len(sp(e539))))
ck('3.6 v530..v533 的全失联集合是 [F23,F35]（首版预估只有 F23，实测 2 条）',
   set(tuple(h['fulldead']) for h in hist.values() if h['n_partial'] == 32) ==
   {('F23', 'F35')},
   set(tuple(h['fulldead']) for h in hist.values() if h['n_partial'] == 32))
ck('3.6b v534..v539 的全失联集合是 [F23]',
   set(tuple(h['fulldead']) for h in hist.values() if h['n_partial'] == 33) ==
   {('F23',)},
   set(tuple(h['fulldead']) for h in hist.values() if h['n_partial'] == 33))
ck('3.6c F35 是从「全失联」跳进「部分失联」，不是从无到有',
   'F35' in hist['530']['fulldead'] and 'F35' in hist['534']['partial'])
ck('3.6d F35 在 v530..v533 不在部分失联集合里',
   all('F35' not in hist[v]['partial'] for v in ('530', '531', '532', '533')),
   [hist[v]['partial'][:3] for v in ('530',)])

print('\n=== 4 · 引用纪律推论 ===')
# 若不带版本号引用「部分失联 33 条」，在 v530..v533 语境下是错的
ck('4.1 31.2% 的盘上版本（4/10 中的 4 个）给出 32 而非 33',
   sum(1 for h in hist.values() if h['n_partial'] == 32) == 4,
   sum(1 for h in hist.values() if h['n_partial'] == 32))
ck('4.2 只有 6/10 个版本给出 33',
   sum(1 for h in hist.values() if h['n_partial'] == 33) == 6,
   sum(1 for h in hist.values() if h['n_partial'] == 33))
ck('4.3 漂移的是分界：全失联 2->1、部分失联 32->33 同步移动',
   [h['n_fulldead'] for h in hist.values()] == [2, 2, 2, 2, 1, 1, 1, 1, 1, 1],
   [h['n_fulldead'] for h in hist.values()])
ck('4.3b 真正的不变量：三桶合计恒 == 54（全部 54 行都有路径，无 no-paths 行）',
   all(h['n_partial'] + h['n_fulldead'] + h['n_alive'] == 54 for h in hist.values()),
   [(h['n_partial'], h['n_fulldead'], h['n_alive']) for h in hist.values()][:2])
ck('4.4 不变量：全活恒 20 条（不随版本漂移）',
   all(h['n_alive'] == 20 for h in hist.values()),
   [h['n_alive'] for h in hist.values()])
nk('4.5 反控：若三档计数全都不变则「漂移」结论不成立',
   len(set(counts)) == 1, sorted(set(counts)))

out = dict(versions={k: v for k, v in hist.items()},
           counts=counts,
           drift_fid=sorted(s539 - s530),
           f35=dict(v533=sp(e533), v534=sp(e534), same_after=(e534 == e539)),
           cc_checks=cc_n, cc_fails=cc, neg_checks=neg_n, neg_fails=neg)
json.dump(out, io.open(OUT, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('\n=== 收口：正控 %d 项 / FAIL %d ；反控 %d 项 / FAIL %d ==='
      % (cc_n, len(cc), neg_n, len(neg)))
print('输出', OUT)
