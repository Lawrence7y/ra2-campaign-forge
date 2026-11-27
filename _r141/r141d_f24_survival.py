#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""R141 主会话：F24 的「现盘存活」到底是 64 件还是 65 件？两个数是否冲突？

盘上现存三个数：
  (a) R136 标题：清单现盘存活 65 / 4,417（6.03% 字节）
  (b) R138 写进 F24 limitations：存在且字节相同 64 件 / 26,846,620 B、存在但字节不同 1 件、不存在 4,352 件
  (c) 看板第九节待办：现盘 65 件 / 44,470,975 B

本脚本从清单逐行 stat，独立算出：
  N_present = 现盘存在（不论字节是否相同）的件数 与 现盘实际字节和
  N_identical = 现盘存在且字节与清单相同的件数 与 清单字节和
并断言二者差恰为「1 件 / 差 16,711,118 B」（a2_sites.json 的 bounds 剔段量）。

反控：
  N1 把 a2_sites.json 那件人为排除 => N_present 降到 64，证明 65 与 64 只差这一件
  N2 用清单 sum 当现盘和 => 必须 != 现盘实际和（否则两个口径无法区分）
  N3 把 rel 路径拼到 ROOT 而非 lead/ 根 => 存活必须归 0（证明根选对了）
"""
import csv
import io
import json
import os

ROOT = '/home/t628/projects/ra2-campaign-forge'
LEAD = os.path.join(ROOT, 'lead')
MAN = os.path.join(LEAD, 'next_re_20261117_r14', 'R17_R101_TIER_FINAL_4417',
                   'tier_final_4417.tsv')
OUTJ = os.path.join(ROOT, '_r141', 'r141d_f24_survival.json')
fails, out = [], {}


def ck(name, cond, detail=''):
    print(('  PASS ' if cond else '  FAIL ') + name + (('  ' + str(detail)) if detail else ''))
    if not cond:
        fails.append(name)


with io.open(MAN, encoding='utf-8') as f:
    rows = list(csv.DictReader(f, delimiter='\t'))
ck('0.1 清单 4,417 行', len(rows) == 4417, len(rows))
tot_man = sum(int(r['bytes']) for r in rows)
ck('0.2 清单 sum(bytes) == 737,517,286', tot_man == 737517286, tot_man)
ck('0.3 清单列名含 rel 与 bytes', 'rel' in rows[0] and 'bytes' in rows[0],
   list(rows[0].keys()))

present, missing = [], []
for r in rows:
    rel = r['rel'].replace('\\', '/')
    p = os.path.join(LEAD, rel)
    if os.path.isfile(p):
        present.append((rel, int(r['bytes']), os.path.getsize(p)))
    else:
        missing.append((rel, int(r['bytes'])))

same = [(rel, mb, db) for rel, mb, db in present if mb == db]
diff = [(rel, mb, db) for rel, mb, db in present if mb != db]

print('\n=== 现盘存活 ===')
print('  存在（不论字节）  : %d 件 / 清单字节 %d / 现盘字节 %d' % (
    len(present), sum(m for _, m, _ in present), sum(d for _, _, d in present)))
print('  存在且字节相同    : %d 件 / 清单字节 %d / 现盘字节 %d' % (
    len(same), sum(m for _, m, _ in same), sum(d for _, _, d in same)))
print('  存在但字节不同    : %d 件 %s' % (len(diff), [(r, m, d) for r, m, d in diff]))
print('  不存在            : %d 件 / %d B' % (len(missing), sum(b for _, b in missing)))

out['present_n'] = len(present)
out['present_manifest_bytes'] = sum(m for _, m, _ in present)
out['present_disk_bytes'] = sum(d for _, _, d in present)
out['same_n'] = len(same)
out['same_manifest_bytes'] = sum(m for _, m, _ in same)
out['same_disk_bytes'] = sum(d for _, _, d in same)
out['diff'] = [dict(rel=r, manifest=m, disk=d) for r, m, d in diff]
out['missing_n'] = len(missing)
out['missing_bytes'] = sum(b for _, b in missing)

# ---------- 正测 ----------
ck('1.1 存在件数 == 65（(a)(c) 的 65）', len(present) == 65, len(present))
ck('1.2 存在件数 + 不存在件数 == 4,417（不重不漏）',
   len(present) + len(missing) == 4417, (len(present), len(missing)))
ck('1.3 现盘实际字节和 == 44,470,975（(c) 的 44,470,975 B）',
   sum(d for _, _, d in present) == 44470975, sum(d for _, _, d in present))
ck('1.4 存在且字节相同 == 64 件 / 26,846,620 B（(b) 的 64）',
   len(same) == 64 and sum(m for _, m, _ in same) == 26846620,
   (len(same), sum(m for _, m, _ in same)))
ck('1.5 存在但字节不同恰 1 件', len(diff) == 1, len(diff))
ck('1.6 该件是 a2_sites.json 且差 == +16,711,118（bounds 剔段量）',
   diff and diff[0][0].endswith('a2_sites.json') and diff[0][2] - diff[0][1] == 16711118,
   diff[0] if diff else None)
ck('1.7 三桶清单字节之和 == 737,517,286（划分恒等式）',
   sum(m for _, m, _ in present) + sum(b for _, b in missing) == 737517286,
   sum(m for _, m, _ in present) + sum(b for _, b in missing))
ck('1.8 不存在 == 4,352 件 / 709,757,429 B', len(missing) == 4352
   and sum(b for _, b in missing) == 709757429,
   (len(missing), sum(b for _, b in missing)))
ck('1.9 存活比例（字节）== 6.03%（44,470,975 / 737,517,286）',
   round(100.0 * sum(d for _, _, d in present) / tot_man, 2) == 6.03,
   round(100.0 * sum(d for _, _, d in present) / tot_man, 2))
ck('1.10 字节相同比例 == 3.64%（26,846,620 / 737,517,286）',
   round(100.0 * sum(m for _, m, _ in same) / tot_man, 2) == 3.64,
   round(100.0 * sum(m for _, m, _ in same) / tot_man, 2))

# ---------- 反控 ----------
print('\n=== 反控 ===')
# N1 排除 a2_sites.json
p2 = [(r, m, d) for r, m, d in present if not r.endswith('a2_sites.json')]
ck('N1 排除 a2_sites.json 后存在件数降到 64（65 与 64 只差这一件）',
   len(p2) == 64, len(p2))
ck('N1b 排除后现盘字节和降到 26,846,620（== 字节相同桶）',
   sum(d for _, _, d in p2) == 26846620, sum(d for _, _, d in p2))

# N2 用清单 sum 当现盘和必须不等
ck('N2 清单 sum（737,517,286）!= 现盘实际和（44,470,975）——两口径可区分',
   tot_man != sum(d for _, _, d in present),
   (tot_man, sum(d for _, _, d in present)))

# N3 用错的根
wrong = sum(1 for r in rows if os.path.isfile(os.path.join(ROOT, r['rel'].replace('\\', '/'))))
ck('N3 把 rel 拼到 ROOT 而非 lead/ 根 => 存活 0（根选对了）', wrong == 0, wrong)

out['fails'] = fails
print('\n=== FAILS: %d ===' % len(fails))
for f in fails:
    print('  ' + f)
json.dump(out, open(OUTJ, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('断言 %d 项，FAIL %d 项' % (len(fails) + 14, len(fails)))
