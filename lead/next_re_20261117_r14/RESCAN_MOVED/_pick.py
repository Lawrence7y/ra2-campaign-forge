# -*- coding: utf-8 -*-
"""确定性抽样：M1 新增 5 行 + M2 新增 5 行（若不足则取全部并记录）。
抽法（可复跑，不含随机数）:
  M1: 取 m1-new 行最多的 5 个子系统；每个子系统内**优先取具名行**（名字非空且非
      sub_/fn_ 伪名），该子系统无具名 m1-new 行时取无名行；同类内取 entry 升序第一行。
  M2: 取全部 m2 行（含与 m0 重叠的），按 entry 升序；不足 5 行如实记缺口。
"""
import csv
import collections

rows = list(csv.DictReader(open('_rows.tsv', encoding='utf-8'), delimiter='\t'))
m1new = [r for r in rows if int(r['m1_sites'])>0 and int(r['m0_sites'])==0]
m2all = [r for r in rows if int(r['m2_sites'])>0]
m2new = [r for r in m2all if int(r['m0_sites'])==0]

cnt = collections.Counter(r['subsystem'] for r in m1new)
top = [s for s, _ in cnt.most_common(5)]
print('# m1-new 计数前 5 子系统:', top)
picked = []
for s in top:
    cand = sorted([r for r in m1new if r['subsystem'] == s], key=lambda r: r['entry'])
    named = [r for r in cand if r['named'] == '1']
    picked.append((named or cand)[0])
print('\n== M1 抽样（%d 行）==' % len(picked))
for r in picked:
    print('%s\t%s\t%s\tsites_m1=%s' % (r['entry'], r['subsystem'],
                                       r['name'] or '<无名>', r['m1_sites']))

print('\n== M2 抽样：m2 行共 %d（其中 m2-new %d）==' % (len(m2all), len(m2new)))
for r in sorted(m2all, key=lambda r: r['entry']):
    print('%s\t%s\t%s\tm0=%s' % (r['entry'], r['subsystem'], r['name'] or '<无名>', r['m0_sites']))
print('\n缺口: M2 新增仅 %d 行，不足卡面要求的 5 行' % len(m2new))
