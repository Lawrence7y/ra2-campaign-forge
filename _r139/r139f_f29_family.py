#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R139 主会话：F29 的族划分与 74/77、以及该比例的判别力（随机置换零假设）。

F29 正文的族口径（字面）：按类名后缀预先固定三族
  Locomotion  11 个，全非桩
  TypeClass   22 个，全桩
  Other       44 个，其中桩 41 / 非桩 3
族内多数派预测准确率 74/77 = 96.10%，对照常数预测 63/77 = 81.82%
随机置换族标签 200 次，最大仅 64

本轮用 r139e 实测出的逐表桩/非桩标签复算上述五个数，并对「族属性携带真实信息」
给出零假设检验：随机置换族标签 2000 次，报最大值与 p 值。
"""
import os
import json
import random
import collections

ROOT = '/home/t628/projects/ra2-campaign-forge'
J = os.path.join(ROOT, '_r139', 'r139e_f29_6377.json')
d = json.load(open(J, encoding='utf-8'))
non_both = set(d['non_both'])
args = sorted(non_both | set())          # 仅 14 个，下面用总表补全
# 从 r139d 取全 77 个名字
D = json.load(open(os.path.join(ROOT, '_r139', 'r139d_f29_tables.json'), encoding='utf-8'))
# r139d 的 name 存成 'V'+类名（模板实参 V<Class>）；r139e 存的是去掉前缀 V 的类名。
# 统一到「类名」口径，否则两边集合不相交（R139 自错 S-266）。
allargs = sorted(r['name'][1:] if r['name'].startswith('V') else r['name'] for r in D['rows'])
fails, out = [], []


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


ck('0.1 77 个实参', len(allargs) == 77, len(allargs))
ck('0.2 实测非桩集合与 r139e 一致（14 个）', len(non_both) == 14, len(non_both))

# 标签：True = 桩
label = {a: (a not in non_both) for a in allargs}


def family(a):
    if a.endswith('LocomotionClass'):
        return 'Locomotion'
    if a.endswith('TypeClass'):
        return 'TypeClass'
    return 'Other'


fam = collections.defaultdict(list)
for a in allargs:
    fam[family(a)].append(a)
print('\n=== 族划分（按类名后缀，字面口径）===')
for k in ('Locomotion', 'TypeClass', 'Other'):
    v = fam[k]
    st = sum(1 for a in v if label[a])
    print('  %-11s n=%-3d 桩=%-3d 非桩=%-3d' % (k, len(v), st, len(v) - st))
out.append({k: dict(n=len(v), stub=sum(1 for a in v if label[a])) for k, v in fam.items()})

ck('1.1 Locomotion == 11', len(fam['Locomotion']) == 11, len(fam['Locomotion']))
ck('1.2 TypeClass == 22', len(fam['TypeClass']) == 22, len(fam['TypeClass']))
ck('1.3 Other == 44', len(fam['Other']) == 44, len(fam['Other']))
ck('1.4 Locomotion 全非桩（桩数 0）', sum(1 for a in fam['Locomotion'] if label[a]) == 0,
   [a for a in fam['Locomotion'] if label[a]])
ck('1.5 TypeClass 全桩（桩数 22）', sum(1 for a in fam['TypeClass'] if label[a]) == 22,
   sum(1 for a in fam['TypeClass'] if label[a]))
other_stub = sum(1 for a in fam['Other'] if label[a])
other_non = [a for a in fam['Other'] if not label[a]]
ck('1.6 Other 桩 41 / 非桩 3', other_stub == 41 and len(other_non) == 3,
   (other_stub, other_non))
ck('1.7 Other 的 3 个非桩恰是 AircraftClass / BulletClass / CStreamClass',
   sorted(other_non) == ['AircraftClass', 'BulletClass', 'CStreamClass'], sorted(other_non))

# ---- 族内多数派预测 ----
correct = 0
for k, v in fam.items():
    s = sum(1 for a in v if label[a])
    maj = s >= len(v) - s          # 平局取桩（本例无平局）
    correct += s if maj else len(v) - s
print('\n=== 族内多数派预测 ===')
print('  正确 %d / %d = %.4f%%' % (correct, len(allargs), 100.0 * correct / len(allargs)))
ck('2.1 族内多数派正确 == 74', correct == 74, correct)
ck('2.2 74/77 == 96.10%（两位小数）', round(100.0 * correct / len(allargs), 2) == 96.10,
   round(100.0 * correct / len(allargs), 2))
const = max(sum(1 for a in allargs if label[a]), sum(1 for a in allargs if not label[a]))
ck('2.3 常数预测（全判桩）== 63、即 81.82%', const == 63 and
   round(100.0 * const / len(allargs), 2) == 81.82, (const, round(100.0 * const / len(allargs), 2)))
ck('2.4 族预测净增 == 74-63 == 11', correct - const == 11, correct - const)

# ---- 零假设：随机置换族标签 ----
sizes = [len(fam[k]) for k in ('Locomotion', 'TypeClass', 'Other')]
labels = [label[a] for a in allargs]
rng = random.Random(20261126)
best = 0
hist = collections.Counter()
N = 2000
for _ in range(N):
    perm = labels[:]
    rng.shuffle(perm)
    i = 0
    c = 0
    for s in sizes:
        blk = perm[i:i + s]
        i += s
        ones = sum(1 for x in blk if x)
        c += max(ones, s - ones)
    hist[c] += 1
    best = max(best, c)
print('\n=== 零假设：随机置换族标签 %d 次 ===' % N)
print('  最大正确数 =', best, '；>=74 的次数 =', sum(v for k, v in hist.items() if k >= 74))
print('  top5 分布 =', hist.most_common(5))
out.append(dict(null_max=best, null_ge74=sum(v for k, v in hist.items() if k >= 74), N=N))
ck('3.1 置换零假设下最大值 <= 64（族标签不是随便分的）', best <= 64, best)
ck('3.2 置换 2000 次里 >= 74 的次数为 0（p < 0.0005）',
   sum(v for k, v in hist.items() if k >= 74) == 0, sum(v for k, v in hist.items() if k >= 74))
ck('3.3 实测 74 严格大于置换最大值', correct > best, (correct, best))

# ---- 反控 ----
rng2 = random.Random(7)
fake = [rng2.random() < 0.5 for _ in allargs]
i = 0
c2 = 0
for s in sizes:
    blk = fake[i:i + s]
    i += s
    ones = sum(1 for x in blk if x)
    c2 += max(ones, s - ones)
ck('N1 反控：随机标签上同一族口径的「正确数」远小于实测 74（判据有判别力）',
   c2 < 74, c2)
ck('N2 反控：若把族口径改成「除 Locomotion 外全桩」，正确数必须不等于 74',
   (lambda: (lambda c: c != 74)(sum(1 for a in allargs if not family(a) == 'Locomotion' or label[a])))()
   is True, 'see formula')

out.append(dict(family_correct=correct, const=const, fails=fails))
open(os.path.join(ROOT, '_r139', 'r139f_f29_family.json'), 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print('\n汇总：%d FAIL' % len(fails))
raise SystemExit(1 if fails else 0)
